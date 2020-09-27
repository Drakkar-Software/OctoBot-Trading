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

import octobot_trading.channels as channels
import octobot_trading.exchanges as exchanges
import octobot_trading.producers as producers
from octobot_trading.constants import CONFIG_SIMULATOR, CONFIG_DEFAULT_SIMULATOR_FEES, CONFIG_SIMULATOR_FEES, \
    CONFIG_SIMULATOR_FEES_MAKER, CONFIG_SIMULATOR_FEES_TAKER, CONFIG_SIMULATOR_FEES_WITHDRAW, \
    DEFAULT_BACKTESTING_TIME_LAG
from octobot_trading.enums import ExchangeConstantsMarketPropertyColumns as Ecmsc, FeePropertyColumns, TraderOrderType


class ExchangeSimulator(exchanges.AbstractExchange):
    def __init__(self, config, exchange_manager, backtesting):
        super().__init__(config, exchange_manager)
        self.backtesting = backtesting
        self.allowed_time_lag = DEFAULT_BACKTESTING_TIME_LAG

        self.exchange_importers = []

        self.symbols = set()
        self.time_frames = set()

        self.current_future_candles = {}

        self.is_authenticated = False

    async def initialize_impl(self):
        self.exchange_importers = self.backtesting.get_importers(ExchangeDataImporter)
        # load symbols and time frames
        for importer in self.exchange_importers:
            self.symbols.update(importer.symbols)
            self.time_frames.update(importer.time_frames)

        # remove duplicates
        self.current_future_candles = {
            symbol: {}
            for symbol in self.symbols
        }

        # set exchange manager attributes
        self.exchange_manager.client_symbols = list(self.symbols)

    @classmethod
    def is_supporting_exchange(cls, exchange_candidate_name) -> bool:
        return True

    @classmethod
    def is_simulated_exchange(cls) -> bool:
        return True

    @staticmethod
    def handles_real_data_for_updater(channel_type, available_data):
        if channel_type in producers.SIMULATOR_PRODUCERS_TO_REAL_DATA_TYPE:
            return all(data_type in available_data
                       for data_type in producers.SIMULATOR_PRODUCERS_TO_REAL_DATA_TYPE[channel_type])
        return True

    async def create_backtesting_exchange_producers(self):
        for importer in self.exchange_importers:
            available_data_types = get_available_data_types(importer)
            at_least_one_updater = False
            for channel_type, updater in producers.UNAUTHENTICATED_UPDATER_PRODUCERS.items():
                if self._are_required_data_available(channel_type, available_data_types):
                    await updater(channels.get_chan(updater.CHANNEL_NAME, self.exchange_manager.id), importer).run()
                    at_least_one_updater = True
            if not at_least_one_updater:
                self.logger.error(f"No updater created for {importer.symbols} backtesting")

    @staticmethod
    def _are_required_data_available(channel_type, available_data_types):
        if channel_type not in producers.SIMULATOR_PRODUCERS_TO_POSSIBLE_DATA_TYPE:
            # no required data if updater is not in SIMULATOR_PRODUCERS_TO_DATA_TYPE keys
            return True
        else:
            # if updater is in SIMULATOR_PRODUCERS_TO_DATA_TYPE keys: check that at least one of the required data is
            # available
            return any(required_data_type in available_data_types
                       for required_data_type
                       in producers.SIMULATOR_PRODUCERS_TO_POSSIBLE_DATA_TYPE[channel_type])

    async def stop(self):
        self.backtesting = None
        self.exchange_importers = []

    def get_exchange_current_time(self):
        return get_backtesting_current_time(self.backtesting)

    def get_available_time_frames(self):
        if self.exchange_importers:
            return [time_frame.value for time_frame in get_available_time_frames(next(iter(self.exchange_importers)))]
        return []

    def get_market_status(self, symbol, price_example=0, with_fixer=True):
        return {
            # number of decimal digits "after the dot"
            Ecmsc.PRECISION.value: {
                Ecmsc.PRECISION_AMOUNT.value: 8,
                Ecmsc.PRECISION_COST.value: 8,
                Ecmsc.PRECISION_PRICE.value: 8,
            },
            Ecmsc.LIMITS.value: {
                Ecmsc.LIMITS_AMOUNT.value: {
                    Ecmsc.LIMITS_AMOUNT_MIN.value: 0.00001,
                    Ecmsc.LIMITS_AMOUNT_MAX.value: 1000000000000,
                },
                Ecmsc.LIMITS_PRICE.value: {
                    Ecmsc.LIMITS_PRICE_MIN.value: 0.000001,
                    Ecmsc.LIMITS_PRICE_MAX.value: 1000000000000,
                },
                Ecmsc.LIMITS_COST.value: {
                    Ecmsc.LIMITS_COST_MIN.value: 0.001,
                    Ecmsc.LIMITS_COST_MAX.value: 1000000000000,
                },
            },
        }

    def get_uniform_timestamp(self, timestamp):
        return timestamp / 1000

    def get_fees(self, symbol):
        result_fees = {
            Ecmsc.TAKER.value: CONFIG_DEFAULT_SIMULATOR_FEES,
            Ecmsc.MAKER.value: CONFIG_DEFAULT_SIMULATOR_FEES,
            Ecmsc.FEE.value: CONFIG_DEFAULT_SIMULATOR_FEES
        }

        if CONFIG_SIMULATOR in self.config and CONFIG_SIMULATOR_FEES in self.config[CONFIG_SIMULATOR]:
            if CONFIG_SIMULATOR_FEES_MAKER in self.config[CONFIG_SIMULATOR][CONFIG_SIMULATOR_FEES]:
                result_fees[Ecmsc.MAKER.value] = \
                    self.config[CONFIG_SIMULATOR][CONFIG_SIMULATOR_FEES][CONFIG_SIMULATOR_FEES_MAKER]

            if CONFIG_SIMULATOR_FEES_MAKER in self.config[CONFIG_SIMULATOR][CONFIG_SIMULATOR_FEES]:
                result_fees[Ecmsc.TAKER.value] = \
                    self.config[CONFIG_SIMULATOR][CONFIG_SIMULATOR_FEES][CONFIG_SIMULATOR_FEES_TAKER]

            if CONFIG_SIMULATOR_FEES_WITHDRAW in self.config[CONFIG_SIMULATOR][CONFIG_SIMULATOR_FEES]:
                result_fees[Ecmsc.FEE.value] = \
                    self.config[CONFIG_SIMULATOR][CONFIG_SIMULATOR_FEES][CONFIG_SIMULATOR_FEES_WITHDRAW]

        return result_fees

    # returns {
    #     'type': takerOrMaker,
    #     'currency': 'BTC', // the unified fee currency code
    #     'rate': percentage, // the fee rate, 0.05% = 0.0005, 1% = 0.01, ...
    #     'cost': feePaid, // the fee cost (amount * fee rate)
    # }
    def get_trade_fee(self, symbol, order_type, quantity, price, taker_or_maker):
        if not taker_or_maker:
            taker_or_maker = Ecmsc.TAKER.value
        symbol_fees = self.get_fees(symbol)
        rate = symbol_fees[taker_or_maker] / 100  # /100 because rate in used in %
        currency, market = split_symbol(symbol)
        fee_currency = currency

        precision = self.get_market_status(symbol)[Ecmsc.PRECISION.value] \
            [Ecmsc.PRECISION_PRICE.value]
        cost = float(round_into_str_with_max_digits(quantity * rate, precision))

        if order_type == TraderOrderType.SELL_MARKET or \
                order_type == TraderOrderType.SELL_LIMIT:
            cost = float(round_into_str_with_max_digits(cost * price, precision))
            fee_currency = market

        return {
            FeePropertyColumns.TYPE.value: taker_or_maker,
            FeePropertyColumns.CURRENCY.value: fee_currency,
            FeePropertyColumns.RATE.value: rate,
            FeePropertyColumns.COST.value: cost
        }

    def get_time_frames(self, importer):
        return sort_time_frames(list(set(get_available_time_frames(importer)) &
                                set(self.exchange_manager.exchange_config.traded_time_frames)),
                                reverse=True)

    def get_split_pair_from_exchange(self, pair) -> (str, str):
        return split_symbol(pair)

    def get_pair_cryptocurrency(self, pair) -> str:
        return self.get_split_pair_from_exchange(pair)[0]

    @staticmethod
    def get_real_available_data(exchange_importers):
        available_data = set()
        for importer in exchange_importers:
            available_data = available_data.union(get_available_data_types(importer))
        return available_data
