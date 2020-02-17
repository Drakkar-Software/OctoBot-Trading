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
import uuid

from octobot_channels.util.channel_creator import create_all_subclasses_channel
from octobot_commons.config_util import has_invalid_default_config_value
from octobot_commons.constants import CONFIG_ENABLED_OPTION
from octobot_commons.enums import PriceIndexes
from octobot_commons.logging.logging_util import get_logger
from octobot_commons.timestamp_util import is_valid_timestamp
from octobot_trading.channels.exchange_channel import ExchangeChannel, get_chan, set_chan, get_exchange_channels, \
    del_chan, del_exchange_channel_container
from octobot_trading.constants import CONFIG_TRADER, CONFIG_EXCHANGES, CONFIG_EXCHANGE_SECRET, CONFIG_EXCHANGE_KEY, \
    WEBSOCKET_FEEDS_TO_TRADING_CHANNELS
from octobot_trading.exchanges.data.exchange_config_data import ExchangeConfig
from octobot_trading.exchanges.data.exchange_personal_data import ExchangePersonalData
from octobot_trading.exchanges.data.exchange_symbols_data import ExchangeSymbolsData
from octobot_trading.exchanges.exchange_simulator import ExchangeSimulator
from octobot_trading.exchanges.exchanges import Exchanges
from octobot_trading.exchanges.margin.margin_util import get_margin_exchange_class_from_exchange_type
from octobot_trading.exchanges.rest_exchange import RestExchange
from octobot_trading.exchanges.websockets.abstract_websocket import AbstractWebsocket
from octobot_trading.exchanges.websockets.websockets_util import check_web_socket_config, search_websocket_class
from octobot_trading.producers import UNAUTHENTICATED_UPDATER_PRODUCERS, AUTHENTICATED_UPDATER_PRODUCERS
from octobot_trading.producers.simulator import AUTHENTICATED_UPDATER_SIMULATOR_PRODUCERS
from octobot_trading.util import is_trader_simulator_enabled
from octobot_trading.util.initializable import Initializable


class ExchangeManager(Initializable):
    def __init__(self, config, exchange_class_string):
        super().__init__()
        self.id = str(uuid.uuid4())
        self.config = config
        self.exchange_class_string = exchange_class_string
        self.exchange_name = exchange_class_string
        self._logger = get_logger(self.__class__.__name__)

        self.is_ready = False
        self.is_simulated: bool = False
        self.is_backtesting: bool = False
        self.rest_only: bool = False
        self.ignore_config: bool = False
        self.is_collecting: bool = False
        self.is_margin: bool = False
        self.is_sandboxed: bool = False

        # exchange_only is True when exchange channels are not required (therefore not created)
        self.exchange_only: bool = False

        self.backtesting_files: list = None

        self.is_trader_simulated = is_trader_simulator_enabled(self.config)
        self.has_websocket = False

        self.trader = None
        self.exchange = None
        self.trading_modes = []

        self.exchange_web_socket = None
        self.exchange_type = None

        self.client_symbols = []
        self.client_time_frames = []

        self.exchange_config = ExchangeConfig(self)
        self.exchange_personal_data = ExchangePersonalData(self)
        self.exchange_symbols_data = ExchangeSymbolsData(self)

    async def initialize_impl(self):
        await self.create_exchanges()

    async def stop(self):
        for trading_mode in self.trading_modes:
            await trading_mode.stop()
        if self.exchange is not None:
            await self.exchange.stop()
            Exchanges.instance().del_exchange(self.exchange.name, self.id)
            self.exchange.exchange_manager = None
            if not self.exchange_only:
                await self.stop_exchange_channels()
        if self.exchange_personal_data is not None and \
                self.exchange_personal_data.portfolio_manager is not None:
            self.exchange_personal_data.portfolio_manager.portfolio_profitability = None
        self.exchange_config = None
        self.exchange_personal_data = None
        self.exchange_symbols_data = None
        self.trader = None
        self.trading_modes = []

    async def stop_exchange_channels(self):
        try:
            chan_names = list(get_exchange_channels(self.id).keys())
            for channel_name in chan_names:
                channel = get_chan(channel_name, self.id)
                await channel.stop()
                for consumer in channel.consumers:
                    await channel.remove_consumer(consumer)
                get_chan(channel_name, self.id).flush()
                del_chan(channel_name, self.id)
            del_exchange_channel_container(self.id)
        except KeyError:
            self._logger.error(f"No exchange channel for this exchange (id: {self.id})")

    async def register_trader(self, trader):
        self.trader = trader
        await self.exchange_personal_data.initialize()
        await self.exchange_config.initialize()

    def _load_constants(self):
        self._load_config_symbols_and_time_frames()
        self.exchange_config.set_config_time_frame()
        self.exchange_config.set_config_traded_pairs()

    def need_user_stream(self):
        return self.config[CONFIG_TRADER][CONFIG_ENABLED_OPTION]

    def reset_exchange_symbols_data(self):
        self.exchange_symbols_data = ExchangeSymbolsData(self)

    def reset_exchange_personal_data(self):
        self.exchange_personal_data = ExchangePersonalData(self)

    async def create_exchanges(self):
        self.exchange_type = RestExchange.create_exchange_type(self.exchange_class_string)

        if not self.is_backtesting:
            # real : create a rest or websocket exchange instance
            await self._create_real_exchange()
        else:
            # simulated : create exchange simulator instance
            await self._create_simulated_exchange()

        if not self.exchange_only:
            # create exchange producers if necessary
            await self._create_exchange_producers()

        if self.is_backtesting:
            await self._init_simulated_exchange()

        self.exchange_name = self.exchange.name
        self.is_ready = True

    """
    Real exchange
    """
    async def _create_real_exchange(self):
        # create REST based on ccxt exchange
        if self.is_margin:
            await self._search_and_create_margin_exchange()
        else:
            self.exchange = RestExchange(config=self.config,
                                         exchange_type=self.exchange_type,
                                         exchange_manager=self,
                                         is_sandboxed=self.is_sandboxed)

        await self.exchange.initialize()

        self._load_constants()

        if not self.exchange_only:
            await self._create_exchange_channels()

        # create Websocket exchange if possible
        if not self.rest_only:
            # search for websocket
            if check_web_socket_config(self.config, self.exchange.name):
                await self._search_and_create_websocket()

    """
    Simulated Exchange
    """
    async def _create_simulated_exchange(self):
        self.exchange = ExchangeSimulator(self.config, self.exchange_type, self, self.backtesting_files)
        await self.exchange.initialize()
        await self._initialize_simulator_time_frames()
        self.exchange_config.set_config_time_frame()
        self.exchange_config.set_config_traded_pairs()
        await self._create_exchange_channels()

    async def _init_simulated_exchange(self):
        try:
            await self.exchange.modify_channels()
            await self.exchange.create_backtesting_exchange_producers()
            await self.exchange.start_backtesting()
        except ValueError:
            self._logger.error("Not enough exchange data to calculate backtesting duration")
            await self.stop()

    """
    Margin exchange
    """
    async def _search_and_create_margin_exchange(self):
        margin_exchange_class = get_margin_exchange_class_from_exchange_type(self.exchange_type)
        self.exchange = margin_exchange_class(self.config, self.exchange_type, self)

    """
    Exchange channels
    """
    async def _create_exchange_channels(self):  # TODO filter creation --> not required if pause is managed
        await create_all_subclasses_channel(ExchangeChannel, set_chan, exchange_manager=self)

    async def _create_exchange_producers(self):
        # Real data producers
        if not self.is_backtesting:
            for updater in UNAUTHENTICATED_UPDATER_PRODUCERS:
                if not self._is_managed_by_websocket(updater.CHANNEL_NAME):
                    await updater(get_chan(updater.CHANNEL_NAME, self.id)).run()

        if self.exchange.is_authenticated and not (self.is_simulated or self.is_backtesting or self.is_collecting):
            for updater in AUTHENTICATED_UPDATER_PRODUCERS:
                if not self._is_managed_by_websocket(updater.CHANNEL_NAME):
                    await updater(get_chan(updater.CHANNEL_NAME, self.id)).run()

        # Simulated producers
        if (not self.exchange.is_authenticated or self.is_simulated or self.is_backtesting) and not self.is_collecting:
            for updater in AUTHENTICATED_UPDATER_SIMULATOR_PRODUCERS:
                await updater(get_chan(updater.CHANNEL_NAME, self.id)).run()

    """
    Websocket
    """
    def _is_managed_by_websocket(self, channel):  # TODO improve checker
        return not self.rest_only and self.has_websocket and \
               any([self.exchange_web_socket.is_feed_available(feed)
                    for feed in WEBSOCKET_FEEDS_TO_TRADING_CHANNELS[channel]])

    async def _search_and_create_websocket(self):
        socket_manager = search_websocket_class(AbstractWebsocket, self.exchange_name)
        if socket_manager is not None:
            await self._create_websocket(AbstractWebsocket.__name__, socket_manager)

    async def _create_websocket(self, websocket_class_name, socket_manager):
        try:
            self.exchange_web_socket = socket_manager.get_websocket_client(self.config, self)
            await self._init_websocket()
            self._logger.info(f"{socket_manager.get_name()} connected to {self.exchange.name}")
        except Exception as e:
            self._logger.error(f"Fail to init websocket for {websocket_class_name} : {e}")
            self.exchange_web_socket = None
            self.has_websocket = False
            raise e

    async def _init_websocket(self):
        await self.exchange_web_socket.init_web_sockets(self.exchange_config.traded_time_frames,
                                                        self.exchange_config.traded_symbol_pairs)

        self.exchange_web_socket.start_sockets()

        self.has_websocket = self.exchange_web_socket.is_websocket_running

    """
    Exchange Configuration
    """
    def check_config(self, exchange_name):
        if CONFIG_EXCHANGE_KEY not in self.config[CONFIG_EXCHANGES][exchange_name] \
                or CONFIG_EXCHANGE_SECRET not in self.config[CONFIG_EXCHANGES][exchange_name]:
            return False
        else:
            return True

    def enabled(self):
        # if we can get candlestick data
        if self.is_simulated or self.exchange.name in self.config[CONFIG_EXCHANGES]:
            return True
        else:
            self._logger.warning(f"Exchange {self.exchange.name} is currently disabled")
            return False

    def get_exchange_symbol_id(self, symbol):
        return self.exchange.get_exchange_pair(symbol)

    def get_exchange_symbol(self, symbol):
        return self.exchange.get_pair_from_exchange(symbol)

    def get_exchange_quote_and_base(self, symbol):
        return self.exchange.get_split_pair_from_exchange(symbol)

    def get_exchange_backtesting(self):
        return self.exchange.backtesting if isinstance(self.exchange, ExchangeSimulator) else None

    def _load_config_symbols_and_time_frames(self):
        client = self.exchange.client
        if client:
            self.client_symbols = client.symbols
            self.client_time_frames = list(client.timeframes.values()) if hasattr(client, "timeframes") else []
        else:
            self._logger.error("Failed to load client from REST exchange")
            self._raise_exchange_load_error()

    async def _initialize_simulator_time_frames(self):
        self.client_time_frames = self.exchange.get_available_time_frames()

    # SYMBOLS
    def symbol_exists(self, symbol):
        if self.client_symbols is None:
            self._logger.error(f"Failed to load available symbols from REST exchange, impossible to check if "
                               f"{symbol} exists on {self.exchange.name}")
            return False
        return symbol in self.client_symbols

    # TIME FRAMES
    def time_frame_exists(self, time_frame):
        if not self.client_time_frames:
            return False
        return time_frame in self.client_time_frames

    def get_rate_limit(self):
        return self.exchange_type.rateLimit / 1000

    @staticmethod
    def need_to_uniformize_timestamp(timestamp):
        return not is_valid_timestamp(timestamp)

    def get_uniformized_timestamp(self, timestamp):
        if ExchangeManager.need_to_uniformize_timestamp(timestamp):
            return self.exchange.get_uniform_timestamp(timestamp)
        return timestamp

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
