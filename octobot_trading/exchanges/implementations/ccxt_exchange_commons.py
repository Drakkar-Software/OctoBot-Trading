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
import decimal
import typing

import octobot_commons.enums as common_enums
import octobot_trading.enums as enums
import octobot_trading.exchanges.connectors.ccxt.exchange_settings_ccxt_generic as exchange_settings_ccxt_generic
import octobot_trading.exchanges.connectors.exchange_settings as exchange_settings
import octobot_trading.exchanges.connectors.ccxt.ccxt_exchange_ui_settings as ccxt_exchange_ui_settings
import octobot_trading.exchanges.types as exchanges_types
import octobot_trading.exchanges.connectors as exchange_connectors


class CCXTExchangeCommons(exchanges_types.SpotExchange):
    CONNECTOR_CLASS = exchange_connectors.CCXTExchange
    CONNECTOR_CONFIG_CLASS: exchange_settings.ExchangeConfig = (
        exchange_settings_ccxt_generic.GenericCCXTExchangeConfig
    )
    CONNECTOR_CONFIG: exchange_settings.ExchangeConfig = None

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
        cls.CONNECTOR_CONFIG = cls.CONNECTOR_CONFIG_CLASS(cls.CONNECTOR_CLASS)

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
        _parser = self.CONNECTOR_CONFIG.ORDERS_PARSER(self.exchange_manager.exchange)
        return await _parser.parse_order(raw_order, order_type=order_type, quantity=quantity,
                                         price=price, status=status, symbol=symbol, side=side,
                                         timestamp=timestamp, check_completeness=check_completeness)

    async def parse_orders(self, raw_orders: list, order_type: str = None,
                           quantity: decimal.Decimal = None, price: decimal.Decimal = None,
                           status: str = None, symbol: str = None,
                           side: str = None, timestamp: int or float = None,
                           check_completeness: bool = True) -> list:
        """
        use this method to format a list of order dicts

        :param raw_orders: raw orders with eventually missing data

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
        _parser = self.CONNECTOR_CONFIG.ORDERS_PARSER(self.exchange_manager.exchange)
        return await _parser.parse_orders(raw_orders, order_type=order_type, quantity=quantity,
                                          price=price, status=status, symbol=symbol, side=side,
                                          timestamp=timestamp, check_completeness=check_completeness)

    async def parse_trade(self, raw_trade: dict, check_completeness: bool = True) -> dict:
        """
        use this method to parse a single trade

        :param raw_trade:

        :param check_completeness: if true checks all attributes, 
            if somethings missing it'll try to fetch it from the exchange

        :return: formatted trade dict (100% complete or we raise NotImplemented)
        """
        _parser = self.CONNECTOR_CONFIG.TRADES_PARSER(self.exchange_manager.exchange)
        return await _parser.parse_trade(raw_trade, check_completeness=check_completeness)

    async def parse_trades(self, raw_trades, check_completeness: bool = True) -> list:
        """
        use this method to format a list of trade dicts

        :param raw_trades: raw trades with eventually missing data

        :param check_completeness: if true checks all attributes, 
            if somethings missing it'll try to fetch it from the exchange

        :return: formatted trades list (100% complete or we raise NotImplemented report)
            
        """
        _parser = self.CONNECTOR_CONFIG.TRADES_PARSER(self.exchange_manager.exchange)
        return await _parser.parse_trades(raw_trades, check_completeness=check_completeness)

    async def parse_position(self, raw_position: dict) -> dict:
        """
        use this method to parse a single position

        :param raw_position:

        :return: formatted position dict (100% complete or we raise NotImplemented)
        """
        _parser = self.CONNECTOR_CONFIG.POSITIONS_PARSER(self.exchange_manager.exchange)
        return await _parser.parse_position(raw_position)

    async def parse_positions(self, raw_positions: list) -> list:
        """
        use this method to format a list of position dicts

        :param raw_positions: raw positions with eventually missing data

        :return: formatted positions list (100% complete or we raise NotImplemented report)
            
        """
        _parser = self.CONNECTOR_CONFIG.POSITIONS_PARSER(self.exchange_manager.exchange)
        return await _parser.parse_positions(raw_positions)

    async def parse_ticker(self, raw_funding_rate: dict, symbol: str, also_get_mini_ticker: bool = False) -> dict:
        _parser = self.CONNECTOR_CONFIG.TICKER_PARSER(self.exchange_manager.exchange)
        return await _parser.parse_ticker(
            raw_ticker=raw_funding_rate, symbol=symbol, also_get_mini_ticker=also_get_mini_ticker)

    async def parse_tickers(self, raw_tickers: list) -> list:
        _parser = self.CONNECTOR_CONFIG.TICKER_PARSER(self.exchange_manager.exchange)
        return await _parser.parse_ticker_list(raw_tickers=raw_tickers)

    def parse_funding_rates(self, raw_funding_rates: list) -> list:
        _parser = self.CONNECTOR_CONFIG.FUNDING_RATE_PARSER(self.exchange_manager.exchange)
        return _parser.parse_funding_rate_list(raw_funding_rates=raw_funding_rates)

    def parse_funding_rate(self, raw_funding_rate: dict, from_ticker: bool = False) -> dict:
        _parser = self.CONNECTOR_CONFIG.FUNDING_RATE_PARSER(self.exchange_manager.exchange)
        return _parser.parse_funding_rate(raw_funding_rate=raw_funding_rate, from_ticker=from_ticker)

    def parse_market_status(self, raw_market_status: dict, with_fixer: bool, price_example) -> dict:
        return self.CONNECTOR_CONFIG.MARKET_STATUS_PARSER(
            market_status=raw_market_status, with_fixer=with_fixer, price_example=price_example
        ).market_status

    async def create_order(self, order_type: enums.TraderOrderType, symbol: str, quantity: decimal.Decimal,
                           price: decimal.Decimal = None, stop_price: decimal.Decimal = None,
                           side: enums.TradeOrderSide = None, current_price: decimal.Decimal = None,
                           params: dict = None) -> dict:
        return await self.connector.create_order(
            order_type=order_type, symbol=symbol, quantity=quantity, price=price,
            stop_price=stop_price, side=side, current_price=current_price, params=params)

    async def edit_order(self, order_id: str, order_type: enums.TraderOrderType, symbol: str,
                         quantity: decimal.Decimal, price: decimal.Decimal,
                         stop_price: decimal.Decimal = None, side: enums.TradeOrderSide = None,
                         current_price: decimal.Decimal = None,
                         params: dict = None) -> dict:
        return await self.connector.edit_order(
            order_id=order_id, order_type=order_type, symbol=symbol, quantity=quantity,
            price=price, stop_price=stop_price, side=side, current_price=current_price, params=params)

    async def create_market_buy_order(self, symbol, quantity, price=None, params=None) -> dict:
        return await self.connector.create_market_buy_order(
            symbol=symbol, quantity=quantity, price=price, params=params)

    async def create_limit_buy_order(self, symbol, quantity, price=None, params=None) -> dict:
        return await self.connector.create_limit_buy_order(
            symbol=symbol, quantity=quantity, price=price, params=params)

    async def create_market_sell_order(self, symbol, quantity, price=None, params=None) -> dict:
        return await self.connector.create_market_sell_order(
            symbol=symbol, quantity=quantity, price=price, params=params)

    async def create_limit_sell_order(self, symbol, quantity, price=None, params=None) -> dict:
        return await self.connector.create_limit_sell_order(
            symbol=symbol, quantity=quantity, price=price, params=params)

    async def create_market_stop_loss_order(self, symbol, quantity, price, side, current_price, params=None) -> dict:
        return await self.connector.create_market_stop_loss_order(
            symbol=symbol, quantity=quantity, price=price, side=side, current_price=current_price, params=params)

    async def create_limit_stop_loss_order(self, symbol, quantity, price=None, side=None, params=None) -> dict:
        return await self.connector.create_limit_stop_loss_order(
            symbol=symbol, quantity=quantity, price=price, side=side, params=params)

    async def create_market_take_profit_order(self, symbol, quantity, price=None, side=None, params=None) -> dict:
        raise NotImplementedError("create_market_take_profit_order is not implemented")

    async def create_limit_take_profit_order(self, symbol, quantity, price=None, side=None, params=None) -> dict:
        raise NotImplementedError("create_limit_take_profit_order is not implemented")

    async def create_market_trailing_stop_order(self, symbol, quantity, price=None, side=None, params=None) -> dict:
        raise NotImplementedError("create_market_trailing_stop_order is not implemented")

    async def create_limit_trailing_stop_order(self, symbol, quantity, price=None, side=None, params=None) -> dict:
        raise NotImplementedError("create_limit_trailing_stop_order is not implemented")

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

    async def get_price_ticker(self, symbol: str, also_get_mini_ticker: bool = False, **kwargs: dict
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

    def custom_edit_stop_orders_params(self, order_id, stop_price, params) -> dict:
        """
        override if certain parameters are required to edit stop orders
        """
        return params
    
    def custom_cancel_stop_orders_params(self, order_id, stop_price, params) -> dict:
        """
        override if certain parameters are required to edit stop orders
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
        return self.connector.parse_balance(balance)

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
