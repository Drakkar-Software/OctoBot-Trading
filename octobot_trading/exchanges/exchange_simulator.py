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

import copy

from octobot_backtesting.importers.exchanges.exchange_importer import ExchangeDataImporter
from octobot_commons.data_util import DataUtil
from octobot_commons.enums import PriceIndexes, TimeFrames
from octobot_commons.number_util import round_into_str_with_max_digits
from octobot_commons.symbol_util import split_symbol
from octobot_commons.time_frame_manager import TimeFrameManager
from octobot_trading.channels import get_chan, TIME_CHANNEL

from octobot_trading.constants import CONFIG_SIMULATOR, CONFIG_DEFAULT_SIMULATOR_FEES, CONFIG_SIMULATOR_FEES, \
    CONFIG_SIMULATOR_FEES_MAKER, CONFIG_SIMULATOR_FEES_TAKER, CONFIG_SIMULATOR_FEES_WITHDRAW, \
    ORDER_CREATION_LAST_TRADES_TO_USE, SIMULATOR_LAST_PRICES_TO_CHECK
from octobot_trading.enums import ExchangeConstantsMarketStatusColumns, ExchangeConstantsMarketPropertyColumns, \
    TraderOrderType, FeePropertyColumns
from octobot_trading.exchanges.abstract_exchange import AbstractExchange
from octobot_trading.exchanges.data.exchange_symbol_data import ExchangeSymbolData
from octobot_trading.util import get_symbols


class ExchangeSimulator(AbstractExchange):
    def __init__(self, config, exchange_type, exchange_manager, backtesting_data_files):
        super().__init__(config, exchange_type, exchange_manager)
        self.backtesting_data_files = backtesting_data_files

        # if CONFIG_BACKTESTING not in self.config:
        #     raise Exception("Backtesting config not found")

        self.exchange_importer = ExchangeDataImporter(self.config,
                                                      self.backtesting_data_files[-1])  # TODO foreach files
        self.exchange_importer.initialize()

        self.symbols = None
        self.data = None
        # self.__set_symbol_list()

        self.config_time_frames = TimeFrameManager.get_config_time_frame(self.config)

        # set exchange manager attributes
        self.exchange_manager.client_symbols = self.symbols
        # self.exchange_manager.client_time_frames = self.__get_available_timeframes()
        self.exchange_manager.time_frames = self.config_time_frames

        self.time_frame_get_times = {}
        self.time_frames_offset = {}
        self.min_time_frame_to_consider = {}

        self.DEFAULT_LIMIT = 100
        self.MIN_LIMIT = 30

        # used to force price movement
        self.recent_trades_multiplier_factor = 1

        self.MIN_ENABLED_TIME_FRAME = TimeFrameManager.find_min_time_frame(self.config_time_frames)
        self.DEFAULT_TIME_FRAME_RECENT_TRADE_CREATOR = self.MIN_ENABLED_TIME_FRAME
        self.DEFAULT_TIME_FRAME_TICKERS_CREATOR = self.MIN_ENABLED_TIME_FRAME
        self.RECENT_TRADES_TO_CREATE = max(SIMULATOR_LAST_PRICES_TO_CHECK, ORDER_CREATION_LAST_TRADES_TO_USE)

    async def initialize_impl(self):
        pass

    async def modify_channels(self):
        # TODO foreach files
        await get_chan(TIME_CHANNEL, self.exchange_manager.exchange.name) \
            .modify(minimum_timestamp=self.exchange_importer.get_minimum_timestamp())

    def get_name(self):
        return self.__class__.__name__ + str(self.symbols)

    def symbol_exists(self, symbol):
        return symbol in self.symbols

    def time_frame_exists(self, time_frame):
        return time_frame in self.time_frame_get_times

    def get_progress(self):  # TODO
        if not self.min_time_frame_to_consider:
            return 0
        else:
            progresses = []
            return int(DataUtil.mean(progresses) * 100)

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
