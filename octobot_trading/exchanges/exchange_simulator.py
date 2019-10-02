#  Drakkar-Software OctoBot-Trading
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
from octobot_backtesting.api.backtesting import initialize_backtesting
from octobot_backtesting.importers.exchanges.exchange_importer import ExchangeDataImporter
from octobot_channels.channels.channel import get_chan
from octobot_commons.channels_name import OctoBotBacktestingChannelsName
from octobot_commons.number_util import round_into_str_with_max_digits
from octobot_commons.symbol_util import split_symbol
from octobot_trading.channels.exchange_channel import get_chan as get_trading_chan
from octobot_trading.constants import CONFIG_SIMULATOR, CONFIG_DEFAULT_SIMULATOR_FEES, CONFIG_SIMULATOR_FEES, \
    CONFIG_SIMULATOR_FEES_MAKER, CONFIG_SIMULATOR_FEES_TAKER, CONFIG_SIMULATOR_FEES_WITHDRAW
from octobot_trading.enums import ExchangeConstantsMarketStatusColumns, ExchangeConstantsMarketPropertyColumns, \
    TraderOrderType, FeePropertyColumns
from octobot_trading.exchanges.abstract_exchange import AbstractExchange
from octobot_trading.producers.simulator import UNAUTHENTICATED_UPDATER_SIMULATOR_PRODUCERS


class ExchangeSimulator(AbstractExchange):
    def __init__(self, config, exchange_type, exchange_manager, backtesting_data_files):
        super().__init__(config, exchange_type, exchange_manager)
        self.backtesting_data_files = backtesting_data_files
        self.backtesting = None

        self.exchange_importers = []

        self.symbols = []
        self.time_frames = []

    async def initialize_impl(self):
        self.backtesting = await initialize_backtesting(self.config, self.backtesting_data_files)

        self.exchange_importers = self.backtesting.get_importers(ExchangeDataImporter)
        # load symbols and time frames
        for importer in self.exchange_importers:
            self.symbols += importer.symbols
            self.time_frames += importer.time_frames

        # remove duplicates
        self.symbols = list(set(self.symbols))
        self.time_frames = list(set(self.time_frames))

        # set exchange manager attributes
        self.exchange_manager.client_symbols = self.symbols
        self.exchange_manager.time_frames = self.time_frames

    async def modify_channels(self):
        # set mininmum and maximum timestamp according to all importers data
        timestamps = [await importer.get_data_timestamp_interval()
                      for importer in self.exchange_importers]  # [(min, max) ... ]

        await get_chan(OctoBotBacktestingChannelsName.TIME_CHANNEL.value).modify(
            minimum_timestamp=min(timestamps)[0],
            maximum_timestamp=max(timestamps)[1])

    async def create_backtesting_exchange_producers(self):
        for importer in self.exchange_importers:
            for updater in UNAUTHENTICATED_UPDATER_SIMULATOR_PRODUCERS:
                await updater(get_trading_chan(updater.CHANNEL_NAME, self.name), importer).run()

    async def stop(self):
        pass  # TODO

    def symbol_exists(self, symbol):
        return symbol in self.symbols

    def time_frame_exists(self, time_frame):
        return time_frame in self.time_frames

    def get_market_status(self, symbol, price_example=0, with_fixer=True):
        return {
            # number of decimal digits "after the dot"
            ExchangeConstantsMarketStatusColumns.PRECISION.value: {
                ExchangeConstantsMarketStatusColumns.PRECISION_AMOUNT.value: 8,
                ExchangeConstantsMarketStatusColumns.PRECISION_COST.value: 8,
                ExchangeConstantsMarketStatusColumns.PRECISION_PRICE.value: 8,
            },
            ExchangeConstantsMarketStatusColumns.LIMITS.value: {
                ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT.value: {
                    ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT_MIN.value: 0.00001,
                    ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT_MAX.value: 1000000000000,
                },
                ExchangeConstantsMarketStatusColumns.LIMITS_PRICE.value: {
                    ExchangeConstantsMarketStatusColumns.LIMITS_PRICE_MIN.value: 0.00001,
                    ExchangeConstantsMarketStatusColumns.LIMITS_PRICE_MAX.value: 1000000000000,
                },
                ExchangeConstantsMarketStatusColumns.LIMITS_COST.value: {
                    ExchangeConstantsMarketStatusColumns.LIMITS_COST_MIN.value: 0.001,
                    ExchangeConstantsMarketStatusColumns.LIMITS_COST_MAX.value: 1000000000000,
                },
            },
        }

    def get_uniform_timestamp(self, timestamp):
        return timestamp / 1000

    def get_fees(self, symbol=None):
        result_fees = {
            ExchangeConstantsMarketPropertyColumns.TAKER.value: CONFIG_DEFAULT_SIMULATOR_FEES,
            ExchangeConstantsMarketPropertyColumns.MAKER.value: CONFIG_DEFAULT_SIMULATOR_FEES,
            ExchangeConstantsMarketPropertyColumns.FEE.value: CONFIG_DEFAULT_SIMULATOR_FEES
        }

        if CONFIG_SIMULATOR in self.config and CONFIG_SIMULATOR_FEES in self.config[CONFIG_SIMULATOR]:
            if CONFIG_SIMULATOR_FEES_MAKER in self.config[CONFIG_SIMULATOR][CONFIG_SIMULATOR_FEES]:
                result_fees[ExchangeConstantsMarketPropertyColumns.MAKER.value] = \
                    self.config[CONFIG_SIMULATOR][CONFIG_SIMULATOR_FEES][CONFIG_SIMULATOR_FEES_MAKER]

            if CONFIG_SIMULATOR_FEES_MAKER in self.config[CONFIG_SIMULATOR][CONFIG_SIMULATOR_FEES]:
                result_fees[ExchangeConstantsMarketPropertyColumns.TAKER.value] = \
                    self.config[CONFIG_SIMULATOR][CONFIG_SIMULATOR_FEES][CONFIG_SIMULATOR_FEES_TAKER]

            if CONFIG_SIMULATOR_FEES_WITHDRAW in self.config[CONFIG_SIMULATOR][CONFIG_SIMULATOR_FEES]:
                result_fees[ExchangeConstantsMarketPropertyColumns.FEE.value] = \
                    self.config[CONFIG_SIMULATOR][CONFIG_SIMULATOR_FEES][CONFIG_SIMULATOR_FEES_WITHDRAW]

        return result_fees

    # returns {
    #     'type': takerOrMaker,
    #     'currency': 'BTC', // the unified fee currency code
    #     'rate': percentage, // the fee rate, 0.05% = 0.0005, 1% = 0.01, ...
    #     'cost': feePaid, // the fee cost (amount * fee rate)
    # }
    def get_trade_fee(self, symbol, order_type, quantity, price,
                      taker_or_maker=ExchangeConstantsMarketPropertyColumns.TAKER.value):
        symbol_fees = self.get_fees(symbol)
        rate = symbol_fees[taker_or_maker] / 100  # /100 because rate in used in %
        currency, market = split_symbol(symbol)
        fee_currency = currency

        precision = self.get_market_status(symbol)[ExchangeConstantsMarketStatusColumns.PRECISION.value] \
            [ExchangeConstantsMarketStatusColumns.PRECISION_PRICE.value]
        cost = float(round_into_str_with_max_digits(quantity * rate, precision))

        if order_type == TraderOrderType.SELL_MARKET or order_type == TraderOrderType.SELL_LIMIT:
            cost = float(round_into_str_with_max_digits(cost * price, precision))
            fee_currency = market

        return {
            FeePropertyColumns.TYPE.value: taker_or_maker,
            FeePropertyColumns.CURRENCY.value: fee_currency,
            FeePropertyColumns.RATE.value: rate,
            FeePropertyColumns.COST.value: cost
        }

    def is_authenticated(self) -> bool:
        return False
