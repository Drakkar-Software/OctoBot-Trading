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
import time
import typing

import ccxt.async_support as ccxt
import octobot_commons.enums as common_enums

from octobot_commons import number_util

import octobot_trading.enums as enums
import octobot_trading.errors as errors
from octobot_trading.exchanges.config import (
    ccxt_exchange_settings,
    ccxt_exchange_ui_settings,
)
import octobot_trading.exchanges.types as exchanges_types
import octobot_trading.exchanges.connectors as exchange_connectors
import octobot_trading.personal_data as personal_data


# TODO remove
class SpotCCXTExchange(exchanges_types.SpotExchange):
    CONNECTOR_CLASS = exchange_connectors.CCXTExchange
    CONNECTOR_CONFIG: ccxt_exchange_settings.CCXTExchangeConfig = (
        ccxt_exchange_settings.CCXTExchangeConfig
    )

    def __init__(self, config, exchange_manager):
        self.initialize_connector_config()
        super().__init__(config, exchange_manager)
        self.connector = self.CONNECTOR_CLASS(
            config,
            exchange_manager,
            additional_ccxt_config=self.get_additional_connector_config(),
            connector_config=self.CONNECTOR_CONFIG,
        )

        self.connector.client.options["defaultType"] = self.get_default_type()
        
    @classmethod
    def initialize_connector_config(cls):
        cls.CONNECTOR_CONFIG = cls.CONNECTOR_CONFIG(cls.CONNECTOR_CLASS)
        
    async def initialize_impl(self):
        await self.connector.initialize()
        self.symbols = self.connector.symbols
        self.time_frames = self.connector.time_frames

    @classmethod
    def init_user_inputs(cls, inputs: dict) -> None:
        """
        Called at constructor, should define all the exchange's user inputs.
        """
        if not cls.CONNECTOR_CONFIG.is_fully_tested_and_supported():
            ccxt_exchange_ui_settings.initialize_experimental_exchange_settings(
                cls, inputs
            )

    @classmethod
    def is_configurable(cls):
        return True

    async def stop(self) -> None:
        await self.connector.stop()
        self.exchange_manager = None

    @classmethod
    def is_supporting_exchange(
        cls, exchange_candidate_name
    ) -> bool:  # move to connector
        return (
            cls.CONNECTOR_CLASS.is_supporting_exchange(exchange_candidate_name)
            or cls.get_name() == exchange_candidate_name
        )

    def get_default_type(self):
        # keep default value
        return self.connector.client.options['defaultType']

    async def create_order(self, order_type: enums.TraderOrderType, symbol: str, quantity: decimal.Decimal,
                           price: decimal.Decimal = None, stop_price: decimal.Decimal = None,
                           side: enums.TradeOrderSide = None, current_price: decimal.Decimal = None,
                           params: dict = None) \
            -> typing.Optional[dict]:
        # todo move to connector
        async with self._order_operation(order_type, symbol, quantity, price, stop_price):
            raw_created_order = await self._create_order_with_retry(order_type, symbol, quantity,
                                                                    price, side, current_price, params)
            return await self.connector.parse_order(raw_created_order, order_type=order_type.value, quantity=quantity,
                                                    price=price, status=enums.OrderStatus.OPEN.value,
                                                    symbol=symbol, side=side, timestamp=time.time())

    async def edit_order(self, order_id: str, order_type: enums.TraderOrderType, symbol: str,
                         quantity: decimal.Decimal, price: decimal.Decimal,
                         stop_price: decimal.Decimal = None, side: enums.TradeOrderSide = None,
                         current_price: decimal.Decimal = None,
                         params: dict = None):
        # todo move to connector
        # todo fix fails with "None future contract doesn't exist, fetching it"
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
            return await self.connector.parse_order(edited_order, order_type=order_type.value, quantity=quantity,
                                                    price=price, symbol=symbol, side=side)

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
            self.logger.exception(e, False, f"Unexpected error during order operation: {e}")

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

    async def _create_specific_order(self, order_type, symbol, quantity: decimal.Decimal, price: decimal.Decimal = None,
                                     side: enums.TradeOrderSide = None, current_price: decimal.Decimal = None,
                                     params=None) -> dict:
        # todo move to connector
        raw_created_order = None
        float_quantity = float(quantity)
        float_price = float(price)
        float_current_price = float(current_price)
        side = None if side is None else side.value
        params = {} if params is None else params
        params.update(self.exchange_manager.exchange_backend.get_orders_parameters(None))
        if order_type == enums.TraderOrderType.BUY_MARKET:
            raw_created_order = await self._create_market_buy_order(symbol, float_quantity, price=float_price,
                                                                    params=params)
        elif order_type == enums.TraderOrderType.BUY_LIMIT:
            raw_created_order = await self._create_limit_buy_order(symbol, float_quantity, price=float_price,
                                                                   params=params)
        elif order_type == enums.TraderOrderType.SELL_MARKET:
            raw_created_order = await self._create_market_sell_order(symbol, float_quantity, price=float_price,
                                                                     params=params)
        elif order_type == enums.TraderOrderType.SELL_LIMIT:
            raw_created_order = await self._create_limit_sell_order(symbol, float_quantity, price=float_price,
                                                                    params=params)
        elif order_type == enums.TraderOrderType.STOP_LOSS:
            raw_created_order = await self._create_market_stop_loss_order(symbol, float_quantity, price=float_price,
                                                                          side=side, current_price=float_current_price,
                                                                          params=params)
        elif order_type == enums.TraderOrderType.STOP_LOSS_LIMIT:
            raw_created_order = await self._create_limit_stop_loss_order(symbol, float_quantity, price=float_price,
                                                                         side=side, params=params)
        elif order_type == enums.TraderOrderType.TAKE_PROFIT:
            raw_created_order = await self._create_market_take_profit_order(symbol, float_quantity, price=float_price,
                                                                            side=side, params=params)
        elif order_type == enums.TraderOrderType.TAKE_PROFIT_LIMIT:
            raw_created_order = await self._create_limit_take_profit_order(symbol, float_quantity, price=float_price,
                                                                           side=side, params=params)
        elif order_type == enums.TraderOrderType.TRAILING_STOP:
            raw_created_order = await self._create_market_trailing_stop_order(symbol, float_quantity, price=float_price,
                                                                              side=side, params=params)
        elif order_type == enums.TraderOrderType.TRAILING_STOP_LIMIT:
            raw_created_order = await self._create_limit_trailing_stop_order(symbol, float_quantity, price=float_price,
                                                                             side=side, params=params)
        return raw_created_order

    async def _create_market_buy_order(self, symbol, quantity, price=None, params=None) -> dict:
        return await self.connector.client.create_market_buy_order(
            symbol,
            quantity,
            params=self.add_cost_to_market_order(quantity, price, params),
        )

    async def _create_limit_buy_order(self, symbol, quantity, price=None, params=None) -> dict:
        return await self.connector.client.create_limit_buy_order(symbol, quantity, price, params=params)

    async def _create_market_sell_order(
        self, symbol, quantity, price=None, params=None
    ) -> dict:
        return await self.connector.client.create_market_sell_order(
            symbol,
            quantity,
            params=self.add_cost_to_market_order(quantity, price, params),
        )

    async def _create_limit_sell_order(self, symbol, quantity, price=None, params=None) -> dict:
        return await self.connector.client.create_limit_sell_order(symbol, quantity, price, params=params)

    async def _create_market_stop_loss_order(self, symbol, quantity, price, side, current_price, params=None) -> dict:
        if self.connector.client.has.get("createStopOrder"):
            return await self.connector.client.create_stop_order(
                symbol,
                enums.TradeOrderType.MARKET.value,
                side,
                quantity,
                price,
                current_price,
                params=params,
            )
        if self.connector.client.has.get("createStopMarketOrder"):
            return await self.connector.client.create_stop_market_order(
                symbol, side, quantity, price, params=params
            )
        raise NotImplementedError("_create_market_stop_loss_order is not implemented")

    async def _create_limit_stop_loss_order(self, symbol, quantity, price=None, side=None, params=None) -> dict:
        if self.connector.client.has.get("createStopLimitOrder"):
            return await self.connector.client.create_stop_limit_order(
                symbol, side, quantity, price, params=params
            )
        raise NotImplementedError("_create_limit_stop_loss_order is not implemented")

    async def _create_market_take_profit_order(self, symbol, quantity, price=None, side=None, params=None) -> dict:
        raise NotImplementedError("_create_market_take_profit_order is not implemented")

    async def _create_limit_take_profit_order(self, symbol, quantity, price=None, side=None, params=None) -> dict:
        raise NotImplementedError("_create_limit_take_profit_order is not implemented")

    async def _create_market_trailing_stop_order(self, symbol, quantity, price=None, side=None, params=None) -> dict:
        raise NotImplementedError("_create_market_trailing_stop_order is not implemented")

    async def _create_limit_trailing_stop_order(self, symbol, quantity, price=None, side=None, params=None) -> dict:
        raise NotImplementedError("_create_limit_trailing_stop_order is not implemented")

    def add_cost_to_market_order(self, quantity, price, params) -> dict:
        if (
            self.CONNECTOR_CONFIG.ADD_COST_TO_CREATE_SPOT_MARKET_ORDER
            or self.CONNECTOR_CONFIG.ADD_COST_TO_CREATE_FUTURE_MARKET_ORDER
        ):
            return {**params, "cost": quantity * price}
        return params
    
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

    async def get_kline_price(self, symbol: str, time_frame: common_enums.TimeFrames, **kwargs: dict
                              ) -> typing.Optional[list]:
        return await self.connector.get_kline_price(symbol=symbol, time_frame=time_frame, **kwargs)

    async def get_order_book(self, symbol: str, limit: int = 5, **kwargs: dict) -> typing.Optional[dict]:
        return await self.connector.get_order_book(symbol=symbol, limit=limit, **kwargs)
   
    async def get_price_ticker(self, symbol: str, also_get_mini_ticker: bool=False, **kwargs: dict
                               ) -> typing.Tuple[dict, dict]:
        return await self.connector.get_price_ticker(
            symbol=symbol, also_get_mini_ticker=also_get_mini_ticker, **kwargs)
        
    async def get_all_currencies_price_ticker(self, **kwargs: dict) -> list:
        return await self.connector.get_all_currencies_price_ticker(**kwargs)

    async def get_order(self, order_id: str, symbol: str = None,
                        check_completeness: bool = None, **kwargs: dict) -> dict:
        return await self.connector.get_order(symbol=symbol, order_id=order_id,
                                              check_completeness=check_completeness, **kwargs)

    def custom_get_order_stop_params(self, order_id, params) -> dict:
        """
        override if certain parameters are required to fetch stop orders
        """
        return params

    def custom_get_all_orders_stop_params(self, params) -> dict:
        """
        override if certain parameters are required to fetch stop orders
        """
        return params

    def custom_get_open_orders_stop_params(self, params) -> dict:
        """
        override if certain parameters are required to fetch stop orders
        """
        return params

    def custom_get_closed_orders_stop_params(self, params) -> dict:
        """
        override if certain parameters are required to fetch stop orders
        """
        return params

    async def get_all_orders(self, symbol: str = None, since: int = None, limit: int = None,
                             check_completeness: bool = None, **kwargs: dict) -> list:
        return await self.connector.get_all_orders(symbol=symbol, since=since, limit=limit,
                                                   check_completeness=check_completeness, **kwargs)

    async def get_open_orders(self, symbol: str = None, since: int = None, limit: int = None,
                              check_completeness: bool = None, **kwargs: dict) -> list:
        return await self.connector.get_open_orders(symbol=symbol, since=since, limit=limit,
                                                    check_completeness=check_completeness, **kwargs)

    async def get_closed_orders(self, symbol: str = None, since: int = None, limit: int = None,
                                check_completeness: bool = None, **kwargs: dict) -> list:
        return await self.connector.get_closed_orders(symbol=symbol, since=since, limit=limit,
                                                      check_completeness=check_completeness, **kwargs)

    async def get_my_recent_trades(self, symbol: str = None, since: int = None, limit: int = None,
                                   check_completeness: bool = None, **kwargs: dict) -> list:
        return await self.connector.get_my_recent_trades(symbol=symbol, since=since, limit=limit,
                                                         check_completeness=check_completeness, **kwargs)

    async def get_recent_trades(self, symbol: str, limit: int = 50,
                                check_completeness: bool = None, **kwargs: dict) -> typing.Optional[list]:
        return await self.connector.get_recent_trades(symbol=symbol, limit=limit, check_completeness=check_completeness,
                                                      **kwargs)

    async def cancel_order(self, order_id: str, symbol: str = None, **kwargs: dict) -> bool:
        return await self.connector.cancel_order(symbol=symbol, order_id=order_id, **kwargs)

    def get_trade_fee(self, symbol, order_type, quantity, price, taker_or_maker):
        return self.connector.get_trade_fee(symbol, order_type, quantity, price, taker_or_maker)

    def get_fees(self, symbol):
        return self.connector.get_fees(symbol)

    def get_pair_from_exchange(self, pair) -> str:
        return self.connector.get_pair_from_exchange(pair)

    def get_split_pair_from_exchange(self, pair) -> typing.Tuple[str, str]:
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

    def parse_account(self, account):
        return self.connector.parse_account(account)
