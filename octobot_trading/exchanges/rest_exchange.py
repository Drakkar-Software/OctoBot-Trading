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
import logging

import ccxt.async_support as ccxt
from ccxt.async_support import OrderNotFound, BaseError, InsufficientFunds
from ccxt.base.errors import ExchangeNotAvailable, InvalidNonce, BadSymbol, RequestTimeout

from octobot_commons.constants import MSECONDS_TO_MINUTE
from octobot_commons.dict_util import get_value_or_default
from octobot_commons.enums import TimeFramesMinutes
from octobot_trading.constants import CONFIG_DEFAULT_FEES, CONFIG_PORTFOLIO_INFO, CONFIG_PORTFOLIO_FREE, \
    CONFIG_PORTFOLIO_USED, CONFIG_PORTFOLIO_TOTAL
from octobot_trading.enums import TraderOrderType, ExchangeConstantsMarketPropertyColumns, \
    ExchangeConstantsOrderColumns as ecoc, TradeOrderSide, OrderStatus, AccountTypes
from octobot_trading.exchanges.abstract_exchange import AbstractExchange
from octobot_trading.exchanges.util.exchange_market_status_fixer import ExchangeMarketStatusFixer


class RestExchange(AbstractExchange):
    """
    CCXT library wrapper
    """

    BUY_STR = TradeOrderSide.BUY.value
    SELL_STR = TradeOrderSide.SELL.value

    ACCOUNTS = {}

    CCXT_CLIENT_LOGIN_OPTIONS = {}

    def __init__(self, config, exchange_type, exchange_manager, is_sandboxed=False):
        super().__init__(config, exchange_type, exchange_manager)
        # We will need to create the rest client and fetch exchange config
        self.is_authenticated = False
        self.is_sandboxed = is_sandboxed
        self.current_account = AccountTypes.CASH
        self._create_client()

    async def initialize_impl(self):
        try:
            self.set_sandbox_mode(self.is_sandboxed)
            await self.client.load_markets()
        except (ExchangeNotAvailable, RequestTimeout) as e:
            self.logger.error(f"initialization impossible: {e}")

    @staticmethod
    def create_exchange_type(exchange_class_string):
        if isinstance(exchange_class_string, str):
            return getattr(ccxt, exchange_class_string)
        return exchange_class_string

    def _create_client(self):
        """
        Exchange instance creation
        :return:
        """
        if self.exchange_manager.ignore_config or self.exchange_manager.check_config(self.name):
            try:
                key, secret, password = self.exchange_manager.get_exchange_credentials(self.logger, self.name)
                if key and secret:
                    self.is_authenticated = True

                self.client = self.exchange_type({
                    'apiKey': key,
                    'secret': secret,
                    'password': password,
                    'verbose': False,
                    'enableRateLimit': True,
                    'options': self.CCXT_CLIENT_LOGIN_OPTIONS
                })
            except Exception as e:
                self.is_authenticated = False
                self.exchange_manager.handle_token_error(e, self.logger)
                self.client = self.exchange_type({
                    'verbose': False,
                    'enableRateLimit': True,
                    'options': self.CCXT_CLIENT_LOGIN_OPTIONS
                })
        else:
            self.client = self.exchange_type({
                'verbose': False,
                'enableRateLimit': True,
                'options': self.CCXT_CLIENT_LOGIN_OPTIONS
            })
            self.logger.error("configuration issue: missing login information !")
        self.client.logger.setLevel(logging.INFO)

    def get_market_status(self, symbol, price_example=None, with_fixer=True):
        try:
            if with_fixer:
                return ExchangeMarketStatusFixer(self.client.market(symbol), price_example).market_status
            else:
                return self.client.market(symbol)
        except Exception as e:
            self.logger.error(f"Fail to get market status of {symbol}: {e}")
            return {}

    # total (free + used), by currency
    async def get_balance(self):
        try:
            balance = await self.client.fetch_balance(params={'recvWindow': 10000000})

            # store portfolio global info
            self.info_list = balance[CONFIG_PORTFOLIO_INFO]
            self.free = balance[CONFIG_PORTFOLIO_FREE]
            self.used = balance[CONFIG_PORTFOLIO_USED]
            self.total = balance[CONFIG_PORTFOLIO_TOTAL]

            # remove not currency specific keys
            balance.pop(CONFIG_PORTFOLIO_INFO, None)
            balance.pop(CONFIG_PORTFOLIO_FREE, None)
            balance.pop(CONFIG_PORTFOLIO_USED, None)
            balance.pop(CONFIG_PORTFOLIO_TOTAL, None)
            return balance

        except InvalidNonce as e:
            self.logger.error(f"Error when loading {self.name} real trader portfolio: {e}. "
                              f"To fix this, please synchronize your computer's clock. ")
            raise e

    def get_candle_since_timestamp(self, time_frame, count):
        return self.client.milliseconds() - TimeFramesMinutes[time_frame] * MSECONDS_TO_MINUTE * count

    async def get_symbol_prices(self, symbol, time_frame, limit=None):
        try:
            if limit:
                return await self.client.fetch_ohlcv(symbol, time_frame.value, limit=limit,
                                                     since=self.get_candle_since_timestamp(time_frame, limit))
            return await self.client.fetch_ohlcv(symbol, time_frame.value)
        except BaseError as e:
            self.logger.error(f"Failed to get_symbol_prices {e}")
            return None

    async def get_kline_price(self, symbol, time_frame):
        try:
            # default implementation
            return await self.get_symbol_prices(symbol, time_frame, limit=1)
        except BaseError as e:
            self.logger.error(f"Failed to get_kline_price {e}")
            return None

    # return up to ten bidasks on each side of the order book stack
    async def get_order_book(self, symbol, limit=5):
        try:
            return await self.client.fetch_order_book(symbol, limit)
        except BaseError as e:
            self.logger.error(f"Failed to get_order_book {e}")
            return None

    async def get_recent_trades(self, symbol, limit=50):
        try:
            return await self.client.fetch_trades(symbol, limit=limit)
        except BaseError as e:
            self.logger.error(f"Failed to get_recent_trades {e}")
            return None

    # A price ticker contains statistics for a particular market/symbol for some period of time in recent past (24h)
    async def get_price_ticker(self, symbol):
        try:
            return await self.client.fetch_ticker(symbol)
        except BaseError as e:
            self.logger.error(f"Failed to get_price_ticker {e}")
            return None

    async def get_all_currencies_price_ticker(self):
        try:
            self.all_currencies_price_ticker = await self.client.fetch_tickers()
            return self.all_currencies_price_ticker
        except BaseError as e:
            self.logger.error(f"Failed to get_all_currencies_price_ticker {e}")
            return None

    # ORDERS
    async def get_order(self, order_id, symbol=None):
        if self.client.has['fetchOrder']:
            try:
                return await self.client.fetch_order(order_id, symbol)
                # self.exchange_manager.exchange_personal_data.upsert_order(order_id, updated_order) TODO
            except OrderNotFound:
                # some exchanges are throwing this error when an order is cancelled (ex: coinbase pro)
                # self.exchange_manager.exchange_personal_data().update_order_attribute(order_id, ecoc.STATUS.value, OrderStatus.CANCELED.value) TODO
                pass
        else:
            raise Exception("This exchange doesn't support fetchOrder")

    async def get_all_orders(self, symbol=None, since=None, limit=None, params={}):
        if self.client.has['fetchOrders']:
            return await self.client.fetch_orders(symbol=symbol, since=since, limit=limit, params=params)
        else:
            raise Exception("This exchange doesn't support fetchOrders")

    async def get_open_orders(self, symbol=None, since=None, limit=None, params={}):
        if self.client.has['fetchOpenOrders']:
            return await self.client.fetch_open_orders(symbol=symbol, since=since, limit=limit, params=params)
        else:
            raise Exception("This exchange doesn't support fetchOpenOrders")

    async def get_closed_orders(self, symbol=None, since=None, limit=None, params={}):
        if self.client.has['fetchClosedOrders']:
            return await self.client.fetch_closed_orders(symbol=symbol, since=since, limit=limit, params=params)
        else:
            raise Exception("This exchange doesn't support fetchClosedOrders")

    async def get_my_recent_trades(self, symbol=None, since=None, limit=None, params={}):
        if self.client.has['fetchMyTrades'] or self.client.has['fetchTrades']:
            if self.client.has['fetchMyTrades']:
                return await self.client.fetch_my_trades(symbol=symbol, since=since, limit=limit, params=params)
            elif self.client.has['fetchTrades']:
                return await self.client.fetch_trades(symbol=symbol, since=since, limit=limit, params=params)
        else:
            raise Exception("This exchange doesn't support fetchMyTrades nor fetchTrades")

    async def cancel_order(self, order_id, symbol=None):
        try:
            return await self.client.cancel_order(order_id, symbol=symbol)
        except OrderNotFound:
            self.logger.error(f"Order {order_id} was not found")
        except Exception as e:
            self.logger.error(f"Order {order_id} failed to cancel | {e}")
        return None

    async def create_order(self, order_type, symbol, quantity, price=None, stop_price=None):
        try:
            created_order = await self._create_specific_order(order_type, symbol, quantity, price)
            # some exchanges are not returning the full order details on creation: fetch it if necessary
            if created_order and not RestExchange._ensure_order_details_completeness(created_order):
                if ecoc.ID.value in created_order:
                    order_symbol = created_order[ecoc.SYMBOL.value] if ecoc.SYMBOL.value in created_order else None
                    created_order = await self.exchange_manager.get_exchange().get_order(created_order[ecoc.ID.value],
                                                                                         order_symbol)

            # on some exchange, market order are not not including price, add it manually to ensure uniformity
            if created_order[ecoc.PRICE.value] is None and price is not None:
                created_order[ecoc.PRICE.value] = price

            return created_order

        except InsufficientFunds as e:
            self._log_error(e, order_type, symbol, quantity, price, stop_price)
            self.logger.warning(e)
        except Exception as e:
            self._log_error(e, order_type, symbol, quantity, price, stop_price)
            self.logger.error(e)
        return None

    # todo { 'type': 'trailing-stop' }
    async def _create_specific_order(self, order_type, symbol, quantity, price=None):
        created_order = None
        if order_type == TraderOrderType.BUY_MARKET:
            created_order = await self.client.create_market_buy_order(symbol, quantity)
        elif order_type == TraderOrderType.BUY_LIMIT:
            created_order = await self.client.create_limit_buy_order(symbol, quantity, price)
        elif order_type == TraderOrderType.SELL_MARKET:
            created_order = await self.client.create_market_sell_order(symbol, quantity)
        elif order_type == TraderOrderType.SELL_LIMIT:
            created_order = await self.client.create_limit_sell_order(symbol, quantity, price)
        elif order_type == TraderOrderType.STOP_LOSS:
            created_order = None
        elif order_type == TraderOrderType.STOP_LOSS_LIMIT:
            created_order = None
        elif order_type == TraderOrderType.TAKE_PROFIT:
            created_order = None
        elif order_type == TraderOrderType.TAKE_PROFIT_LIMIT:
            created_order = None
        return created_order

    @staticmethod
    def _ensure_order_details_completeness(order, order_required_fields=None):
        if order_required_fields is None:
            order_required_fields = [ecoc.ID.value, ecoc.TIMESTAMP.value, ecoc.SYMBOL.value, ecoc.TYPE.value,
                                     ecoc.SIDE.value, ecoc.PRICE.value, ecoc.AMOUNT.value, ecoc.REMAINING.value]
        return all(key in order for key in order_required_fields)

    def _log_error(self, error, order_type, symbol, quantity, price, stop_price):
        order_desc = f"order_type: {order_type}, symbol: {symbol}, quantity: {quantity}, price: {price}," \
                     f" stop_price: {stop_price}"
        self.logger.error(f"Failed to create order : {error} ({order_desc})")

    def get_trade_fee(self, symbol, order_type, quantity, price, taker_or_maker):
        return self.client.calculate_fee(symbol=symbol,
                                         type=order_type,
                                         side=RestExchange._get_side(order_type),
                                         amount=quantity,
                                         price=price,
                                         takerOrMaker=taker_or_maker)

    def get_fees(self, symbol):
        try:
            market_status = self.client.market(symbol)
            return {
                ExchangeConstantsMarketPropertyColumns.TAKER.value:
                    get_value_or_default(market_status, ExchangeConstantsMarketPropertyColumns.TAKER.value,
                                         CONFIG_DEFAULT_FEES),
                ExchangeConstantsMarketPropertyColumns.MAKER.value:
                    get_value_or_default(market_status, ExchangeConstantsMarketPropertyColumns.MAKER.value,
                                         CONFIG_DEFAULT_FEES),
                ExchangeConstantsMarketPropertyColumns.FEE.value:
                    get_value_or_default(market_status, ExchangeConstantsMarketPropertyColumns.FEE.value,
                                         CONFIG_DEFAULT_FEES)
            }
        except Exception as e:
            self.logger.error(f"Fees data for {symbol} was not found ({e})")
            return {
                ExchangeConstantsMarketPropertyColumns.TAKER.value: CONFIG_DEFAULT_FEES,
                ExchangeConstantsMarketPropertyColumns.MAKER.value: CONFIG_DEFAULT_FEES,
                ExchangeConstantsMarketPropertyColumns.FEE.value: CONFIG_DEFAULT_FEES
            }

    def get_uniform_timestamp(self, timestamp):
        return timestamp / 1000

    async def stop(self):
        self.logger.info(f"Closing connection.")
        await self.client.close()
        self.logger.info(f"Connection closed.")

    def get_pair_from_exchange(self, pair) -> str:
        try:
            return self.client.market(pair)["symbol"]
        except BadSymbol:
            try:
                return self.client.markets_by_id[pair]["symbol"]
            except KeyError:
                self.logger.error(f"Failed to get market of {pair}")
                return None

    def get_split_pair_from_exchange(self, pair) -> (str, str):
        try:
            market_data: dict = self.client.market(pair)
            return market_data["base"], market_data["quote"]
        except BadSymbol:
            try:
                return self.client.markets_by_id[pair]["base"], self.client.markets_by_id[pair]["quote"]
            except KeyError:
                self.logger.error(f"Failed to get market of {pair}")
                return None, None

    def get_exchange_pair(self, pair: str) -> str:
        if pair in self.client.symbols:
            try:
                return self.client.market(pair)["id"]
            except KeyError:
                raise KeyError(f'{pair} is not supported')
        else:
            raise ValueError(f'{pair} is not supported')

    def get_default_balance(self):
        return self.client.account()

    def set_sandbox_mode(self, is_sandboxed):
        self.client.setSandboxMode(is_sandboxed)

    @staticmethod
    def _get_side(order_type):
        return TradeOrderSide.BUY.value if order_type in (TraderOrderType.BUY_LIMIT, TraderOrderType.BUY_MARKET) \
            else TradeOrderSide.SELL.value

    """
    Accounts
    """

    async def switch_to_account(self, account_type):
        raise NotImplementedError("switch_to_account is not available on this exchange")

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
        return self.client.parse_ohlcv(ohlcv)

    def parse_order_book(self, order_book):
        return self.client.parse_order_book(order_book)

    def parse_timestamp(self, data_dict, timestamp_key, default_value=None, ms=False):
        parsed_timestamp = self.client.parse8601(self.client.safe_string(data_dict, timestamp_key))
        return (parsed_timestamp if ms else parsed_timestamp * 10 ** -3) if parsed_timestamp else default_value

    def parse_currency(self, currency):
        return self.client.safe_currency_code(currency)

    def parse_status(self, status):
        return OrderStatus(self.client.parse_order_status(status))

    def parse_side(self, side):
        return TradeOrderSide.BUY if side == self.BUY_STR else TradeOrderSide.SELL

    def parse_account(self, account):
        return AccountTypes[account]
