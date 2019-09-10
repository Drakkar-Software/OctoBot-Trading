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

from octobot_commons.data_util import DataUtil
from octobot_commons.enums import PriceIndexes, TimeFrames
from octobot_commons.number_util import round_into_str_with_max_digits
from octobot_commons.symbol_util import split_symbol
from octobot_commons.time_frame_manager import TimeFrameManager

from octobot_trading.constants import CONFIG_SIMULATOR, CONFIG_DEFAULT_SIMULATOR_FEES, CONFIG_SIMULATOR_FEES, \
    CONFIG_SIMULATOR_FEES_MAKER, CONFIG_SIMULATOR_FEES_TAKER, CONFIG_SIMULATOR_FEES_WITHDRAW, \
    ORDER_CREATION_LAST_TRADES_TO_USE, SIMULATOR_LAST_PRICES_TO_CHECK
from octobot_trading.enums import ExchangeConstantsMarketStatusColumns, ExchangeConstantsMarketPropertyColumns, \
    TraderOrderType, FeePropertyColumns
from octobot_trading.exchanges.abstract_exchange import AbstractExchange
from octobot_trading.exchanges.data.exchange_symbol_data import ExchangeSymbolData
from octobot_trading.util import get_symbols


class ExchangeSimulator(AbstractExchange):
    def __init__(self, config, exchange_type, exchange_manager, config_backtesting_data_files):
        super().__init__(config, exchange_type, exchange_manager)
        self.initializing = True

        # initialize_backtesting(config, config_backtesting_data_files)
        #
        # if CONFIG_BACKTESTING not in self.config:
        #     raise Exception("Backtesting config not found")

        self.symbols = None
        self.data = None
        self.__set_symbol_list()

        self.config_time_frames = TimeFrameManager.get_config_time_frame(self.config)

        # set exchange manager attributes
        self.exchange_manager.client_symbols = self.symbols
        self.exchange_manager.client_time_frames = self.__get_available_timeframes()
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

        # self.backtesting = Backtesting(self.config, self)
        self.__prepare()
        self.initializing = False

    def get_name(self):
        return self.__class__.__name__ + str(self.symbols)

    def __get_available_timeframes(self):
        client_timeframes = {}
        for symbol in self.symbols:
            client_timeframes[symbol] = [tf.value
                                         for tf in self.config_time_frames
                                         if tf.value in self.get_ohlcv(symbol)]
        return client_timeframes

    # todo merge multiple file with the same symbol
    # def __set_symbol_list(self):
    #     self.symbols = []
    #     self.data = {}
    #     symbols_appended = {}
    #     relevant_symbols = set(get_symbols(self.config))
    #
    #     # parse files
    #     for file in self.config[CONFIG_BACKTESTING][CONFIG_BACKTESTING_DATA_FILES]:
    #         exchange_name, symbol, timestamp, data_type = interpret_file_name(file)
    #         if symbol is not None and symbol in relevant_symbols:
    #             if exchange_name is not None and timestamp is not None and data_type is not None:
    #
    #                 # check if symbol data already in symbols
    #                 # TODO check exchanges ?
    #                 if symbol not in symbols_appended:
    #                     symbols_appended[symbol] = 0
    #                     if symbols_appended[symbol] < int(timestamp):
    #                         symbols_appended[symbol] = int(timestamp)
    #                         self.symbols.append(symbol)
    #                         data = DataCollectorParser.parse(BACKTESTING_FILE_PATH, file)
    #                         self.data[symbol] = self.__fix_timestamps(data)

    # def __fix_timestamps(self, data):
    #     for time_frame in data[BACKTESTING_DATA_OHLCV]:
    #         need_to_uniform_timestamps = self.exchange_manager.need_to_uniformize_timestamp(
    #             data[BACKTESTING_DATA_OHLCV][time_frame][0][PriceIndexes.IND_PRICE_TIME.value])
    #         for data_list in data[BACKTESTING_DATA_OHLCV][time_frame]:
    #             if need_to_uniform_timestamps:
    #                 data_list[PriceIndexes.IND_PRICE_TIME.value] = \
    #                     self.get_uniform_timestamp(data_list[PriceIndexes.IND_PRICE_TIME.value])
    #     return data

    def __prepare(self):
        # create get times and init offsets
        for symbol in self.symbols:
            self.time_frame_get_times[symbol] = {}
            for time_frame in TimeFrames:
                self.time_frame_get_times[symbol][time_frame.value] = 0
                self.time_frames_offset = {}

    # # returns price (ohlcv) data for a given symbol
    # def get_ohlcv(self, symbol):
    #     return self.data[symbol][BACKTESTING_DATA_OHLCV]
    #
    # # returns trades data for a given symbol
    # def get_trades(self, symbol):
    #     return self.data[symbol][BACKTESTING_DATA_TRADES]

    def symbol_exists(self, symbol):
        return symbol in self.symbols

    def time_frame_exists(self, time_frame):
        return time_frame in self.time_frame_get_times

    def has_data_for_time_frame(self, symbol, time_frame):
        return time_frame in self.get_ohlcv(symbol) \
               and len(self.get_ohlcv(symbol)[time_frame]) >= self.DEFAULT_LIMIT + self.MIN_LIMIT

    @staticmethod
    def __extract_from_indexes(array, max_index, symbol, factor=1):
        max_limit = len(array)
        max_index *= factor

        # if max_index > max_limit:
        #     raise BacktestingEndedException(symbol)

        # else:
        #     return array[:max_index]

    def __get_candle_index(self, time_frame, symbol):
        if symbol not in self.data or time_frame not in self.get_ohlcv(symbol):
            self.logger.error("get_candle_index(self, timeframe, symbol) called with unset "
                              f"time_frames_offset[symbol][timeframe] for symbol: {symbol} and timeframe: {time_frame}."
                              " Call init_candles_offset(self, timeframes, symbol) to set candles indexes in order to "
                              "have consistent candles on different timeframes while using the timeframes you are "
                              "interested in")
        return self.time_frames_offset[symbol][time_frame] + self.time_frame_get_times[symbol][time_frame]

    def __extract_data_with_limit(self, symbol, time_frame):
        to_use_time_frame = time_frame.value or \
                            TimeFrameManager.find_min_time_frame(self.time_frames_offset[symbol].keys()).value
        return ExchangeSimulator.__extract_from_indexes(self.get_ohlcv(symbol)[to_use_time_frame],
                                                        self.__get_candle_index(to_use_time_frame, symbol),
                                                        symbol)

    def __ensure_available_data(self, symbol):
        # if symbol not in self.data:
        #     raise NoCandleDataForThisSymbolException(f"No candles data for {symbol} symbol.")
        pass

    def get_candles_exact(self, symbol, time_frame, min_index, max_index, return_list=True):
        self.__ensure_available_data(symbol)
        candles = self.get_ohlcv(symbol)[time_frame.value][min_index:max_index]
        self.get_symbol_data(symbol).handle_candles_update(time_frame, candles, replace_all=True)
        return self.get_symbol_data(symbol).get_symbol_prices(time_frame, None, return_list)

    async def get_symbol_prices(self, symbol, time_frame, limit=None, return_list=True):
        self.__ensure_available_data(symbol)
        candles = self.__extract_data_with_limit(symbol, time_frame)
        if time_frame is not None:
            self.time_frame_get_times[symbol][time_frame.value] += 1
            # if it's at least the second iteration: only use the last candle, otherwise use all
            if self.time_frame_get_times[symbol][time_frame.value] > 1:
                candles = candles[-1]
            self.get_symbol_data(symbol).handle_candles_update(time_frame, candles)

    def get_full_candles_data(self, symbol, time_frame):
        full_data = self.get_ohlcv(symbol)[time_frame.value]
        temp_symbol_data = ExchangeSymbolData(symbol)
        temp_symbol_data.handle_candles_update(time_frame, full_data, True)
        return temp_symbol_data.get_symbol_prices(time_frame)

    def _get_used_time_frames(self, symbol):
        if symbol in self.time_frames_offset:
            return self.time_frames_offset[symbol].keys()
        else:
            return [self.DEFAULT_TIME_FRAME_RECENT_TRADE_CREATOR]

    def _find_min_time_frame_to_consider(self, time_frames, symbol):
        time_frames_to_consider = copy.copy(time_frames)
        self.min_time_frame_to_consider[symbol] = None
        while not self.min_time_frame_to_consider[symbol] and time_frames_to_consider:
            potential_min_time_frame_to_consider = TimeFrameManager.find_min_time_frame(time_frames_to_consider).value
            if potential_min_time_frame_to_consider in self.get_ohlcv(symbol):
                self.min_time_frame_to_consider[symbol] = potential_min_time_frame_to_consider
            else:
                time_frames_to_consider.remove(potential_min_time_frame_to_consider)
        if self.min_time_frame_to_consider[symbol]:
            return self.get_ohlcv(symbol)[self.min_time_frame_to_consider[symbol]][self.MIN_LIMIT] \
                [PriceIndexes.IND_PRICE_TIME.value]
        else:
            self.logger.error(f"No data for the timeframes: {time_frames} in loaded backtesting file.")
            # if backtesting_enabled(self.config):
            #     self.backtesting.end(symbol)

    """
    Used to set self.time_frames_offset: will set offsets for all the given timeframes to keep data consistent 
    relatively to the smallest timeframe given in timeframes list.
    Ex: timeframes = ["1m", "1h", "1d"] => this will set offsets at 0 for "1m" because it is the smallest timeframe and
    will find the corresponding offset for the "1h" and "1d" timeframes if associated data are going further in the past
    than the "1m" timeframe. 
    This is used to avoid data from 500 hours ago mixed with data from 500 min ago for example.
    """

    def init_candles_offset(self, time_frames, symbol):
        min_time_frame_to_consider = dict()
        min_time_frame_to_consider[symbol] = self._find_min_time_frame_to_consider(time_frames, symbol)
        if symbol not in self.time_frames_offset:
            self.time_frames_offset[symbol] = {}
        for time_frame in time_frames:
            if time_frame.value in self.get_ohlcv(symbol):
                found_index = False
                for index, candle in enumerate(self.get_ohlcv(symbol)[time_frame.value]):
                    if candle[PriceIndexes.IND_PRICE_TIME.value] >= min_time_frame_to_consider[symbol]:
                        index_to_use = index
                        if candle[PriceIndexes.IND_PRICE_TIME.value] > min_time_frame_to_consider[symbol] and \
                                index > 0:
                            # if superior: take the prvious one
                            index_to_use = index - 1
                        found_index = True
                        self.time_frames_offset[symbol][time_frame.value] = index_to_use
                        break
                if not found_index:
                    self.time_frames_offset[symbol][time_frame.value] = \
                        len(self.get_ohlcv(symbol)[time_frame.value]) - 1

    def get_min_time_frame(self, symbol):
        if symbol in self.min_time_frame_to_consider:
            return self.min_time_frame_to_consider[symbol]
        else:
            return None

    def get_progress(self):
        if not self.min_time_frame_to_consider:
            return 0
        else:
            progresses = []
            for symbol in self.time_frame_get_times:
                if symbol in self.min_time_frame_to_consider:
                    current = self.time_frame_get_times[symbol][self.min_time_frame_to_consider[symbol]]
                    nb_max = len(self.get_ohlcv(symbol)[self.min_time_frame_to_consider[symbol]])
                    progresses.append(current / nb_max)
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

    async def end_backtesting(self, symbol):
        await self.backtesting.end(symbol)

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
