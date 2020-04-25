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
from octobot_backtesting.api.backtesting import get_backtesting_current_time
from octobot_backtesting.api.importer import get_available_data_types, get_available_time_frames
from octobot_backtesting.importers.exchanges.exchange_importer import ExchangeDataImporter
from octobot_commons.number_util import round_into_str_with_max_digits
from octobot_commons.symbol_util import split_symbol
from octobot_commons.time_frame_manager import sort_time_frames
from octobot_trading.channels.exchange_channel import get_chan as get_trading_chan
from octobot_trading.constants import CONFIG_SIMULATOR, CONFIG_DEFAULT_SIMULATOR_FEES, CONFIG_SIMULATOR_FEES, \
    CONFIG_SIMULATOR_FEES_MAKER, CONFIG_SIMULATOR_FEES_TAKER, CONFIG_SIMULATOR_FEES_WITHDRAW, \
    DEFAULT_BACKTESTING_TIME_LAG
from octobot_trading.enums import ExchangeConstantsMarketStatusColumns, ExchangeConstantsMarketPropertyColumns, \
    TraderOrderType, FeePropertyColumns
from octobot_trading.exchanges.abstract_exchange import AbstractExchange
from octobot_trading.producers.simulator import UNAUTHENTICATED_UPDATER_SIMULATOR_PRODUCERS, \
    SIMULATOR_PRODUCERS_TO_POSSIBLE_DATA_TYPE, SIMULATOR_PRODUCERS_TO_REAL_DATA_TYPE


class ExchangeSimulator(AbstractExchange):
    def __init__(self, config, exchange_type, exchange_manager, backtesting):
        super().__init__(config, exchange_type, exchange_manager)
        self.backtesting = backtesting
        self.allowed_time_lag = DEFAULT_BACKTESTING_TIME_LAG

        """
        Backtesting exchange importers list
        """
        self.exchange_importers = []

        """
        Exchange simulator will never be authenticated
        """
        self.is_authenticated = False

        self.current_future_candles = {}

    async def initialize_impl(self):
        client_symbols = []
        client_time_frames = []

        self.exchange_importers = self.backtesting.get_importers(ExchangeDataImporter)

        # load symbols and time frames
        for importer in self.exchange_importers:
            client_symbols += importer.symbols
            client_time_frames += importer.time_frames

        # remove duplicates
        self.symbols = list(set(self.symbols))
        self.current_future_candles = {
            symbol: {}
            for symbol in self.symbols
        }
        self.time_frames = list(set(self.time_frames))

        # set exchange manager attributes
        self.exchange_manager.client_symbols = client_symbols
        self.exchange_manager.client_time_frames = client_time_frames

    async def create_backtesting_exchange_producers(self):
        for importer in self.exchange_importers:
            available_data_types = get_available_data_types(importer)
            at_least_one_updater = False
            for channel_type, updater in UNAUTHENTICATED_UPDATER_SIMULATOR_PRODUCERS.items():
                if _are_required_data_available(channel_type, available_data_types):
                    await updater(get_trading_chan(updater.CHANNEL_NAME, self.exchange_manager.id), importer).run()
                    at_least_one_updater = True
            if not at_least_one_updater:
                self.logger.error(f"No updater created for {importer.symbols} backtesting")

    async def stop(self):
        self.backtesting = None
        self.exchange_importers = []

    def get_exchange_current_time(self):
        return get_backtesting_current_time(self.backtesting)

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
                    ExchangeConstantsMarketStatusColumns.LIMITS_PRICE_MIN.value: 0.000001,
                    ExchangeConstantsMarketStatusColumns.LIMITS_PRICE_MAX.value: 1000000000000,
                },
                ExchangeConstantsMarketStatusColumns.LIMITS_COST.value: {
                    ExchangeConstantsMarketStatusColumns.LIMITS_COST_MIN.value: 0.001,
                    ExchangeConstantsMarketStatusColumns.LIMITS_COST_MAX.value: 1000000000000,
                },
            },
        }

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

    def get_split_pair_from_exchange(self, pair) -> (str, str):
        return split_symbol(pair)

    def get_pair_cryptocurrency(self, pair) -> str:
        return self.get_split_pair_from_exchange(pair)[0]


def handles_real_data_for_updater(channel_type, available_data):
    if channel_type in SIMULATOR_PRODUCERS_TO_REAL_DATA_TYPE:
        return all(data_type in available_data for data_type in SIMULATOR_PRODUCERS_TO_REAL_DATA_TYPE[channel_type])
    return True


def get_real_available_data(exchange_importers):
    available_data = set()
    for importer in exchange_importers:
        available_data = available_data.union(get_available_data_types(importer))
    return available_data


def _are_required_data_available(channel_type, available_data_types):
    if channel_type not in SIMULATOR_PRODUCERS_TO_POSSIBLE_DATA_TYPE:
        # no required data if updater is not in SIMULATOR_PRODUCERS_TO_DATA_TYPE keys
        return True
    else:
        # if updater is in SIMULATOR_PRODUCERS_TO_DATA_TYPE keys: check that at least one of the required data is
        # available
        return any(required_data_type in available_data_types
                   for required_data_type in SIMULATOR_PRODUCERS_TO_POSSIBLE_DATA_TYPE[channel_type])
