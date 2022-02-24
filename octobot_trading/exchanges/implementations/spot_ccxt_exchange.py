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
import typing

import ccxt.async_support as ccxt
from octobot_commons import enums as common_enums

import octobot_trading.enums as enums
import octobot_trading.errors as errors
import octobot_trading.exchanges.types as exchanges_types
import octobot_trading.exchanges.connectors as exchange_connectors
import octobot_trading.personal_data as personal_data
from octobot_trading.enums import ExchangeConstantsOrderColumns as ecoc


class SpotCCXTExchange(exchanges_types.SpotExchange):
    ORDER_NON_EMPTY_FIELDS = [ecoc.ID.value, ecoc.TIMESTAMP.value, ecoc.SYMBOL.value, ecoc.TYPE.value,
                              ecoc.SIDE.value, ecoc.PRICE.value, ecoc.AMOUNT.value, ecoc.STATUS.value]
    ORDER_REQUIRED_FIELDS = ORDER_NON_EMPTY_FIELDS + [ecoc.REMAINING.value]

    def __init__(self, config, exchange_manager):
        super().__init__(config, exchange_manager)
        self.connector = exchange_connectors.CCXTExchange(
            config,
            exchange_manager,
            additional_ccxt_config=self.get_additional_connector_config()
        )

        self.connector.client.options['defaultType'] = self.get_default_type()

    async def initialize_impl(self):
        await self.connector.initialize()
        self.symbols = self.connector.symbols
        self.time_frames = self.connector.time_frames

    async def stop(self) -> None:
        await self.connector.stop()
        self.exchange_manager = None

    @classmethod
    def is_supporting_exchange(cls, exchange_candidate_name) -> bool:
        return exchange_connectors.CCXTExchange.is_supporting_exchange(exchange_candidate_name)

    def get_default_type(self):
        # keep default value
        return self.connector.client.options['defaultType']

    async def create_order(self, order_type: enums.TraderOrderType, symbol: str, quantity: decimal.Decimal,
                           price: decimal.Decimal = None, stop_price: decimal.Decimal = None,
                           side: enums.TradeOrderSide = None, current_price: decimal.Decimal = None,
                           params: dict = None) \
            -> typing.Optional[dict]:
        async with self._order_operation(order_type, symbol, quantity, price, stop_price):
            created_order = await self._create_order_with_retry(order_type, symbol, quantity,
                                                                price, side, current_price, params)
            return await self._verify_order(created_order, order_type, symbol, price)
        return None

    async def edit_order(self, order_id: str, order_type: enums.TraderOrderType, symbol: str,
                         quantity: decimal.Decimal, price: decimal.Decimal,
                         stop_price: decimal.Decimal = None, side: enums.TradeOrderSide = None,
                         current_price: decimal.Decimal = None,
                         params: dict = None):
        # Note: on most exchange, this implementation will just replace the order by cancelling the one
        # which id is given and create a new one
        async with self._order_operation(order_type, symbol, quantity, price, stop_price):
            float_quantity = float(quantity)
            float_price = float(price)
            float_stop_price = None if stop_price is None else float(stop_price)
            float_current_price = None if current_price is None else float(current_price)
            side = None if side is None else side.value
            params = {} if params is None else params
            params.update(self.exchange_manager.exchange_backend.get_orders_parameters(None))
            edited_order = await self._edit_order(order_id, order_type, symbol, quantity=float_quantity,
                                                  price=float_price, stop_price=float_stop_price, side=side,
                                                  current_price=float_current_price, params=params)
            return await self._verify_order(edited_order, order_type, symbol, price)
        return None

    async def _edit_order(self, order_id: str, order_type: enums.TraderOrderType, symbol: str,
                          quantity: float, price: float, stop_price: float = None, side: str = None,
                          current_price: float = None, params: dict = None):
        ccxt_order_type = self.connector.get_ccxt_order_type(order_type)
        price_to_use = price
        if ccxt_order_type == enums.TradeOrderType.MARKET.value:
            # can't set price in market orders
            price_to_use = None
        # do not use keyword arguments here as default ccxt edit order is passing *args (and not **kwargs)
        return await self.connector.client.edit_order(order_id, symbol, ccxt_order_type, side,
                                                      quantity, price_to_use, params)

    @contextlib.asynccontextmanager
    async def _order_operation(self, order_type, symbol, quantity, price, stop_price):
        try:
            yield
        except ccxt.InsufficientFunds as e:
            self.log_order_creation_error(e, order_type, symbol, quantity, price, stop_price)
            self.logger.warning(str(e))
            raise errors.MissingFunds(e)
        except ccxt.NotSupported:
            raise errors.NotSupported
        except Exception as e:
            self.log_order_creation_error(e, order_type, symbol, quantity, price, stop_price)
            self.logger.exception(e, True, f"Unexpected error when creating order: {e}")

    async def _verify_order(self, created_order, order_type, symbol, price, params=None):
        # some exchanges are not returning the full order details on creation: fetch it if necessary
        if created_order and not self._ensure_order_details_completeness(created_order):
            if ecoc.ID.value in created_order:
                params = params or {}
                created_order = await self.exchange_manager.exchange.get_order(created_order[ecoc.ID.value], symbol,
                                                                               params=params)

        # on some exchange, market order are not not including price, add it manually to ensure uniformity
        if created_order[ecoc.PRICE.value] is None and price is not None:
            created_order[ecoc.PRICE.value] = float(price)

        return self.clean_order(created_order)

    async def _create_order_with_retry(self, order_type, symbol, quantity: decimal.Decimal,
                                       price: decimal.Decimal, side: enums.TradeOrderSide,
                                       current_price: decimal.Decimal, params) -> dict:
        try:
            return await self._create_specific_order(order_type, symbol, quantity, price=price, side=side,
                                                     current_price=current_price, params=params)
        except (ccxt.InvalidOrder, ccxt.BadRequest) as e:
            # can be raised when exchange precision/limits rules change
            self.logger.debug(f"Failed to create order ({e}) : order_type: {order_type}, symbol: {symbol}. "
                              f"This might be due to an update on {self.name} market rules. Fetching updated rules.")
            await self.connector.client.load_markets(reload=True)
            # retry order creation with updated markets (ccxt will use the updated market values)
            return await self._create_specific_order(order_type, symbol, quantity, price=price, side=side,
                                                     current_price=current_price, params=params)

    def _ensure_order_details_completeness(self, order, order_required_fields=None, order_non_empty_fields=None):
        if order_required_fields is None:
            order_required_fields = self.ORDER_REQUIRED_FIELDS
        if order_non_empty_fields is None:
            order_non_empty_fields = self.ORDER_NON_EMPTY_FIELDS
        # ensure all order_required_fields are present and all order_non_empty_fields are not empty
        return all(key in order for key in order_required_fields) and \
            all(order[key] for key in order_non_empty_fields)

    async def _create_specific_order(self, order_type, symbol, quantity: decimal.Decimal, price: decimal.Decimal = None,
                                     side: enums.TradeOrderSide = None, current_price: decimal.Decimal = None,
                                     params=None) -> dict:
        created_order = None
        float_quantity = float(quantity)
        float_price = float(price)
        float_current_price = float(current_price)
        side = None if side is None else side.value
        params = {} if params is None else params
        params.update(self.exchange_manager.exchange_backend.get_orders_parameters(None))
        if order_type == enums.TraderOrderType.BUY_MARKET:
            created_order = await self._create_market_buy_order(symbol, float_quantity, price=float_price,
                                                                params=params)
        elif order_type == enums.TraderOrderType.BUY_LIMIT:
            created_order = await self._create_limit_buy_order(symbol, float_quantity, price=float_price,
                                                               params=params)
        elif order_type == enums.TraderOrderType.SELL_MARKET:
            created_order = await self._create_market_sell_order(symbol, float_quantity, price=float_price,
                                                                 params=params)
        elif order_type == enums.TraderOrderType.SELL_LIMIT:
            created_order = await self._create_limit_sell_order(symbol, float_quantity, price=float_price,
                                                                params=params)
        elif order_type == enums.TraderOrderType.STOP_LOSS:
            created_order = await self._create_market_stop_loss_order(symbol, float_quantity, price=float_price,
                                                                      side=side, current_price=float_current_price,
                                                                      params=params)
        elif order_type == enums.TraderOrderType.STOP_LOSS_LIMIT:
            created_order = await self._create_limit_stop_loss_order(symbol, float_quantity, price=float_price,
                                                                     side=side, params=params)
        elif order_type == enums.TraderOrderType.TAKE_PROFIT:
            created_order = await self._create_market_take_profit_order(symbol, float_quantity, price=float_price,
                                                                        side=side, params=params)
        elif order_type == enums.TraderOrderType.TAKE_PROFIT_LIMIT:
            created_order = await self._create_limit_take_profit_order(symbol, float_quantity, price=float_price,
                                                                       side=side, params=params)
        elif order_type == enums.TraderOrderType.TRAILING_STOP:
            created_order = await self._create_market_trailing_stop_order(symbol, float_quantity, price=float_price,
                                                                          side=side, params=params)
        elif order_type == enums.TraderOrderType.TRAILING_STOP_LIMIT:
            created_order = await self._create_limit_trailing_stop_order(symbol, float_quantity, price=float_price,
                                                                         side=side, params=params)
        return created_order

    async def _create_market_buy_order(self, symbol, quantity, price=None, params=None) -> dict:
        return await self.connector.client.create_market_buy_order(symbol, quantity, params=params)

    async def _create_limit_buy_order(self, symbol, quantity, price=None, params=None) -> dict:
        return await self.connector.client.create_limit_buy_order(symbol, quantity, price, params=params)

    async def _create_market_sell_order(self, symbol, quantity, price=None, params=None) -> dict:
        return await self.connector.client.create_market_sell_order(symbol, quantity, params=params)

    async def _create_limit_sell_order(self, symbol, quantity, price=None, params=None) -> dict:
        return await self.connector.client.create_limit_sell_order(symbol, quantity, price, params=params)

    async def _create_market_stop_loss_order(self, symbol, quantity, price, side, current_price, params=None) -> dict:
        raise NotImplementedError("_create_market_stop_loss_order is not implemented")

    async def _create_limit_stop_loss_order(self, symbol, quantity, price=None, side=None, params=None) -> dict:
        raise NotImplementedError("_create_limit_stop_loss_order is not implemented")

    async def _create_market_take_profit_order(self, symbol, quantity, price=None, side=None, params=None) -> dict:
        raise NotImplementedError("_create_market_take_profit_order is not implemented")

    async def _create_limit_take_profit_order(self, symbol, quantity, price=None, side=None, params=None) -> dict:
        raise NotImplementedError("_create_limit_take_profit_order is not implemented")

    async def _create_market_trailing_stop_order(self, symbol, quantity, price=None, side=None, params=None) -> dict:
        raise NotImplementedError("_create_market_trailing_stop_order is not implemented")

    async def _create_limit_trailing_stop_order(self, symbol, quantity, price=None, side=None, params=None) -> dict:
        raise NotImplementedError("_create_limit_trailing_stop_order is not implemented")

    def get_exchange_current_time(self):
        return self.connector.get_exchange_current_time()

    def get_uniform_timestamp(self, timestamp):
        return self.connector.get_uniform_timestamp(timestamp)

    def get_market_status(self, symbol, price_example=None, with_fixer=True):
        return self.connector.get_market_status(symbol, price_example=price_example, with_fixer=with_fixer)

    async def get_balance(self, **kwargs: dict):
        return await self.connector.get_balance(**kwargs)

    async def get_symbol_prices(self, symbol: str, time_frame: common_enums.TimeFrames, limit: int = None,
                                **kwargs: dict) -> typing.Optional[list]:
        return await self.connector.get_symbol_prices(symbol=symbol, time_frame=time_frame, limit=limit, **kwargs)

    async def get_kline_price(self, symbol: str, time_frame: common_enums.TimeFrames, **kwargs: dict) -> typing.Optional[list]:
        return await self.connector.get_kline_price(symbol=symbol, time_frame=time_frame, **kwargs)

    async def get_order_book(self, symbol: str, limit: int = 5, **kwargs: dict) -> typing.Optional[dict]:
        return await self.connector.get_order_book(symbol=symbol, limit=limit, **kwargs)

    async def get_recent_trades(self, symbol: str, limit: int = 50, **kwargs: dict) -> typing.Optional[list]:
        return await self.connector.get_recent_trades(symbol=symbol, limit=limit, **kwargs)

    async def get_price_ticker(self, symbol: str, **kwargs: dict) -> typing.Optional[dict]:
        return await self.connector.get_price_ticker(symbol=symbol, **kwargs)

    async def get_all_currencies_price_ticker(self, **kwargs: dict) -> typing.Optional[list]:
        return await self.connector.get_all_currencies_price_ticker(**kwargs)

    async def get_order(self, order_id: str, symbol: str = None, **kwargs: dict) -> dict:
        return await self.connector.get_order(symbol=symbol, order_id=order_id, **kwargs)

    async def get_all_orders(self, symbol: str = None, since: int = None, limit: int = None, **kwargs: dict) -> list:
        return await self.connector.get_all_orders(symbol=symbol, since=since, limit=limit, **kwargs)

    async def get_open_orders(self, symbol: str = None, since: int = None, limit: int = None, **kwargs: dict) -> list:
        return await self.connector.get_open_orders(symbol=symbol, since=since, limit=limit, **kwargs)

    async def get_closed_orders(self, symbol: str = None, since: int = None, limit: int = None, **kwargs: dict) -> list:
        return await self.connector.get_closed_orders(symbol=symbol, since=since, limit=limit, **kwargs)

    async def get_my_recent_trades(self, symbol: str = None, since: int = None, limit: int = None, **kwargs: dict) -> list:
        return await self.connector.get_my_recent_trades(symbol=symbol, since=since, limit=limit, **kwargs)

    async def cancel_order(self, order_id: str, symbol: str = None, **kwargs: dict) -> bool:
        return await self.connector.cancel_order(symbol=symbol, order_id=order_id, **kwargs)

    def get_trade_fee(self, symbol, order_type, quantity, price, taker_or_maker):
        return self.connector.get_trade_fee(symbol, order_type, quantity, price, taker_or_maker)

    def get_fees(self, symbol):
        return self.connector.get_fees(symbol)

    def get_pair_from_exchange(self, pair) -> str:
        return self.connector.get_pair_from_exchange(pair)

    def get_split_pair_from_exchange(self, pair) -> (str, str):
        return self.connector.get_split_pair_from_exchange(pair)

    def get_exchange_pair(self, pair) -> str:
        return self.connector.get_exchange_pair(pair)

    def get_pair_cryptocurrency(self, pair) -> str:
        return self.connector.get_pair_cryptocurrency(pair)

    def get_default_balance(self):
        return self.connector.get_default_balance()

    def get_rate_limit(self):
        return self.connector.get_rate_limit()

    async def switch_to_account(self, account_type: enums.AccountTypes):
        return await self.connector.switch_to_account(account_type=account_type)

    def parse_balance(self, balance):
        return personal_data.parse_decimal_portfolio(self.connector.parse_balance(balance))

    def parse_trade(self, trade):
        return self.connector.parse_trade(trade)

    def parse_order(self, order):
        return self.connector.parse_order(order)

    def parse_ticker(self, ticker):
        return self.connector.parse_ticker(ticker)

    def parse_ohlcv(self, ohlcv):
        return self.connector.parse_ohlcv(ohlcv)

    def parse_order_book(self, order_book):
        return self.connector.parse_order_book(order_book)

    def parse_order_book_ticker(self, order_book_ticker):
        return self.connector.parse_order_book_ticker(order_book_ticker)

    def parse_timestamp(self, data_dict, timestamp_key, default_value=None, ms=False):
        return self.connector.parse_timestamp(data_dict, timestamp_key, default_value=default_value, ms=ms)

    def parse_currency(self, currency):
        return self.connector.parse_currency(currency)

    def parse_order_id(self, order):
        return self.connector.parse_order_id(order)

    def parse_order_symbol(self, order):
        return self.connector.parse_order_symbol(order)

    def parse_status(self, status):
        return self.connector.parse_status(status)

    def parse_side(self, side):
        return self.connector.parse_side(side)

    def parse_account(self, account):
        return self.connector.parse_account(account)

    def clean_recent_trade(self, recent_trade):
        return self.connector.clean_recent_trade(recent_trade)

    def clean_trade(self, trade):
        return self.connector.clean_trade(trade)

    def clean_order(self, order):
        return self.connector.clean_order(order)
