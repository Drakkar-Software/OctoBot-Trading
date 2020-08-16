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
from ccxt import AuthenticationError

from octobot_channels.util.channel_creator import create_all_subclasses_channel
from octobot_commons.config_util import has_invalid_default_config_value, decrypt_element_if_possible
from octobot_commons.constants import CONFIG_ENABLED_OPTION
from octobot_commons.enums import PriceIndexes
from octobot_commons.logging.logging_util import get_logger
from octobot_commons.timestamp_util import is_valid_timestamp
from octobot_trading.channels.exchange_channel import get_exchange_channels, del_chan, set_chan, get_chan, \
    del_exchange_channel_container, ExchangeChannel, TimeFrameExchangeChannel
from octobot_trading.constants import CONFIG_TRADER, CONFIG_EXCHANGES, CONFIG_EXCHANGE_SECRET, CONFIG_EXCHANGE_KEY, \
    WEBSOCKET_FEEDS_TO_TRADING_CHANNELS, CONFIG_EXCHANGE_PASSWORD
from octobot_trading.enums import RestExchangePairsRefreshMaxThresholds
from octobot_trading.exchanges.data.exchange_config_data import ExchangeConfig
from octobot_trading.exchanges.data.exchange_personal_data import ExchangePersonalData
from octobot_trading.exchanges.data.exchange_symbols_data import ExchangeSymbolsData
from octobot_trading.exchanges.exchange_simulator import ExchangeSimulator
from octobot_trading.exchanges.exchanges import Exchanges
from octobot_trading.exchanges.exchange_util import get_margin_exchange_class, get_rest_exchange_class, \
    get_future_exchange_class, get_spot_exchange_class
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
        self.tentacles_setup_config = None
        self.exchange_class_string = exchange_class_string
        self.exchange_name = exchange_class_string
        self._logger = get_logger(self.__class__.__name__)

        self.is_ready = False
        self.is_simulated: bool = False
        self.is_backtesting: bool = False
        self.rest_only: bool = False
        self.ignore_config: bool = False
        self.is_collecting: bool = False
        self.is_spot_only: bool = False
        self.is_margin: bool = False
        self.is_future: bool = False
        self.is_sandboxed: bool = False
        self.is_trading: bool = True
        self.without_auth: bool = False

        # exchange_only is True when exchange channels are not required (therefore not created)
        self.exchange_only: bool = False

        self.backtesting = None

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

    async def stop(self, warning_on_missing_elements=True):
        for trading_mode in self.trading_modes:
            await trading_mode.stop()
        if self.exchange is not None:
            if not self.exchange_only:
                await self.stop_exchange_channels(should_warn=warning_on_missing_elements)
            await self.exchange.stop()
            Exchanges.instance().del_exchange(self.exchange.name, self.id, should_warn=warning_on_missing_elements)
            self.exchange.exchange_manager = None
        if self.exchange_personal_data is not None:
            self.exchange_personal_data.clear()
        self.exchange_config = None
        self.exchange_personal_data = None
        self.exchange_symbols_data = None
        self.trader = None
        self.trading_modes = []
        self.backtesting = None

    async def stop_exchange_channels(self, should_warn=True):
        try:
            for channel_name in list(get_exchange_channels(self.id)):
                channel = get_chan(channel_name, self.id)
                await channel.stop()
                for consumer in channel.consumers:
                    await channel.remove_consumer(consumer)
                get_chan(channel_name, self.id).flush()
                del_chan(channel_name, self.id)
            del_exchange_channel_container(self.id)
        except KeyError:
            if should_warn:
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
        if self.is_sandboxed:
            self._logger.info(f"Using sandbox exchange for {self.exchange_name}")
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
        if self.is_spot_only:
            await self._search_and_create_spot_exchange()
        elif self.is_future:
            await self._search_and_create_future_exchange()
        elif self.is_margin:
            await self._search_and_create_margin_exchange()

        if not self.exchange:
            await self._search_and_create_rest_exchange()

        try:
            await self.exchange.initialize()
        except AuthenticationError:
            self._logger.error("Authentication error, retrying without authentication...")
            self.without_auth = True
            await self._create_real_exchange()
            return

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
        self.exchange = ExchangeSimulator(self.config, self.exchange_type, self, self.backtesting)
        await self.exchange.initialize()
        self._initialize_simulator_time_frames()
        self.exchange_config.set_config_time_frame()
        self.exchange_config.set_config_traded_pairs()
        await self._create_exchange_channels()

    async def _init_simulated_exchange(self):
        await self.exchange.create_backtesting_exchange_producers()

    """
    Rest exchange
    """

    async def _search_and_create_rest_exchange(self):
        rest_exchange_class = get_rest_exchange_class(self.exchange_type, self.tentacles_setup_config)
        if rest_exchange_class:
            self.exchange = rest_exchange_class(config=self.config,
                                                exchange_type=self.exchange_type,
                                                exchange_manager=self,
                                                is_sandboxed=self.is_sandboxed)

    """
    Spot exchange
    """

    async def _search_and_create_spot_exchange(self):
        spot_exchange_class = get_spot_exchange_class(self.exchange_type, self.tentacles_setup_config)
        if spot_exchange_class:
            self.exchange = spot_exchange_class(config=self.config,
                                                exchange_type=self.exchange_type,
                                                exchange_manager=self,
                                                is_sandboxed=self.is_sandboxed)

    """
    Margin exchange
    """

    async def _search_and_create_margin_exchange(self):
        margin_exchange_class = get_margin_exchange_class(self.exchange_type, self.tentacles_setup_config)
        if margin_exchange_class:
            self.exchange = margin_exchange_class(config=self.config,
                                                  exchange_type=self.exchange_type,
                                                  exchange_manager=self,
                                                  is_sandboxed=self.is_sandboxed)

    """
    Future exchange
    """

    async def _search_and_create_future_exchange(self):
        future_exchange_class = get_future_exchange_class(self.exchange_type, self.tentacles_setup_config)
        if future_exchange_class:
            self.exchange = future_exchange_class(config=self.config,
                                                  exchange_type=self.exchange_type,
                                                  exchange_manager=self,
                                                  is_sandboxed=self.is_sandboxed)

    """
    Exchange channels
    """

    async def _create_exchange_channels(self):  # TODO filter creation --> not required if pause is managed
        for exchange_channel_class_type in [ExchangeChannel, TimeFrameExchangeChannel]:
            await create_all_subclasses_channel(exchange_channel_class_type, set_chan, 
                                                is_synchronized=self.is_backtesting,
                                                exchange_manager=self)

    async def _create_exchange_producers(self):
        # Always init exchange user data first on real trading
        if self.exchange.is_authenticated \
                and self.trader and self.is_trading \
                and not (self.is_simulated or self.is_backtesting or self.is_collecting):
            await self._create_authenticated_producers()

        # Real data producers
        if not self.is_backtesting:
            for updater in UNAUTHENTICATED_UPDATER_PRODUCERS:
                if not self._is_managed_by_websocket(updater.CHANNEL_NAME):
                    await updater(get_chan(updater.CHANNEL_NAME, self.id)).run()

        # Simulated producers
        if (not self.exchange.is_authenticated or self.is_simulated or self.is_backtesting) \
                and self.trader and self.is_trading \
                and not self.is_collecting:
            for updater in AUTHENTICATED_UPDATER_SIMULATOR_PRODUCERS:
                await updater(get_chan(updater.CHANNEL_NAME, self.id)).run()

    async def _create_authenticated_producers(self):
        for updater in AUTHENTICATED_UPDATER_PRODUCERS:
            if self._is_managed_by_websocket(updater.CHANNEL_NAME):
                # websocket is handling this channel: initialize data if required
                if self._is_websocket_feed_requiring_init(updater.CHANNEL_NAME):
                    try:
                        updater(get_chan(updater.CHANNEL_NAME, self.id)).trigger_single_update()
                    except Exception as e:
                        self._logger.exception(e, True, f"Error when initializing data for {updater.CHANNEL_NAME} "
                                                        f"channel required by websocket: {e}")
            else:
                # no websocket for this channel: start an updater
                await updater(get_chan(updater.CHANNEL_NAME, self.id)).run()

    def requires_refresh_trigger(self, channel):
        """
        Return True if the given channel is to be updated artificially (ex: via channel updater). In this case it
        is necessary to trigger a manual update to get the exact picture at a given time (last updater push might
        have been a few seconds ago)
        Return False if this channels updates by itself and manual refresh trigger is not necessary (ex: websocket feed)
        :param channel: name of the channel
        :return: True if it should be refreshed via a manual trigger to be exactly up to date
        """
        return not self._is_managed_by_websocket(channel)

    """
    Websocket
    """

    def _is_managed_by_websocket(self, channel):  # TODO improve checker
        return not self.rest_only and self.has_websocket and \
               channel in WEBSOCKET_FEEDS_TO_TRADING_CHANNELS and \
               any([self.exchange_web_socket.is_feed_available(feed)
                    for feed in WEBSOCKET_FEEDS_TO_TRADING_CHANNELS[channel]])

    def _is_websocket_feed_requiring_init(self, channel):
        return any([self.exchange_web_socket.is_feed_requiring_init(feed)
                    for feed in WEBSOCKET_FEEDS_TO_TRADING_CHANNELS[channel]])

    async def _search_and_create_websocket(self):
        socket_manager = search_websocket_class(AbstractWebsocket, self.exchange_name, self.tentacles_setup_config)
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
        await self.exchange_web_socket.init_websocket(self.exchange_config.traded_time_frames,
                                                      self.exchange_config.traded_symbol_pairs,
                                                      self.tentacles_setup_config)

        await self.exchange_web_socket.start_sockets()

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

    def get_rest_pairs_refresh_threshold(self) -> RestExchangePairsRefreshMaxThresholds:
        traded_pairs_count = len(self.exchange_config.traded_symbol_pairs)
        if traded_pairs_count < RestExchangePairsRefreshMaxThresholds.FAST.value:
            return RestExchangePairsRefreshMaxThresholds.FAST
        if traded_pairs_count < RestExchangePairsRefreshMaxThresholds.MEDIUM.value:
            return RestExchangePairsRefreshMaxThresholds.MEDIUM
        return RestExchangePairsRefreshMaxThresholds.SLOW

    def _load_config_symbols_and_time_frames(self):
        client = self.exchange.client
        if client:
            self.client_symbols = client.symbols
            self.client_time_frames = list(client.timeframes) if hasattr(client, "timeframes") else []
        else:
            self._logger.error("Failed to load client from REST exchange")
            self._raise_exchange_load_error()

    def _initialize_simulator_time_frames(self):
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
                self.config[CONFIG_EXCHANGES][self.get_exchange_name()].get(CONFIG_EXCHANGE_KEY, ''),
                self.config[CONFIG_EXCHANGES][self.get_exchange_name()].get(CONFIG_EXCHANGE_SECRET, '')):
            logger.warning("Exchange configuration tokens are not set yet, to use OctoBot's real trader's features, "
                           "please enter your api tokens in exchange configuration")
            return False
        return True

    def get_exchange_credentials(self, logger, exchange_name):
        if self.ignore_config or not self.should_decrypt_token(logger) or self.without_auth:
            return "", "", ""
        config_exchange = self.config[CONFIG_EXCHANGES][exchange_name]
        return (decrypt_element_if_possible(CONFIG_EXCHANGE_KEY, config_exchange, None),
                decrypt_element_if_possible(CONFIG_EXCHANGE_SECRET, config_exchange, None),
                decrypt_element_if_possible(CONFIG_EXCHANGE_PASSWORD, config_exchange, None))

    @staticmethod
    def handle_token_error(error, logger):
        logger.error(f"Exchange configuration tokens are invalid : please check your configuration ! "
                     f"({error.__class__.__name__})")

    def get_symbol_data(self, symbol):
        return self.exchange_symbols_data.get_exchange_symbol_data(symbol)

    def __str__(self):
        exchange_type = 'rest'
        exchange_type = 'spot only' if self.is_spot_only else exchange_type
        exchange_type = 'margin' if self.is_margin else exchange_type
        exchange_type = 'future' if self.is_future else exchange_type
        return f"[{self.__class__.__name__}] with {self.exchange.__class__.__name__ if self.exchange else '?'} " \
               f"exchange class on {self.get_exchange_name()} | {exchange_type} | " \
               f"{'authenticated | ' if self.exchange and self.exchange.is_authenticated else 'unauthenticated | '}" \
               f"{'backtesting | ' if self.backtesting else ''}{'sandboxed | ' if self.is_sandboxed else ''}" \
               f"{'' if self.is_trading else 'not trading | '}" \
               f"{'websocket | ' if self.has_websocket else 'no websocket | '} id: {self.id}"
