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
import contextlib
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
import octobot_trading.personal_data as personal_data
from octobot_trading.enums import ExchangeConstantsOrderColumns as ecoc


class CCXTExchange(abstract_exchange.AbstractExchange):
    """
    CCXT library wrapper
    """
    CCXT_ISOLATED = "ISOLATED"
    CCXT_CROSSED = "CROSSED"

    def __init__(self, config, exchange_manager, additional_ccxt_config=None):
        super().__init__(config, exchange_manager)
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
                if not(key and secret) and not self.exchange_manager.is_simulated:
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

    def get_market_status(self, symbol, price_example=None, with_fixer=True):
        try:
            if with_fixer:
                return exchanges.ExchangeMarketStatusFixer(self.client.market(symbol), price_example).market_status
            return self.client.market(symbol)
        except ccxt.NotSupported:
            raise octobot_trading.errors.NotSupported
        except Exception as e:
            self.logger.error(f"Fail to get market status of {symbol}: {e}")
            return {}

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
                if limit:
                    return await self.client.fetch_ohlcv(symbol, time_frame.value, limit=limit,
                                                         since=since, params=kwargs)
                return await self.client.fetch_ohlcv(symbol, time_frame.value, since=since, params=kwargs)
        except ccxt.NotSupported:
            raise octobot_trading.errors.NotSupported
        except ccxt.BaseError as e:
            raise octobot_trading.errors.FailedRequest(f"Failed to get_symbol_prices: {e.__class__.__name__} on {e}")

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

    async def get_recent_trades(self, symbol: str, limit: int = 50, **kwargs: dict) -> typing.Optional[list]:
        try:
            with self.error_describer():
                return await self.client.fetch_trades(symbol, limit=limit, params=kwargs)
        except ccxt.NotSupported:
            raise octobot_trading.errors.NotSupported
        except ccxt.BaseError as e:
            raise octobot_trading.errors.FailedRequest(f"Failed to get_recent_trades {e}")

    # A price ticker contains statistics for a particular market/symbol for some period of time in recent past (24h)
    async def get_price_ticker(self, symbol: str, **kwargs: dict) -> typing.Optional[dict]:
        try:
            with self.error_describer():
                return await self.client.fetch_ticker(symbol, params=kwargs)
        except ccxt.NotSupported:
            raise octobot_trading.errors.NotSupported
        except ccxt.BaseError as e:
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

    # ORDERS
    async def get_order(self, order_id: str, symbol: str = None, **kwargs: dict) -> dict:
        if self.client.has['fetchOrder']:
            try:
                with self.error_describer():
                    params = kwargs.pop("params", {})
                    return await self.client.fetch_order(order_id, symbol, params=params, **kwargs)
                # self.exchange_manager.exchange_personal_data.upsert_order(order_id, updated_order) TODO
            except ccxt.OrderNotFound:
                # some exchanges are throwing this error when an order is cancelled (ex: coinbase pro)
                pass
            except ccxt.NotSupported as e:
                # some exchanges are throwing this error when an order is cancelled (ex: coinbase pro)
                raise octobot_trading.errors.NotSupported from e
        else:
            # When fetch_order is not supported, uses get_open_orders and extract order id
            open_orders = await self.get_open_orders(symbol=symbol)
            for order in open_orders:
                if order.get(ecoc.ID.value, None) == order_id:
                    return order
        return None  # OrderNotFound

    async def get_all_orders(self, symbol: str = None, since: int = None,
                             limit: int = None, **kwargs: dict) -> list:
        if self.client.has['fetchOrders']:
            with self.error_describer():
                return await self.client.fetch_orders(symbol=symbol, since=since, limit=limit, params=kwargs)
        else:
            raise octobot_trading.errors.NotSupported("This exchange doesn't support fetchOrders")

    async def get_open_orders(self, symbol: str = None, since: int = None,
                              limit: int = None, **kwargs: dict) -> list:
        if self.client.has['fetchOpenOrders']:
            with self.error_describer():
                return await self.client.fetch_open_orders(symbol=symbol, since=since, limit=limit, params=kwargs)
        else:
            raise octobot_trading.errors.NotSupported("This exchange doesn't support fetchOpenOrders")

    async def get_closed_orders(self, symbol: str = None, since: int = None,
                                limit: int = None, **kwargs: dict) -> list:
        if self.client.has['fetchClosedOrders']:
            with self.error_describer():
                return await self.client.fetch_closed_orders(symbol=symbol, since=since, limit=limit, params=kwargs)
        else:
            raise octobot_trading.errors.NotSupported("This exchange doesn't support fetchClosedOrders")

    async def get_my_recent_trades(self, symbol: str = None, since: int = None,
                                   limit: int = None, **kwargs: dict) -> list:
        if self.client.has['fetchMyTrades'] or self.client.has['fetchTrades']:
            with self.error_describer():
                if self.client.has['fetchMyTrades']:
                    return await self.client.fetch_my_trades(symbol=symbol, since=since, limit=limit, params=kwargs)
                elif self.client.has['fetchTrades']:
                    return await self.client.fetch_trades(symbol=symbol, since=since, limit=limit, params=kwargs)
        else:
            raise octobot_trading.errors.NotSupported("This exchange doesn't support fetchMyTrades nor fetchTrades")

    async def cancel_order(self, order_id: str, symbol: str = None, **kwargs: dict) -> bool:
        cancel_resp = None
        try:
            with self.error_describer():
                cancel_resp = await self.client.cancel_order(order_id, symbol=symbol, params=kwargs)
            try:
                cancelled_order = await self.exchange_manager.exchange.get_order(
                    order_id, symbol=symbol
                )
                return cancelled_order is None or personal_data.parse_is_cancelled(cancelled_order)
            except ccxt.OrderNotFound:
                # Order is not found: it has successfully been cancelled (some exchanges don't allow to
                # get a cancelled order).
                return True
        except ccxt.OrderNotFound:
            self.logger.error(f"Trying to cancel order with id {order_id} but order was not found")
        except (ccxt.NotSupported, octobot_trading.errors.NotSupported) as e:
            raise octobot_trading.errors.NotSupported from e
        except Exception as e:
            self.logger.exception(e, True, f"Order {order_id} failed to cancel | {e} ({e.__class__.__name__})")
        return cancel_resp is not None

    async def get_positions(self, symbols=None, **kwargs: dict) -> list:
        return await self.client.fetch_positions(symbols=symbols, params=kwargs)

    async def get_position(self, symbol: str, **kwargs: dict) -> dict:
        return await self.client.fetch_position(symbol=symbol, params=kwargs)

    async def get_funding_rate(self, symbol: str, **kwargs: dict) -> dict:
        return await self.client.fetch_funding_rate(symbol=symbol, params=kwargs)

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

    def get_ccxt_order_type(self, order_type: enums.TraderOrderType):
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
            self.logger.error(f"Fees data for {symbol} was not found ({e})")
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

    def get_split_pair_from_exchange(self, pair) -> (str, str):
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

    def parse_trade(self, trade):
        return self.client.parse_trade(trade)

    def parse_order(self, order):
        return self.client.parse_order(order)

    def parse_ticker(self, ticker):
        return self.client.parse_ticker(ticker)

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

    def parse_order_id(self, order):
        return order.get(ecoc.ID.value, None)

    def parse_order_symbol(self, order):
        return order.get(ecoc.SYMBOL.value, None)

    def parse_status(self, status):
        return enums.OrderStatus(self.client.parse_order_status(status))

    def parse_side(self, side):
        return enums.TradeOrderSide.BUY if side == self.BUY_STR else enums.TradeOrderSide.SELL

    def parse_account(self, account):
        return enums.AccountTypes[account]

    """
    Cleaners
    """

    def clean_recent_trade(self, recent_trade):
        try:
            recent_trade.pop(ecoc.INFO.value)
            recent_trade.pop(ecoc.DATETIME.value)
            recent_trade.pop(ecoc.ID.value)
            recent_trade.pop(ecoc.ORDER.value)
            recent_trade.pop(ecoc.FEE.value)
            recent_trade.pop(ecoc.TYPE.value)
            recent_trade.pop(ecoc.TAKER_OR_MAKER.value)
            recent_trade[ecoc.TIMESTAMP.value] = \
                self.get_uniformized_timestamp(recent_trade[ecoc.TIMESTAMP.value])
        except KeyError as e:
            self.logger.error(f"Fail to clean recent_trade dict ({e})")
        return recent_trade

    def clean_trade(self, trade):
        try:
            trade.pop(ecoc.INFO.value)
            trade[ecoc.TIMESTAMP.value] = \
                self.get_uniformized_timestamp(trade[ecoc.TIMESTAMP.value])
        except KeyError as e:
            self.logger.error(f"Fail to clean trade dict ({e})")
        return trade

    def clean_order(self, order):
        try:
            order.pop(ecoc.INFO.value)
            exchange_timestamp = order[ecoc.TIMESTAMP.value]
            order[ecoc.TIMESTAMP.value] = \
                self.get_uniformized_timestamp(exchange_timestamp)
        except KeyError as e:
            self.logger.error(f"Fail to cleanup order dict ({e})")
        return order

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
