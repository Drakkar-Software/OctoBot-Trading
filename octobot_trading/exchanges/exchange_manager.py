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
import time

from octobot_channels.util.channel_creator import create_all_subclasses_channel
from octobot_commons.config_util import has_invalid_default_config_value
from octobot_commons.constants import CONFIG_ENABLED_OPTION, CONFIG_WILDCARD, MIN_EVAL_TIME_FRAME
from octobot_commons.enums import PriceIndexes
from octobot_commons.logging.logging_util import get_logger
from octobot_commons.symbol_util import split_symbol
from octobot_commons.time_frame_manager import TimeFrameManager
from octobot_commons.timestamp_util import is_valid_timestamp

from octobot_trading.channels import BALANCE_CHANNEL, OHLCV_CHANNEL, ORDER_BOOK_CHANNEL, RECENT_TRADES_CHANNEL, \
    TICKER_CHANNEL, ORDERS_CHANNEL, KLINE_CHANNEL, TRADES_CHANNEL, POSITIONS_CHANNEL, BALANCE_PROFITABILITY_CHANNEL, \
    TIME_CHANNEL
from octobot_trading.channels.exchange_channel import ExchangeChannel, get_chan, set_chan
from octobot_trading.constants import CONFIG_TRADER, CONFIG_CRYPTO_CURRENCIES, CONFIG_CRYPTO_PAIRS, \
    CONFIG_CRYPTO_QUOTE, CONFIG_CRYPTO_ADD, CONFIG_EXCHANGE_WEB_SOCKET, CONFIG_EXCHANGES, CONFIG_EXCHANGE_SECRET, \
    CONFIG_EXCHANGE_KEY
from octobot_trading.exchanges.exchange_simulator import ExchangeSimulator
from octobot_trading.exchanges.data.exchange_global_data import ExchangeGlobalData
from octobot_trading.exchanges.data.exchange_personal_data import ExchangePersonalData
from octobot_trading.exchanges.data.exchange_symbols_data import ExchangeSymbolsData
from octobot_trading.exchanges.rest_exchange import RestExchange
from octobot_trading.exchanges.websockets.abstract_websocket import AbstractWebsocket
from octobot_trading.producers.balance_updater import BalanceUpdater, BalanceProfitabilityUpdater
from octobot_trading.producers.kline_updater import KlineUpdater
from octobot_trading.producers.ohlcv_updater import OHLCVUpdater
from octobot_trading.producers.order_book_updater import OrderBookUpdater
from octobot_trading.producers.orders_updater import CloseOrdersUpdater, OpenOrdersUpdater
from octobot_trading.producers.positions_updater import PositionsUpdater
from octobot_trading.producers.recent_trade_updater import RecentTradeUpdater
from octobot_trading.producers.simulator.balance_updater_simulator import BalanceProfitabilityUpdaterSimulator
from octobot_trading.producers.simulator.kline_updater_simulator import KlineUpdaterSimulator
from octobot_trading.producers.simulator.ohlcv_updater_simulator import OHLCVUpdaterSimulator
from octobot_trading.producers.simulator.order_book_updater_simulator import OrderBookUpdaterSimulator
from octobot_trading.producers.simulator.orders_updater_simulator import OpenOrdersUpdaterSimulator, \
    CloseOrdersUpdaterSimulator
from octobot_trading.producers.simulator.recent_trade_updater_simulator import RecentTradeUpdaterSimulator
from octobot_trading.producers.simulator.ticker_updater_simulator import TickerUpdaterSimulator
from octobot_trading.producers.ticker_updater import TickerUpdater
from octobot_trading.producers.time_updater import TimeUpdater
from octobot_trading.producers.trades_updater import TradesUpdater
from octobot_trading.util import is_trader_simulator_enabled
from octobot_trading.util.initializable import Initializable


class ExchangeManager(Initializable):
    WEB_SOCKET_RESET_MIN_INTERVAL = 15

    def __init__(self, config, exchange_class_string,
                 is_simulated=False,
                 is_backtesting=False,
                 rest_only=False,
                 ignore_config=False,
                 is_collecting=False,
                 backtesting_files=None):
        super().__init__()
        self.config = config
        self.exchange_class_string = exchange_class_string
        self.rest_only = rest_only
        self.ignore_config = ignore_config
        self.backtesting_files = backtesting_files
        self.logger = get_logger(self.__class__.__name__)

        self.is_ready = False
        self.is_backtesting = is_backtesting
        self.is_simulated = is_simulated
        self.is_collecting = is_collecting
        self.is_trader_simulated = is_trader_simulator_enabled(self.config)

        self.trader = None
        self.exchange = None

        self.client_symbols = []
        self.client_time_frames = {}

        self.cryptocurrencies_traded_pairs = {}
        self.traded_pairs = []
        self.time_frames = []

        self.exchange_global_data = ExchangeGlobalData(self)
        self.exchange_personal_data = ExchangePersonalData(self)
        self.exchange_symbols_data = ExchangeSymbolsData(self)

    async def initialize_impl(self):
        await self.create_exchanges()

    async def register_trader(self, trader):
        self.trader = trader
        await self.exchange_personal_data.initialize()
        await self.exchange_global_data.initialize()

    def _load_constants(self):
        self._load_config_symbols_and_time_frames()
        self._set_config_time_frame()
        self._set_config_traded_pairs()

    def need_user_stream(self):
        return self.config[CONFIG_TRADER][CONFIG_ENABLED_OPTION]

    def reset_exchange_symbols_data(self):
        self.exchange_symbols_data = ExchangeSymbolsData(self)

    def reset_exchange_personal_data(self):
        self.exchange_personal_data = ExchangePersonalData(self)

    async def create_exchanges(self):
        self.exchange_type = RestExchange.create_exchange_type(self.exchange_class_string)

        if not self.is_backtesting:
            # create REST based on ccxt exchange
            self.exchange = RestExchange(self.config, self.exchange_type, self)
            await self.exchange.initialize()

            self._load_constants()
            await self._create_exchange_channels()

            # create Websocket exchange if possible
            if not self.rest_only:
                # search for websocket
                if self.check_web_socket_config(self.exchange.name):
                    self.exchange_web_socket = self._search_and_create_websocket(AbstractWebsocket)

        # if simulated : create exchange simulator instance
        else:
            self.exchange = ExchangeSimulator(self.config, self.exchange_type, self, self.backtesting_files)
            await self.exchange.initialize()
            self._set_config_traded_pairs()
            await self._create_exchange_channels()

        # create exchange producers if necessary
        await self._create_exchange_producers()

        if self.is_backtesting:
            await self.exchange.modify_channels()

        self.is_ready = True

    async def _create_exchange_channels(self):  # TODO filter creation
        await create_all_subclasses_channel(ExchangeChannel, set_chan, exchange_manager=self)

    async def _create_exchange_producers(self):
        # Real data producers
        if self.rest_only and not self.is_backtesting:  # TODO or filter creation with WS
            await OHLCVUpdater(get_chan(OHLCV_CHANNEL, self.exchange.name)).run()
            await OrderBookUpdater(get_chan(ORDER_BOOK_CHANNEL, self.exchange.name)).run()
            await RecentTradeUpdater(get_chan(RECENT_TRADES_CHANNEL, self.exchange.name)).run()
            await TickerUpdater(get_chan(TICKER_CHANNEL, self.exchange.name)).run()
            await KlineUpdater(get_chan(KLINE_CHANNEL, self.exchange.name)).run()

        if self.exchange.is_authenticated and not (self.is_simulated or self.is_backtesting or self.is_collecting):  # TODO or filter creation with WS
            await BalanceUpdater(get_chan(BALANCE_CHANNEL, self.exchange.name)).run()
            await BalanceProfitabilityUpdater(get_chan(BALANCE_PROFITABILITY_CHANNEL, self.exchange.name)).run()
            await CloseOrdersUpdater(get_chan(ORDERS_CHANNEL, self.exchange.name)).run()
            await OpenOrdersUpdater(get_chan(ORDERS_CHANNEL, self.exchange.name)).run()
            await TradesUpdater(get_chan(TRADES_CHANNEL, self.exchange.name)).run()
            await PositionsUpdater(get_chan(POSITIONS_CHANNEL, self.exchange.name)).run()

        # Simulated producers
        if (not self.exchange.is_authenticated or self.is_simulated or self.is_backtesting) and not self.is_collecting:
            # Not required
            # await BalanceUpdaterSimulator(get_chan(BALANCE_CHANNEL, self.exchange.name)).run()
            await BalanceProfitabilityUpdaterSimulator(get_chan(BALANCE_PROFITABILITY_CHANNEL, self.exchange.name)).run()

            await CloseOrdersUpdaterSimulator(get_chan(ORDERS_CHANNEL, self.exchange.name)).run()
            await OpenOrdersUpdaterSimulator(get_chan(ORDERS_CHANNEL, self.exchange.name)).run()

            # Not required
            # await TradesUpdaterSimulator(get_chan(TRADES_CHANNEL, self.exchange.name)).run()

            # TODO
            # await PositionsUpdaterSimulator(get_chan(POSITIONS_CHANNEL, self.exchange.name)).run()

        if self.is_backtesting:
            await TimeUpdater(get_chan(TIME_CHANNEL, self.exchange.name)).run()
            await OHLCVUpdaterSimulator(get_chan(OHLCV_CHANNEL, self.exchange.name)).run()
            await OrderBookUpdaterSimulator(get_chan(ORDER_BOOK_CHANNEL, self.exchange.name)).run()
            await RecentTradeUpdaterSimulator(get_chan(RECENT_TRADES_CHANNEL, self.exchange.name)).run()
            await TickerUpdaterSimulator(get_chan(TICKER_CHANNEL, self.exchange.name)).run()
            await KlineUpdaterSimulator(get_chan(KLINE_CHANNEL, self.exchange.name)).run()

    def _search_and_create_websocket(self, websocket_class):
        for socket_manager in websocket_class.__subclasses__():
            # add websocket exchange if available
            if socket_manager.has_name(self.exchange.name):
                exchange_web_socket = socket_manager.get_websocket_client(self.config, self)

                # init websocket
                try:
                    exchange_web_socket.init_web_sockets(self.time_frames, self.traded_pairs)

                    # start the websocket
                    exchange_web_socket.start_sockets()

                    return exchange_web_socket
                except Exception as e:
                    self.logger.error(f"Fail to init websocket for {websocket_class} : {e}")
                    raise e
        return None

    def did_not_just_try_to_reset_web_socket(self):
        if self.last_web_socket_reset is None:
            return True
        else:
            return time.time() - self.last_web_socket_reset > self.WEB_SOCKET_RESET_MIN_INTERVAL

    def reset_websocket_exchange(self):
        if self.did_not_just_try_to_reset_web_socket():
            # set web socket reset time
            self.last_web_socket_reset = time.time()

            # clear databases
            # self.reset_symbols_data()
            self.reset_exchange_personal_data()

            # close and restart websockets
            if self.websocket_available():
                self.exchange_web_socket.close_and_restart_sockets()

            # databases will be filled at the next calls similarly to bot startup process

    # Exchange configuration functions
    def check_config(self, exchange_name):
        if CONFIG_EXCHANGE_KEY not in self.config[CONFIG_EXCHANGES][exchange_name] \
                or CONFIG_EXCHANGE_SECRET not in self.config[CONFIG_EXCHANGES][exchange_name]:
            return False
        else:
            return True

    def force_disable_web_socket(self, exchange_name):
        return CONFIG_EXCHANGE_WEB_SOCKET in self.config[CONFIG_EXCHANGES][exchange_name] \
               and not self.config[CONFIG_EXCHANGES][exchange_name][CONFIG_EXCHANGE_WEB_SOCKET]

    def check_web_socket_config(self, exchange_name):
        return not self.force_disable_web_socket(exchange_name)

    def enabled(self):
        # if we can get candlestick data
        if self.is_simulated or self.exchange.name in self.config[CONFIG_EXCHANGES]:
            return True
        else:
            self.logger.warning(f"Exchange {self.exchange.name} is currently disabled")
            return False

    def get_exchange_symbol_id(self, symbol):
        return self.exchange.get_exchange_pair(symbol)

    def get_exchange_symbol(self, symbol):
        return self.exchange.get_pair_from_exchange(symbol)

    def get_exchange_quote_and_base(self, symbol):
        return self.exchange.get_split_pair_from_exchange(symbol)

    def _load_config_symbols_and_time_frames(self):
        client = self.exchange.client
        if client:
            self.client_symbols = client.symbols
            self.client_time_frames[CONFIG_WILDCARD] = client.timeframes if hasattr(client, "timeframes") else {}
        else:
            self.logger.error("Failed to load client from REST exchange")
            self._raise_exchange_load_error()

    # SYMBOLS
    def _set_config_traded_pairs(self):
        self.cryptocurrencies_traded_pairs = {}
        for cryptocurrency in self.config[CONFIG_CRYPTO_CURRENCIES]:
            if self.config[CONFIG_CRYPTO_CURRENCIES][cryptocurrency][CONFIG_CRYPTO_PAIRS]:
                if self.config[CONFIG_CRYPTO_CURRENCIES][cryptocurrency][CONFIG_CRYPTO_PAIRS] != CONFIG_WILDCARD:
                    self.cryptocurrencies_traded_pairs[cryptocurrency] = []
                    for symbol in self.config[CONFIG_CRYPTO_CURRENCIES][cryptocurrency][CONFIG_CRYPTO_PAIRS]:
                        if self.symbol_exists(symbol):
                            self.cryptocurrencies_traded_pairs[cryptocurrency].append(symbol)
                        else:
                            self.logger.error(f"{self.exchange.name} is not supporting the "
                                              f"{symbol} trading pair.")

                else:
                    self.cryptocurrencies_traded_pairs[cryptocurrency] = self._create_wildcard_symbol_list(
                        self.config[CONFIG_CRYPTO_CURRENCIES][cryptocurrency][CONFIG_CRYPTO_QUOTE])

                    # additionnal pairs
                    if CONFIG_CRYPTO_ADD in self.config[CONFIG_CRYPTO_CURRENCIES][cryptocurrency]:
                        self.cryptocurrencies_traded_pairs[cryptocurrency] += self._add_tradable_symbols(cryptocurrency)

                # add to global traded pairs
                if not self.cryptocurrencies_traded_pairs[cryptocurrency]:
                    self.logger.error(f"{self.exchange.name} is not supporting any {cryptocurrency} trading pair "
                                      f"from current configuration.")
                self.traded_pairs += self.cryptocurrencies_traded_pairs[cryptocurrency]
            else:
                self.logger.error(f"Current configuration for {cryptocurrency} is not including any trading pair, "
                                  f"this asset can't be traded and related orders won't be loaded. "
                                  f"OctoBot requires at least one trading pair in configuration to handle an asset. "
                                  f"You can add trading pair(s) for each asset in the configuration section.")

    def get_traded_pairs(self, crypto_currency=None):
        if crypto_currency:
            if crypto_currency in self.cryptocurrencies_traded_pairs:
                return self.cryptocurrencies_traded_pairs[crypto_currency]
            else:
                return []
        return self.traded_pairs

    def symbol_exists(self, symbol):
        if self.client_symbols is None:
            self.logger.error(f"Failed to load available symbols from REST exchange, impossible to check if "
                              f"{symbol} exists on {self.exchange.name}")
            return False
        return symbol in self.client_symbols

    def _create_wildcard_symbol_list(self, crypto_currency):
        return [s for s in [ExchangeManager._is_tradable_with_cryptocurrency(symbol, crypto_currency)
                            for symbol in self.client_symbols]
                if s is not None]

    def _add_tradable_symbols(self, crypto_currency):
        return [
            symbol
            for symbol in self.config[CONFIG_CRYPTO_CURRENCIES][crypto_currency][CONFIG_CRYPTO_ADD]
            if self.symbol_exists(symbol) and symbol not in self.cryptocurrencies_traded_pairs[crypto_currency]
        ]

    @staticmethod
    def _is_tradable_with_cryptocurrency(symbol, crypto_currency):
        return symbol if split_symbol(symbol)[1] == crypto_currency else None

    # TIME FRAMES
    def _set_config_time_frame(self):
        for time_frame in TimeFrameManager.get_config_time_frame(self.config):
            if self.time_frame_exists(time_frame.value):
                self.time_frames.append(time_frame)
        # add shortest timeframe for realtime evaluators
        client_shortest_time_frame = TimeFrameManager.find_min_time_frame(
            self.client_time_frames[CONFIG_WILDCARD], MIN_EVAL_TIME_FRAME)
        if client_shortest_time_frame not in self.time_frames:
            self.time_frames.append(client_shortest_time_frame)

        self.time_frames = TimeFrameManager.sort_time_frames(self.time_frames, reverse=True)

    def time_frame_exists(self, time_frame, symbol=None):
        if CONFIG_WILDCARD in self.client_time_frames or symbol is None:
            return time_frame in self.client_time_frames[CONFIG_WILDCARD]
        else:
            # should only happen in backtesting (or with an exchange with different timeframes per symbol)
            return time_frame in self.client_time_frames[symbol]

    def get_rate_limit(self):
        return self.exchange_type.rateLimit / 1000

    @staticmethod
    def need_to_uniformize_timestamp(timestamp):
        return not is_valid_timestamp(timestamp)

    def uniformize_candles_if_necessary(self, candle_or_candles):
        if candle_or_candles:  # TODO improve
            if isinstance(candle_or_candles[0], list):
                if self.need_to_uniformize_timestamp(candle_or_candles[0][PriceIndexes.IND_PRICE_TIME.value]):
                    self._uniformize_candles_timestamps(candle_or_candles)
            else:
                if self.need_to_uniformize_timestamp(candle_or_candles[PriceIndexes.IND_PRICE_TIME.value]):
                    self._uniformize_candle_timestamps(candle_or_candles)
            return candle_or_candles

    def _uniformize_candles_timestamps(self, candles):
        for candle in candles:
            self._uniformize_candle_timestamps(candle)

    def _uniformize_candle_timestamps(self, candle):
        candle[PriceIndexes.IND_PRICE_TIME.value] = \
            self.exchange.get_uniform_timestamp(candle[PriceIndexes.IND_PRICE_TIME.value])

    # Exceptions
    def _raise_exchange_load_error(self):
        raise Exception(f"{self.exchange} - Failed to load exchange instances")

    def get_exchange_name(self):
        return self.exchange_type.__name__

    def should_decrypt_token(self, logger):
        if has_invalid_default_config_value(
                self.config[CONFIG_EXCHANGES][self.get_exchange_name()][CONFIG_EXCHANGE_KEY],
                self.config[CONFIG_EXCHANGES][self.get_exchange_name()][CONFIG_EXCHANGE_SECRET]):
            logger.warning("Exchange configuration tokens are not set yet, to use OctoBot's real trader's features, "
                           "please enter your api tokens in exchange configuration")
            return False
        return True

    @staticmethod
    def handle_token_error(error, logger):
        logger.error(f"Exchange configuration tokens are invalid : please check your configuration ! "
                     f"({error.__class__.__name__})")

    def get_symbol_data(self, symbol):
        return self.exchange_symbols_data.get_exchange_symbol_data(symbol)
