# pylint: disable=E0611
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
import asyncio
import contextlib
import copy
import decimal
import logging

import ccxt.async_support as ccxt
import typing

import octobot_commons.constants
import octobot_commons.enums
import octobot_commons.symbols as commons_symbols

import octobot_trading
import octobot_trading.constants as constants
import octobot_trading.enums as enums
import octobot_trading.errors
import octobot_trading.exchanges as exchanges
import octobot_trading.exchanges.abstract_exchange as abstract_exchange
import octobot_trading.exchanges.config.ccxt_exchange_settings as ccxt_exchange_settings
import octobot_trading.personal_data as personal_data
from octobot_trading.enums import ExchangeConstantsOrderColumns as ecoc, OrderStatus
import octobot_trading.exchanges.parser as parser


class CCXTExchange(abstract_exchange.AbstractExchange):
    """
    CCXT library wrapper
    """
    CCXT_ISOLATED = "ISOLATED"
    CCXT_CROSSED = "CROSSED"

    def __init__(self, config, exchange_manager,
                 connector_config: ccxt_exchange_settings.CCXTExchangeConfig,
                 additional_ccxt_config=None,
                 ):
        super().__init__(config, exchange_manager)
        self.connector_config: ccxt_exchange_settings.CCXTExchangeConfig = connector_config
        self.orders_parser: parser.OrdersParser = connector_config.ORDERS_PARSER_CLASS
        self.trades_parser: parser.TradesParser = connector_config.TRADES_PARSER_CLASS
        self.positions_parser: parser.PositionsParser = connector_config.POSITIONS_PARSER_CLASS
        self.ticker_parser: parser.TickerParser = connector_config.TICKER_PARSER_CLASS
        self.market_status_parser: parser.ExchangeMarketStatusParser = connector_config.MARKET_STATUS_PARSER_CLASS

        self.CANDLE_LOADING_LIMIT_TO_TRY_IF_FAILED = 100

        self.client = None
        self.exchange_type = None
        self.all_currencies_price_ticker = None
        self.is_authenticated = False

        self.additional_ccxt_config = additional_ccxt_config
        self.headers = {}
        self.options = {}
        # add default options
        self.add_options(self.get_ccxt_client_login_options())

        self._create_exchange_type()
        self._create_client()

    async def initialize_impl(self):
        try:
            if self.exchange_manager.exchange.is_supporting_sandbox():
                self.set_sandbox_mode(self.exchange_manager.is_sandboxed)

            if self._should_authenticate() and not self.exchange_manager.exchange_only:
                await self._ensure_auth()

            if self.exchange_manager.is_loading_markets:
                with self.error_describer():
                    await self.client.load_markets()

            # initialize symbols and timeframes
            self.symbols = self.get_client_symbols()
            self.time_frames = self.get_client_time_frames()
        except (ccxt.ExchangeNotAvailable, ccxt.RequestTimeout) as e:
            raise octobot_trading.errors.UnreachableExchange() from e
        except ccxt.AuthenticationError:
            raise ccxt.AuthenticationError

    async def parse_order(self, raw_order: dict, order_type: str = None,
                          quantity: decimal.Decimal = None, price: decimal.Decimal = None,
                          status: str = None, symbol: str = None,
                          side: str = None, timestamp: int or float = None,
                          check_completeness: bool = True) -> dict:
        """
        use this method to parse a single order

        :param raw_order:

        optional:
        :param status: to use if it's missing in the order
        :param order_type: to use if it's missing in the order
        :param price: to use if it's missing in the order
        :param quantity: to use if it's missing in the order
        :param symbol: to use if it's missing in the order
        :param side: to use if it's missing in the order
        :param timestamp: to use if it's missing in the order

        :param check_completeness: if true checks all attributes, 
            if somethings missing it'll try to fetch it from the exchange

        :return: formatted order dict (100% complete or we raise NotImplemented)
        """
        parser = self.orders_parser(self.exchange_manager.exchange)
        return await parser.parse_order(raw_order, order_type=order_type, quantity=quantity,
                                        price=price, status=status, symbol=symbol, side=side,
                                        timestamp=timestamp, check_completeness=check_completeness)

    async def parse_orders(self, raw_orders: list, order_type: str = None,
                           quantity: decimal.Decimal = None, price: decimal.Decimal = None,
                           status: str = None, symbol: str = None,
                           side: str = None, timestamp: int or float = None,
                           check_completeness: bool = True) -> list:
        """
        use this method to format a list of order dicts

        :param raw_order: raw orders with eventually missing data

        optional:
        :param status: to use if it's missing in the order
        :param order_type: to use if it's missing in the order
        :param price: to use if it's missing in the order
        :param quantity: to use if it's missing in the order
        :param symbol: to use if it's missing in the order
        :param side: to use if it's missing in the order
        :param timestamp: to use if it's missing in the order

        :param check_completeness: if true checks all attributes, 
            if somethings missing it'll try to fetch it from the exchange

        :return: formatted orders list (100% complete or we raise NotImplemented report)
            
        """
        parser = self.orders_parser(self.exchange_manager.exchange)
        return await parser.parse_orders(raw_orders, order_type=order_type, quantity=quantity,
                                         price=price, status=status, symbol=symbol, side=side,
                                         timestamp=timestamp, check_completeness=check_completeness)

    async def parse_trade(self, raw_trade: dict, check_completeness: bool = True) -> dict:
        """
        use this method to parse a single trade

        :param raw_trade:

        optional:
        :param status: to use if it's missing in the trade
        :param trade_type: to use if it's missing in the trade
        :param price: to use if it's missing in the trade
        :param quantity: to use if it's missing in the trade
        :param symbol: to use if it's missing in the trade
        :param side: to use if it's missing in the trade
        :param timestamp: to use if it's missing in the trade

        :param check_completeness: if true checks all attributes, 
            if somethings missing it'll try to fetch it from the exchange

        :return: formatted trade dict (100% complete or we raise NotImplemented)
        """
        parser = self.trades_parser(self.exchange_manager.exchange)
        return await parser.parse_trade(raw_trade, check_completeness=check_completeness)

    async def parse_trades(self, raw_trades, check_completeness: bool = True) -> list:
        """
        use this method to format a list of trade dicts

        :param raw_trade: raw trades with eventually missing data

        optional:
        :param status: to use if it's missing in the trade
        :param trade_type: to use if it's missing in the trade
        :param price: to use if it's missing in the trade
        :param quantity: to use if it's missing in the trade
        :param symbol: to use if it's missing in the trade
        :param side: to use if it's missing in the trade
        :param timestamp: to use if it's missing in the trade

        :param check_completeness: if true checks all attributes, 
            if somethings missing it'll try to fetch it from the exchange

        :return: formatted trades list (100% complete or we raise NotImplemented report)
            
        """
        parser = self.trades_parser(self.exchange_manager.exchange)
        return await parser.parse_trades(raw_trades, check_completeness=check_completeness)

    async def parse_position(self, raw_position: dict) -> dict:
        """
        use this method to parse a single position

        :param raw_position:

        :param check_completeness: if true checks all attributes, 
            if somethings missing it'll try to fetch it from the exchange

        :return: formatted position dict (100% complete or we raise NotImplemented)
        """
        parser = self.positions_parser(self.exchange_manager.exchange)
        return await parser.parse_position(raw_position)

    async def parse_positions(self, raw_positions: list) -> list:
        """
        use this method to format a list of position dicts

        :param raw_position: raw positions with eventually missing data

        :param check_completeness: if true checks all attributes, 
            if somethings missing it'll try to fetch it from the exchange

        :return: formatted positions list (100% complete or we raise NotImplemented report)
            
        """
        parser = self.positions_parser(self.exchange_manager.exchange)
        return await parser.parse_positions(raw_positions)

    def parse_ticker(self, raw_ticker: dict, symbol) -> dict:
        return self.ticker_parser.parse_ticker(ticker=raw_ticker, exchange = self.exchange_manager.exchange, symbol=symbol)

    def parse_market_status(self, raw_market_status: dict, with_fixer: bool, price_example) -> dict:
        return self.market_status_parser(
            market_status=raw_market_status, with_fixer=with_fixer, price_example=price_example,
            fix_precision=self.connector_config.MARKET_STATUS_FIX_PRECISION,
            remove_invalid_price_limits=self.connector_config.MARKET_STATUS_REMOVE_INVALID_PRICE_LIMITS).market_status

    def get_client_symbols(self):
        return set(self.client.symbols) \
            if hasattr(self.client, "symbols") and self.client.symbols is not None else set()

    def get_client_time_frames(self):
        return set(self.client.timeframes) \
            if hasattr(self.client, "timeframes") and self.client.timeframes is not None else set()

    @classmethod
    def is_supporting_exchange(cls, exchange_candidate_name) -> bool:
        return isinstance(exchange_candidate_name, str)

    def _create_exchange_type(self):
        if self.is_supporting_exchange(self.exchange_manager.exchange_class_string):
            self.exchange_type = getattr(ccxt, self.exchange_manager.exchange_class_string)
        else:
            self.exchange_type = self.exchange_manager.exchange_class_string

    def get_ccxt_client_login_options(self):
        """
        :return: ccxt client login option dict, can be overwritten to custom exchange login
        """
        if self.exchange_manager.is_future:
            return {'defaultType': 'future'}
        if self.exchange_manager.is_margin:
            return {'defaultType': 'margin'}
        return {'defaultType': 'spot'}

    def add_headers(self, headers_dict):
        """
        Add new headers to ccxt client
        :param headers_dict: the additional header keys and values as dict
        """
        for header_key, header_value in headers_dict.items():
            self.headers[header_key] = header_value
            if self.client is not None:
                self.client.headers[header_key] = header_value

    def add_options(self, options_dict):
        """
        Add new options to ccxt client
        :param options_dict: the additional option keys and values as dict
        """
        for option_key, option_value in options_dict.items():
            self.options[option_key] = option_value
            if self.client is not None:
                self.client.options[option_key] = option_value

    async def _ensure_auth(self):
        try:
            await self.get_balance()
        except ccxt.AuthenticationError as e:
            await self.client.close()
            self._unauthenticated_exchange_fallback(e)
        except Exception as e:
            # Is probably handled in exchange tentacles, important thing here is that authentication worked
            self.logger.debug(f"Error when checking exchange connection: {e}. This should not be an issue.")

    def _create_client(self):
        """
        Exchange instance creation
        :return:
        """
        if not self.exchange_manager.exchange_only:
            # avoid logging version on temporary exchange_only exchanges
            self.logger.info(f"Creating {self.exchange_type.__name__} exchange with ccxt in version {ccxt.__version__}")
        if self.exchange_manager.ignore_config or self.exchange_manager.check_config(self.name):
            try:
                key, secret, password = self.exchange_manager.get_exchange_credentials(self.logger, self.name)
                if not (key and secret) and not self.exchange_manager.is_simulated:
                    self.logger.warning(f"No exchange API key set for {self.exchange_manager.exchange_name}. "
                                        f"Enter your account details to enable real trading on this exchange.")
                if self._should_authenticate():
                    self.client = self.exchange_type(self._get_client_config(key, secret, password))
                    self.is_authenticated = True
                    if self.exchange_manager.check_credentials:
                        self.client.checkRequiredCredentials()
                else:
                    self.client = self.exchange_type(self._get_client_config())
            except (ccxt.AuthenticationError, Exception) as e:
                self._unauthenticated_exchange_fallback(e)
        else:
            self.client = self._get_unauthenticated_exchange()
            self.logger.error("configuration issue: missing login information !")
        self.client.logger.setLevel(logging.INFO)
        self.use_http_proxy_if_necessary()

    def use_http_proxy_if_necessary(self):
        self.client.aiohttp_trust_env = constants.ENABLE_EXCHANGE_HTTP_PROXY_FROM_ENV

    def _should_authenticate(self):
        return not (self.exchange_manager.is_simulated or
                    self.exchange_manager.is_backtesting)

    def _unauthenticated_exchange_fallback(self, err):
        self.is_authenticated = False
        self.handle_token_error(err)
        self.client = self._get_unauthenticated_exchange()

    def _get_unauthenticated_exchange(self):
        return self.exchange_type(self._get_client_config())

    def _get_client_config(self, api_key=None, secret=None, password=None):
        config = {
            'verbose': constants.ENABLE_CCXT_VERBOSE,
            'enableRateLimit': constants.ENABLE_CCXT_RATE_LIMIT,
            'timeout': constants.DEFAULT_REQUEST_TIMEOUT,
            'options': self.options,
            'headers': self.headers
        }
        if api_key is not None:
            config['apiKey'] = api_key
        if secret is not None:
            config['secret'] = secret
        if password is not None:
            config['password'] = password
        # apply self.additional_ccxt_config
        config.update(self.additional_ccxt_config or {})
        return config

    def get_market_status(self, symbol, price_example=None, with_fixer=True,) -> dict:
        try:
            return self.parse_market_status(
                raw_market_status=self.client.market(symbol), with_fixer=with_fixer, price_example=price_example)
        except ccxt.NotSupported:
            raise octobot_trading.errors.NotSupported

    async def get_balance(self, **kwargs: dict):
        """
        fetch balance (free + used) by currency
        :return: balance dict
        """
        if not kwargs:
            kwargs = {}
        try:
            with self.error_describer():
                balance = await self.client.fetch_balance(params=kwargs)

                # remove not currency specific keys
                balance.pop(constants.CONFIG_PORTFOLIO_FREE, None)
                balance.pop(constants.CONFIG_PORTFOLIO_USED, None)
                balance.pop(constants.CONFIG_PORTFOLIO_TOTAL, None)
                balance.pop(constants.CCXT_INFO, None)
                balance.pop(enums.ExchangeConstantsCCXTColumns.DATETIME.value, None)
                balance.pop(enums.ExchangeConstantsCCXTColumns.TIMESTAMP.value, None)
                return personal_data.parse_decimal_portfolio(balance)

        except ccxt.InvalidNonce as err:
            exchanges.log_time_sync_error(self.logger, self.name, err, "real trader portfolio")
            raise err
        except ccxt.NotSupported:
            raise octobot_trading.errors.NotSupported

    async def get_symbol_prices(self,
                                symbol: str,
                                time_frame: octobot_commons.enums.TimeFrames,
                                limit: int = None,
                                since: int = None,
                                **kwargs: dict) -> typing.Optional[list]:
        try:
            with self.error_describer():
                if limit := self.cut_candle_limit(limit):
                    return await self.client.fetch_ohlcv(symbol, time_frame.value, limit=limit,
                                                         since=since, params=kwargs)
                return await self.client.fetch_ohlcv(symbol, time_frame.value, since=since, params=kwargs)
        except ccxt.NotSupported:
            if limit:
                raise octobot_trading.errors.NotSupported
        except ccxt.BaseError as e:
            if limit:
                raise octobot_trading.errors.FailedRequest(
                    f"Failed to get_symbol_prices: {e.__class__.__name__} on {e}")
        except Exception as e:
            if limit:
                raise octobot_trading.errors.FailedRequest(
                    f"Failed to get_symbol_prices: Unknown error on {symbol}/{time_frame} {e}")
        # try again with a limit
        return await self.get_symbol_prices(symbol=symbol, time_frame=time_frame, since=since,
                                            limit=self.CANDLE_LOADING_LIMIT_TO_TRY_IF_FAILED, **kwargs)

    def cut_candle_limit(self, limit) -> typing.Optional[int]:
        if self.connector_config.CANDLE_LOADING_LIMIT:
            limit = min(limit, self.connector_config.CANDLE_LOADING_LIMIT)
        return limit

    async def get_kline_price(self,
                              symbol: str,
                              time_frame: octobot_commons.enums.TimeFrames,
                              **kwargs: dict) -> typing.Optional[list]:
        try:
            # default implementation
            return await self.get_symbol_prices(symbol, time_frame, limit=1, **kwargs)
        except ccxt.NotSupported:
            raise octobot_trading.errors.NotSupported
        except ccxt.BaseError as e:
            raise octobot_trading.errors.FailedRequest(f"Failed to get_kline_price {e}")

    # return up to ten bidasks on each side of the order book stack
    async def get_order_book(self, symbol: str, limit: int = 5, **kwargs: dict) -> typing.Optional[dict]:
        try:
            with self.error_describer():
                return await self.client.fetch_order_book(symbol, limit=limit, params=kwargs)
        except ccxt.NotSupported:
            raise octobot_trading.errors.NotSupported
        except ccxt.BaseError as e:
            raise octobot_trading.errors.FailedRequest(f"Failed to get_order_book {e}")

    async def get_recent_trades(self, symbol: str, limit: int = 100, check_completeness: bool = True, **kwargs: dict) -> typing.Optional[list]:
        try:
            with self.error_describer():
                return await self.parse_trades(
                    await self.client.fetchTrades(symbol, limit=limit, params=kwargs), check_completeness=check_completeness)
        except ccxt.NotSupported:
            raise octobot_trading.errors.NotSupported
        except ccxt.BaseError as e:
            raise octobot_trading.errors.FailedRequest(f"Failed to get_recent_trades {e}")

    # A price ticker contains statistics for a particular market/symbol for some period of time in recent past (24h)
    async def get_price_ticker(self, symbol: str, **kwargs: dict) -> dict:
        try:
            with self.error_describer():
                ticker = await self.client.fetch_ticker(symbol, params=kwargs)
                return self.parse_ticker(raw_ticker=ticker, symbol=symbol)
        except ccxt.NotSupported:
            raise octobot_trading.errors.NotSupported
        except ccxt.BaseError as e:
            raise octobot_trading.errors.FailedRequest(f"Failed to get_price_ticker {e}")
        except Exception as e:
            raise octobot_trading.errors.FailedRequest(f"Failed to get_price_ticker {e}")

    async def get_all_currencies_price_ticker(self, **kwargs: dict) -> typing.Optional[list]:
        try:
            with self.error_describer():
                symbols = kwargs.pop("symbols", None)
                self.all_currencies_price_ticker = await self.client.fetch_tickers(symbols, params=kwargs)
            return self.all_currencies_price_ticker
        except ccxt.NotSupported:
            raise octobot_trading.errors.NotSupported
        except ccxt.BaseError as e:
            raise octobot_trading.errors.FailedRequest(f"Failed to get_all_currencies_price_ticker {e}")

    async def get_order(self, order_id: str, symbol: str = None, check_completeness: bool = True,
                        **kwargs: dict) -> typing.Optional[dict]:
        defined_methods = self.connector_config.GET_ORDER_METHODS
        if enums.CCXTExchangeConfigMethods.GET_ORDER_DEFAULT.value in defined_methods and\
                (order := await self.get_order_default(order_id, symbol,
                                                       check_completeness=check_completeness, **kwargs)):
            return order
        if enums.CCXTExchangeConfigMethods.GET_ORDER_FROM_OPEN_AND_CLOSED_ORDERS.value in defined_methods and \
                (order := await self.get_order_from_open_and_closed_orders(order_id, symbol,
                                                                           check_completeness=check_completeness,
                                                                           **kwargs)):
            return order
        if enums.CCXTExchangeConfigMethods.GET_ORDER_USING_STOP_ID.value in defined_methods and \
                (order := await self.get_order_using_stop_id(order_id, symbol, check_completeness=check_completeness)):
            return order
        if enums.CCXTExchangeConfigMethods.GET_ORDER_FROM_TRADES.value in defined_methods and \
                (order := await self.get_trade(order_id, symbol, check_completeness=check_completeness)):
            return order
        self.logger.debug(f"Order not found using get_order: {order_id} / {symbol} - order might not exist anymore")

    async def get_order_default(self, order_id: str, symbol: str = None, check_completeness: bool = True,
                                **kwargs: dict) -> typing.Optional[dict]:
        if self.client.has.get('fetchOrder'):
            try:
                with self.error_describer():
                    params = kwargs.pop("params", {})
                    return await self.parse_order(
                        await self.client.fetch_order(order_id, symbol, params=params, **kwargs),
                        check_completeness=check_completeness, )
            except ccxt.OrderNotFound:
                # some exchanges are throwing this error when an order is cancelled (ex: coinbase pro)
                pass
            except ccxt.NotSupported as e:
                self.logger.exception(e, True, "Failed to fetch closed orders using get_order_default: Not Supported")
            except Exception as e:
                self.logger.exception(e, True, "Failed to fetch closed orders using get_order_default")
        return None

    async def get_order_using_stop_id(self, order_id: str, symbol: str = None, check_completeness: bool = True,
                                      **kwargs: dict) -> typing.Optional[dict]:
        if self.client.has.get('fetchOrder'):
            try:
                with self.error_describer():
                    params = kwargs.pop("params", {})
                    params["stop_order_id"] = order_id
                    return await self.parse_order(
                        await self.client.fetch_order(order_id, symbol, params=params, **kwargs),
                        check_completeness=check_completeness, )
            except ccxt.OrderNotFound:
                # some exchanges are throwing this error when an order is cancelled
                pass
            except Exception as e:
                self.logger.exception(e, True, "Failed to get order using get_order_using_stop_id")
        return None

    async def get_order_using_get_orders(self, order_id: str, symbol: str = None, check_completeness: bool = True,
                                         **kwargs: dict
                                         ) -> typing.Optional[dict]:
        try:
            open_orders = await self.get_open_orders(symbol=symbol, check_completeness=check_completeness, )
            for order in open_orders:
                if order.get(ecoc.ID.value, None) == order_id:
                    return order
        except Exception as e:
            self.logger.exception(e, True, "Failed to get order using get_order_using_get_orders")
        return None

    async def get_order_from_open_and_closed_orders(self, order_id: str, symbol: str = None,
                                                    check_completeness: bool = True, **kwargs: dict
                                                    ) -> typing.Optional[dict]:
        for order in await self.get_open_orders(symbol, check_completeness=check_completeness, **kwargs):
            if order[ecoc.ID.value] == order_id:
                return order
        for order in await self.get_closed_orders(symbol, check_completeness=check_completeness, **kwargs):
            if order[ecoc.ID.value] == order_id:
                return order
        return None  # OrderNotFound

    async def get_all_orders(self, symbol: str = None, since: int = None, limit: int = None,
                             check_completeness: bool = True, **kwargs: dict) -> list:
        limit = self.cut_order_pagination_limit(limit)
        defined_methods = self.connector_config.GET_ALL_ORDERS_METHODS
        orders = []
        if enums.CCXTExchangeConfigMethods.GET_ALL_ORDERS_DEFAULT.value in defined_methods:
            orders += await self.get_all_orders_default(symbol=symbol, since=since, limit=limit, 
                                                check_completeness=check_completeness, kwargs=kwargs)
        if enums.CCXTExchangeConfigMethods.GET_ALL_STOP_ORDERS_USING_STOP_LOSS_ENDPOINT.value in defined_methods:
            orders += await self.get_all_stop_orders_using_stop_loss_endpoint(symbol=symbol, since=since, limit=limit, 
                                                check_completeness=check_completeness, kwargs=kwargs)
        return orders

    async def get_all_orders_default(self, symbol: str = None, since: int = None, limit: int = None,
                                     check_completeness: bool = True, **kwargs: dict) -> list:
        if self.client.has.get('fetchOrders'):
            with self.error_describer():
                return await self.parse_orders(
                    await self.client.fetch_orders(symbol=symbol, since=since,
                                                   limit=limit, params=kwargs),
                    check_completeness=check_completeness, )
        else:
            raise octobot_trading.errors.NotSupported("This exchange doesn't support fetchOrders")
        
    async def get_all_stop_orders_using_stop_loss_endpoint(self, symbol: str = None, since: int = None,
                                                            limit: int = None, check_completeness: bool = True,
                                                            **kwargs: dict) -> list:
        try:
            if "stop" not in kwargs:
                # only fetch untriggered stop orders
                kwargs["stop"] = True
                return await self.get_all_orders_default(symbol=symbol, since=since, limit=limit,
                                                          check_completeness=check_completeness, **kwargs)
            return []
        except Exception as e:
            self.logger.exception(e, True, "Failed to fetch all stop orders using"
                                  " get_all_stop_order_using_stop_loss_endpoint")
            return []

    async def get_open_orders(self, symbol: str = None, since: int = None, limit: int = None,
                              check_completeness: bool = True, **kwargs: dict) -> list:
        """
            all known get_closed_orders methods should be added here so untested exchanges have higher chance of success
        """
        limit = self.cut_order_pagination_limit(limit)
        defined_methods = self.connector_config.GET_OPEN_ORDERS_METHODS
        orders = []
        if enums.CCXTExchangeConfigMethods.GET_OPEN_ORDERS_DEFAULT.value in defined_methods:
            orders += await self.get_open_orders_default(symbol, since, limit, check_completeness=check_completeness,
                                                        **kwargs)
        if enums.CCXTExchangeConfigMethods.GET_OPEN_STOP_ORDERS_USING_STOP_LOSS_ENDPOINT.value in defined_methods:
            orders += await self.get_open_stop_orders_using_stop_loss_endpoint(symbol, since, limit,
                                                                               check_completeness=check_completeness,
                                                                               **kwargs)
        return orders

    async def get_open_orders_default(self, symbol: str = None, since: int = None, limit: int = None,
                                      check_completeness: bool = True, **kwargs: dict) -> list:
        if self.client.has.get('fetchOpenOrders'):
            with self.error_describer():
                return await self.parse_orders(
                    await self.client.fetch_open_orders(symbol=symbol, since=since, limit=limit, params=kwargs),
                    check_completeness=check_completeness)
        else:
            raise octobot_trading.errors.NotSupported("This exchange doesn't support fetchOpenOrders")

    async def get_open_stop_orders_using_stop_loss_endpoint(self, symbol: str = None, since: int = None,
                                                            limit: int = None, check_completeness: bool = True,
                                                            **kwargs: dict) -> list:
        try:
            if "stop" not in kwargs:
                # only fetch untriggered stop orders
                kwargs["stop"] = True
                return await self.get_open_orders_default(symbol=symbol, since=since, limit=limit,
                                                          check_completeness=check_completeness, **kwargs)
            return []
        except Exception as e:
            self.logger.exception(e, True, "Failed to fetch open stop orders using"
                                  " get_open_stop_order_using_stop_loss_endpoint")
            return []

    async def get_closed_orders(self, symbol: str = None, since: int = None, limit: int = None,
                                check_completeness: bool = True, **kwargs: dict) -> list:
        """
            all known get_closed_orders methods should be added here so untested exchanges have higher chance of success
        """
        limit = self.cut_order_pagination_limit(limit)
        defined_methods = self.connector_config.GET_CLOSED_ORDERS_METHODS
        orders = []
        if enums.CCXTExchangeConfigMethods.GET_CLOSED_ORDERS_DEFAULT.value in defined_methods:
            orders += await self.get_closed_orders_default(symbol, since, limit, check_completeness=check_completeness,
                                                       **kwargs)
        if enums.CCXTExchangeConfigMethods.GET_CLOSED_STOP_ORDERS_USING_STOP_LOSS_ENDPOINT.value in defined_methods:
            orders += await self.get_closed_stop_orders_using_stop_loss_endpoint(symbol, since, limit,
                                                                                 check_completeness=check_completeness,
                                                                                 **kwargs)
        return orders

    async def get_closed_orders_default(self, symbol: str = None, since: int = None, limit: int = None,
                                        check_completeness: bool = True, **kwargs: dict) -> list:
        if self.client.has.get('fetchClosedOrders'):
            with self.error_describer():
                return await self.parse_orders(
                    await self.client.fetch_closed_orders(symbol=symbol, since=since, limit=limit, params=kwargs),
                    check_completeness=check_completeness)
        else:
            raise octobot_trading.errors.NotSupported("This exchange doesn't support fetchClosedOrders")

    async def get_closed_stop_orders_using_stop_loss_endpoint(self, symbol, since, limit,
                                                              check_completeness: bool = True, **kwargs) -> list:
        if "stop" not in kwargs:
            # only fetch untriggered stop orders
            kwargs["stop"] = True
            try:
                return await self.get_closed_orders_default(symbol=symbol, since=since, limit=limit,
                                                            check_completeness=check_completeness, **kwargs)
            except ccxt.AuthenticationError as e:
                self.logger.debug(f"(known issue) Fail to fetching closed stop orders : {e}")
            except Exception as e:
                self.logger.exception(e, True, "Failed to fetch closed stop orders using"
                                      " get_open_stop_order_using_stop_loss_endpoint")
        return []

    def cut_order_pagination_limit(self, limit: int) -> typing.Optional[int]:
        if self.connector_config.MAX_ORDER_PAGINATION_LIMIT:
            return min(self.connector_config.MAX_ORDER_PAGINATION_LIMIT, limit)
        else:
            return limit

    async def get_my_recent_trades(self, symbol: str = None, since: int = None,
                                   limit: int = None, check_completeness: bool = True, **kwargs: dict) -> list:
        """
            all known get_my_recent_trades methods should be added here
        """
        limit = self.cut_recent_trades_pagination_limit(limit)
        defined_methods = self.connector_config.GET_MY_RECENT_TRADES_METHODS
        error_messages = ""
        if enums.CCXTExchangeConfigMethods.GET_MY_RECENT_TRADES_DEFAULT.value in defined_methods:
            fetched_trades, error_message  = await self.get_my_recent_trades_default(
                symbol=symbol, since=since, limit=limit, check_completeness=check_completeness, kwargs=kwargs)
            if fetched_trades:
                return fetched_trades
            elif error_message:
                error_messages += error_message
        if enums.CCXTExchangeConfigMethods.GET_MY_RECENT_TRADES_USING_RECENT_TRADES.value in defined_methods:
            fetched_trades, error_message  = await self.get_my_recent_trades_using_recent_trades(
                symbol=symbol, since=since, limit=limit, check_completeness=check_completeness, kwargs=kwargs)
            if fetched_trades:
                return fetched_trades
            elif error_message:
                error_messages += error_message
        if enums.CCXTExchangeConfigMethods.GET_MY_RECENT_TRADES_USING_CLOSED_ORDERS.value in defined_methods:
            fetched_trades, error_message  = await self.get_my_recent_trades_using_closed_orders(
                symbol=symbol, since=since, limit=limit, check_completeness=check_completeness, kwargs=kwargs)
            if fetched_trades:
                return fetched_trades
            elif error_message:
                error_messages += error_message
        if error_messages != "":
            raise octobot_trading.errors.NotSupported("This exchange doesn't support fetching trade history.\n"
                                                      f"Errors: {error_messages}")
        self.logger.warning("No trades found when fetching my recent trades. This is only normal if this account didn't trade yet")
        return []

    async def get_my_recent_trades_default(self, symbol: str = None, since: int = None, limit: int = None,
                                           check_completeness: bool = True,
                                           **kwargs: dict) -> typing.Tuple[list or None, str or None]:
        try:
            if self.client.has.get('fetchMyTrades'):
                return await self.parse_trades(
                    await self.client.fetchMyTrades(symbol=symbol, since=since, limit=limit, params=kwargs),
                    check_completeness=check_completeness), None
            else:
                return None, f"Failed to fetch recent trades using get_my_recent_trades_default - " \
                    "error: Exchange doesn't have a fetchMyTrades method\n"
        except Exception as e:
            return None, f"Failed to fetch recent trades using get_my_recent_trades_default - error: {e}"

    async def get_my_recent_trades_using_recent_trades(self, symbol: str = None, since: int = None,
                                                   limit: int = None, check_completeness: bool = True,
                                                   **kwargs: dict) -> typing.Tuple[list or None, str or None]:
        try:
            return await self.get_recent_trades(symbol, limit, check_completeness, **kwargs), None
        except Exception as e:
            return None, f"Failed to fetch recent trades using get_my_recent_trades_using_recent_trades - error: {e}"
        
    async def get_my_recent_trades_using_closed_orders(self, symbol: str = None, since: int = None,
                                                       limit: int = None, check_completeness: bool = True,
                                                       **kwargs: dict) -> typing.Tuple[list or None, str or None]:
        try:
            closed_orders = await self.get_closed_orders(symbol=symbol, since=since, limit=limit,
                                                         check_completeness=check_completeness, **kwargs)
            trades = []
            for order in closed_orders:
                if order[ecoc.STATUS.value] == OrderStatus.FILLED.value or order[ecoc.STATUS.value] == OrderStatus.CLOSED.value:
                    trades.append(order)
            return trades, None
        except Exception as e:
            return None, f"Failed to fetch recent trades using get_my_recent_trades_using_closed_orders: {e}"

    def cut_recent_trades_pagination_limit(self, limit: int) -> typing.Union[int, None]:
        if self.connector_config.MAX_RECENT_TRADES_PAGINATION_LIMIT:
            return min(self.connector_config.MAX_RECENT_TRADES_PAGINATION_LIMIT, limit)
        else:
            return limit

    async def get_trade(self, trade_id, symbol, check_completeness=True) -> typing.Union[None, dict]:
        trades = await self.get_my_recent_trades(symbol, check_completeness=check_completeness)
        # usually the right trade is within the last ones
        for trade in trades[::-1]:
            if trade[ecoc.ID.value] == trade_id:
                return trade
        return None  # TradeNotFound
    
    async def cancel_order(self, order_id: str, symbol: str = None, **kwargs: dict) -> bool:
        defined_methods = self.connector_config.CANCEL_ORDERS_METHODS
        messages = ""
        if enums.CCXTExchangeConfigMethods.CANCEL_ORDER_DEFAULT.value in defined_methods:
            success, error_message = await self.cancel_order_default(order_id, symbol=symbol, **kwargs)
            if success:                    
                return True
            else:
                messages = error_message or messages
        if enums.CCXTExchangeConfigMethods.CANCEL_ORDER_DEFAULT.value in defined_methods:
            success, await self.cancel_stop_order_using_stop_loss_endpoint(order_id, symbol=symbol, **kwargs)
            if success:                    
                return True
            else:
                messages = error_message + messages if error_message else messages
        if messages != "":
            raise octobot_trading.errors.NotSupported(messages)
        self.logger.warning(f"Failed to cancel order {symbol} {order_id} - order was not found")
        return False # order not found

    async def cancel_order_default(self, order_id: str, symbol: str = None, **kwargs: dict) -> bool:
        success = False
        cancel_resp_message = None
        try:
            cancel_resp = None
            with self.error_describer():
                cancel_resp = await self.client.cancel_order(order_id, symbol=symbol, params=kwargs)
            cancel_resp_message = f" - Cancel response: {cancel_resp or 'no response'}"
            is_canceled, _ =  await self.check_if_canceled(order_id, symbol)
            if is_canceled:
                return
            await asyncio.sleep(20) # try again - some exchanges need a while to update the order (bybit for example)
            return await self.check_if_canceled(order_id, symbol, cancel_resp_message)
        except ccxt.OrderNotFound:
            return success, f"Trying to cancel order (id {order_id}) with cancel_order_default but order was not found{cancel_resp_message or ''}\n"
        except (ccxt.NotSupported, octobot_trading.errors.NotSupported) as e:
            return success, f"cancel_order_default is not supported. Error: {e}{cancel_resp_message or ''}\n"
        except Exception as e:
            return success, f"Order {order_id} failed to cancel using  | {e} ({e.__class__.__name__}){cancel_resp_message or ''}\n"
    
    async def check_if_canceled(self, order_id, symbol, cancel_resp_message=""):
        success = False
        try:
            # check if canceled
            cancelled_order = await self.get_order(order_id, symbol=symbol)
            if cancelled_order:
                if personal_data.parse_is_cancelled(cancelled_order):
                    success = True
                    return success, None
                else:
                    return success, f"Error canceling order (id {order_id}), the order is still uncanceled{cancel_resp_message}"
            else:
                # Order is not found: it has successfully been cancelled 
                # (some exchanges don't allow to get a cancelled order).
                success = True
                return success, None
        except ccxt.OrderNotFound:
            # Order is not found: it has successfully been cancelled 
            # (some exchanges don't allow to get a cancelled order).
            success = True
            return success, None

    async def cancel_stop_order_using_stop_loss_endpoint(self, order_id: str, symbol: str = None, **kwargs: dict) -> bool:
        # some exchange have an extra stop/take profit endpoint
        # from bybit docs: You may cancel all untriggered conditional orders or take profit/stop loss order.
        # Essentially, after a conditional order is triggered, it will become an active order. So, when a conditional
        # order is triggered, cancellation has to be done through the active order endpoint for any unfilled or
        # partially filled active order
        kwargs["stop_order_id"] = order_id
        return await self.cancel_order_default(order_id, symbol=symbol, kwargs=kwargs)

    async def get_positions(self, **kwargs: dict) -> list:
        """
            all known get_positions methods should be added here
            so untested exchanges have higher chance of success
        """
        defined_methods = self.connector_config.GET_POSITION_METHODS
        positions = []
        if enums.CCXTExchangeConfigMethods.GET_POSITION_DEFAULT.value in defined_methods:
            positions += await self.get_position_default(**kwargs)
        if enums.CCXTExchangeConfigMethods.GET_POSITION_BY_SUB_TYPE.value in defined_methods:
            positions += await self.get_position_by_sub_type(**kwargs)
        if enums.CCXTExchangeConfigMethods.GET_POSITION_WITH_PRIVATE_GET_POSITION_RISK.value in defined_methods:
            positions += await self.get_position_with_private_get_position_risk()
        return positions

    async def get_position_default(self, **kwargs: dict) -> list:
        try:
            return await self.parse_positions(await self.client.fetch_positions(params=kwargs))
        except Exception as e:
            self.logger.debug(f"Failed to load positions using get_position_default ({e})")
            return []

    async def get_position_with_private_get_position_risk(self) -> list:
        try:
            if self.client.has.get("fapiPrivate_get_positionrisk"):
                return self.parse_positions(await self.client.fapiPrivate_get_positionrisk())                
        except Exception as e:
            self.logger.debug(f"Failed to load positions using private_get_position_risk ({e})")
        return []

    async def get_position_by_sub_type(self, **kwargs: dict) -> list:
        params = {**kwargs}
        positions = []
        POSITION_TYPES = ("linear", "inverse")
        for position_type in POSITION_TYPES:
            try:
                params["subType"] = position_type
                positions += await self.get_position_default(**params)
            except Exception as e:
                self.logger.info(f"Failed to load positions using: "
                                 f"get_position_by_sub_type - {position_type} positions: ({e})")
        return positions

    async def get_position(self, symbol: str, **kwargs: dict) -> dict:
        return await self.client.fetch_position(symbol=symbol, params=kwargs)

    async def get_funding_rate(self, symbol: str, **kwargs: dict) -> dict:
        try:
            if funding_rate := await self.client.fetch_funding_rate(symbol=symbol, params=kwargs):
                return funding_rate
        except Exception as e:
            self.logger.exception(
                e, True, "Failed to get funding rate - OctoBot is trying to use get_funding_rate_history instead ")
            # continue on every error as there is another way
        return (await self.get_funding_rate_history(symbol=symbol, limit=1))[-1]

    async def get_funding_rate_history(self, symbol: str, limit: int = 1, **kwargs: dict) -> list:
        return await self.client.fetch_funding_rate_history(symbol=symbol, limit=limit, params=kwargs)

    async def set_symbol_leverage(self, symbol: str, leverage: int, **kwargs: dict):
        return await self.client.set_leverage(leverage=int(leverage), symbol=symbol, params=kwargs)

    async def set_symbol_margin_type(self, symbol: str, isolated: bool):
        return await self.client.set_margin_mode(symbol=symbol,
                                                 marginType=self.CCXT_ISOLATED if isolated else self.CCXT_CROSSED)

    async def set_symbol_position_mode(self, symbol: str, one_way: bool):
        return await self.client.set_position_mode(self, hedged=not one_way, symbol=symbol)

    async def set_symbol_partial_take_profit_stop_loss(self, symbol: str, inverse: bool,
                                                       tp_sl_mode: enums.TakeProfitStopLossMode):
        raise NotImplementedError("set_symbol_partial_take_profit_stop_loss is not implemented")

    def get_bundled_order_parameters(self, stop_loss_price=None, take_profit_price=None) -> dict:
        return self.connector.get_bundled_order_parameters(stop_loss_price=stop_loss_price,
                                                           take_profit_price=take_profit_price)

    @staticmethod
    def get_ccxt_order_type(order_type: enums.TraderOrderType):
        if order_type in (enums.TraderOrderType.BUY_LIMIT, enums.TraderOrderType.SELL_LIMIT,
                          enums.TraderOrderType.STOP_LOSS_LIMIT, enums.TraderOrderType.TAKE_PROFIT_LIMIT,
                          enums.TraderOrderType.TRAILING_STOP_LIMIT):
            return enums.TradeOrderType.LIMIT.value
        if order_type in (enums.TraderOrderType.BUY_MARKET, enums.TraderOrderType.SELL_MARKET,
                          enums.TraderOrderType.STOP_LOSS, enums.TraderOrderType.TAKE_PROFIT,
                          enums.TraderOrderType.TRAILING_STOP):
            return enums.TradeOrderType.MARKET.value
        raise RuntimeError(f"Unknown order type: {order_type}")

    def get_trade_fee(self, symbol, order_type, quantity, price, taker_or_maker):
        fees = self.client.calculate_fee(symbol=symbol,
                                         type=order_type,
                                         side=exchanges.get_order_side(order_type),
                                         amount=float(quantity),
                                         price=float(price),
                                         takerOrMaker=taker_or_maker)
        fees[enums.FeePropertyColumns.COST.value] = decimal.Decimal(str(fees[enums.FeePropertyColumns.COST.value]))
        if self.exchange_manager.is_future:
            # fees on futures are wrong
            rate = fees[enums.FeePropertyColumns.RATE.value]
            # avoid using ccxt computed fees as they are often wrong
            # see https://docs.ccxt.com/en/latest/manual.html#trading-fees
            parsed_symbol = commons_symbols.parse_symbol(symbol)
            if self.exchange_manager.exchange.get_pair_future_contract(symbol).is_inverse_contract():
                fees[enums.FeePropertyColumns.COST.value] = decimal.Decimal(str(rate)) * quantity
                fees[enums.FeePropertyColumns.CURRENCY.value] = parsed_symbol.base
            else:
                fees[enums.FeePropertyColumns.COST.value] = decimal.Decimal(str(rate)) * quantity * price
                fees[enums.FeePropertyColumns.CURRENCY.value] = parsed_symbol.quote
        return fees

    def get_fees(self, symbol):
        try:
            market_status = self.client.market(symbol)
            return {
                enums.ExchangeConstantsMarketPropertyColumns.TAKER.value:
                    market_status.get(enums.ExchangeConstantsMarketPropertyColumns.TAKER.value,
                                      constants.CONFIG_DEFAULT_FEES),
                enums.ExchangeConstantsMarketPropertyColumns.MAKER.value:
                    market_status.get(enums.ExchangeConstantsMarketPropertyColumns.MAKER.value,
                                      constants.CONFIG_DEFAULT_FEES),
                enums.ExchangeConstantsMarketPropertyColumns.FEE.value:
                    market_status.get(enums.ExchangeConstantsMarketPropertyColumns.FEE.value,
                                      constants.CONFIG_DEFAULT_FEES)
            }
        except ccxt.NotSupported:
            raise octobot_trading.errors.NotSupported
        except Exception as e:
            self.logger.exception(e, True, f"Fees data for {symbol} was not found")
            return {
                enums.ExchangeConstantsMarketPropertyColumns.TAKER.value: constants.CONFIG_DEFAULT_FEES,
                enums.ExchangeConstantsMarketPropertyColumns.MAKER.value: constants.CONFIG_DEFAULT_FEES,
                enums.ExchangeConstantsMarketPropertyColumns.FEE.value: constants.CONFIG_DEFAULT_FEES
            }

    def get_uniform_timestamp(self, timestamp):
        return timestamp / octobot_commons.constants.MSECONDS_TO_SECONDS

    def get_exchange_current_time(self):
        return self.get_uniform_timestamp(self.client.milliseconds())

    async def stop(self) -> None:
        self.logger.info(f"Closing connection.")
        await self.client.close()
        self.logger.info(f"Connection closed.")
        self.exchange_manager = None

    def get_pair_from_exchange(self, pair) -> typing.Optional[str]:
        try:
            return self.client.market(pair)["symbol"]
        except ccxt.BadSymbol:
            try:
                return self.client.markets_by_id[pair]["symbol"]
            except KeyError:
                self.logger.error(f"Failed to get market of {pair}")
        return None

    def get_split_pair_from_exchange(self, pair) -> typing.Tuple[str, str]:
        try:
            market_data: dict = self.client.market(pair)
            return market_data["base"], market_data["quote"]
        except ccxt.BadSymbol:
            try:
                return self.client.markets_by_id[pair]["base"], self.client.markets_by_id[pair]["quote"]
            except KeyError:
                self.logger.error(f"Failed to get market of {pair}")
                return None, None

    def get_exchange_pair(self, pair) -> str:
        if pair in self.client.symbols:
            try:
                return self.client.market(pair)["id"]
            except KeyError:
                pass
        raise ValueError(f'{pair} is not supported')

    def get_pair_cryptocurrency(self, pair) -> str:
        if pair in self.client.symbols:
            try:
                return self.client.market(pair)["base"]
            except KeyError:
                pass
        raise ValueError(f'{pair} is not supported')

    def get_default_balance(self):
        return self.client.account()

    def get_rate_limit(self):
        return self.exchange_type.rateLimit / 1000

    def set_sandbox_mode(self, is_sandboxed):
        try:
            self.client.setSandboxMode(is_sandboxed)
        except ccxt.NotSupported as e:
            default_type = self.client.options.get('defaultType', None)
            additional_info = f" in type {default_type}" if default_type else ""
            self.logger.warning(f"{self.name} does not support sandboxing {additional_info}: {e}")
            # raise exception to stop this exchange and prevent dealing with a real funds exchange
            raise e

    """
    Parsers
    """

    def parse_balance(self, balance):
        return self.client.parse_balance(balance)

    def parse_ohlcv(self, ohlcv):
        return self.uniformize_candles_if_necessary(self.client.parse_ohlcv(ohlcv))

    def parse_order_book(self, order_book):
        return self.client.parse_order_book(order_book)

    def parse_order_book_ticker(self, order_book_ticker):
        return order_book_ticker

    def parse_timestamp(self, data_dict, timestamp_key, default_value=None, ms=False):
        parsed_timestamp = self.client.parse8601(self.client.safe_string(data_dict, timestamp_key))
        return (parsed_timestamp if ms else parsed_timestamp * 10 ** -3) if parsed_timestamp else default_value

    def parse_currency(self, currency):
        return self.client.safe_currency_code(currency)

    def parse_account(self, account):
        return enums.AccountTypes[account.lower()]

    def get_max_handled_pair_with_time_frame(self) -> int:
        """
        Override when necessary
        :return: the maximum number of simultaneous pairs * time_frame that this exchange can handle.
        """
        # 15 pairs, each on 3 time frames
        return 45

    @contextlib.contextmanager
    def error_describer(self):
        try:
            yield
        except ccxt.DDoSProtection as e:
            # raised upon rate limit issues, last response data might have details on what is happening
            if self.exchange_manager.exchange.should_log_on_ddos_exception(e):
                self.logger.error(
                    f"DDoSProtection triggered [{e} ({e.__class__.__name__})]. "
                    f"Last response headers: {self.client.last_response_headers} "
                    f"Last json response: {self.client.last_json_response}"
                )
            raise
