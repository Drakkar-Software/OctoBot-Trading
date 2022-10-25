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

from octobot_commons import enums as common_enums

import octobot_trading.exchanges.connectors as exchange_connectors
import octobot_trading.exchanges.types as exchanges_types
import octobot_trading.personal_data as personal_data
import octobot_trading.enums as trading_enums

#TODO remove
class FutureCCXTExchange(exchanges_types.FutureExchange):
    CONNECTOR_CLASS = exchange_connectors.CCXTExchange

    def __init__(self, config, exchange_manager):
        super().__init__(config, exchange_manager)
        self.connector = self.CONNECTOR_CLASS(
            config,
            exchange_manager,
            additional_ccxt_config=self.get_additional_connector_config()
        )

    async def initialize_impl(self):
        await self.connector.initialize()
        self.symbols = self.connector.symbols
        self.time_frames = self.connector.time_frames

        self.connector.client.options['defaultType'] = self.get_default_type()

    async def stop(self) -> None:
        await self.connector.stop()
        self.exchange_manager = None

    @classmethod
    def is_supporting_exchange(cls, exchange_candidate_name) -> bool:
        return cls.CONNECTOR_CLASS.is_supporting_exchange(exchange_candidate_name)

    def get_default_type(self):
        return 'future'

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

    async def switch_to_account(self, account_type: trading_enums.AccountTypes):
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

    async def get_positions(self, **kwargs: dict) -> list:
        return await self.connector.get_positions(**kwargs)

    async def get_symbol_positions(self, symbol: str, **kwargs: dict) -> list:
        return await self.connector.get_symbol_positions(symbol=symbol, **kwargs)

    async def get_funding_rate(self, symbol: str, **kwargs: dict) -> dict:
        return await self.connector.get_funding_rate(symbol=symbol, **kwargs)

    async def get_funding_rate_history(self, symbol: str, limit: int = 1, **kwargs: dict) -> list:
        return await self.connector.get_funding_rate_history(symbol=symbol, limit=limit, **kwargs)

    async def set_symbol_leverage(self, symbol: str, leverage: int, **kwargs: dict):
        return await self.connector.set_symbol_leverage(leverage=leverage, symbol=symbol, **kwargs)

    async def set_symbol_margin_type(self, symbol: str, isolated: bool):
        return await self.connector.set_symbol_margin_type(symbol=symbol, isolated=isolated)

    async def set_symbol_position_mode(self, symbol: str, one_way: bool):
        return await self.connector.set_symbol_position_mode(symbol=symbol, one_way=one_way)

    async def set_symbol_partial_take_profit_stop_loss(self, symbol: str, inverse: bool,
                                                       tp_sl_mode: trading_enums.TakeProfitStopLossMode):
        return await self.connector.set_symbol_partial_take_profit_stop_loss(symbol=symbol, inverse=inverse,
                                                                             tp_sl_mode=tp_sl_mode)

    def get_pair_market_type(self, pair, property_name, def_value=False):
        return self.connector.client.safe_string(
            self.connector.client.safe_value(self.connector.client.markets, pair, {}), property_name, def_value
        )

    def is_linear_symbol(self, symbol):
        return self.get_pair_market_type(symbol, "linear") == "True"

    def is_inverse_symbol(self, symbol):
        return self.get_pair_market_type(symbol, "inverse") == "True"

    def is_futures_symbol(self, symbol):
        return self.get_pair_market_type(symbol, "futures") == "True"

    def is_swap_symbol(self, symbol):
        return self.get_pair_market_type(symbol, "swap") == "True"

    def is_option_symbol(self, symbol):
        return self.get_pair_market_type(symbol, "option") == "True"

    def parse_position(self, position_dict) -> dict:
        try:
            position_dict.update({
                trading_enums.ExchangeConstantsPositionColumns.SYMBOL.value:
                    position_dict.get(position_dict[trading_enums.ExchangePositionCCXTColumns.SYMBOL.value]),
                trading_enums.ExchangeConstantsPositionColumns.TIMESTAMP.value:
                    position_dict.get(trading_enums.ExchangePositionCCXTColumns.TIMESTAMP.value,
                                      self.connector.get_exchange_current_time()),
                trading_enums.ExchangeConstantsPositionColumns.SIDE.value:
                    self.parse_position_side(
                        position_dict.get(trading_enums.ExchangePositionCCXTColumns.SIDE.value,
                                          trading_enums.PositionSide.UNKNOWN.value), None),
                trading_enums.ExchangeConstantsPositionColumns.MARGIN_TYPE.value:
                    position_dict.get(trading_enums.ExchangePositionCCXTColumns.MARGIN_TYPE.value, None),
                trading_enums.ExchangeConstantsPositionColumns.QUANTITY.value:
                    decimal.Decimal(
                        f"{position_dict.get(trading_enums.ExchangePositionCCXTColumns.CONTRACT_SIZE.value, 0)}"),
                trading_enums.ExchangeConstantsPositionColumns.COLLATERAL.value:
                    decimal.Decimal(
                        f"{position_dict.get(trading_enums.ExchangePositionCCXTColumns.COLLATERAL.value, 0)}"),
                trading_enums.ExchangeConstantsPositionColumns.NOTIONAL.value:
                    decimal.Decimal(
                        f"{position_dict.get(trading_enums.ExchangePositionCCXTColumns.NOTIONAL.value, 0)}"),
                trading_enums.ExchangeConstantsPositionColumns.LEVERAGE.value:
                    decimal.Decimal(
                        f"{position_dict.get(trading_enums.ExchangePositionCCXTColumns.LEVERAGE.value, 0)}"),
                trading_enums.ExchangeConstantsPositionColumns.UNREALIZED_PNL.value:
                    decimal.Decimal(
                        f"{position_dict.get(trading_enums.ExchangePositionCCXTColumns.UNREALISED_PNL.value, 0)}"),
                trading_enums.ExchangeConstantsPositionColumns.REALISED_PNL.value:
                    decimal.Decimal(
                        f"{position_dict.get(trading_enums.ExchangePositionCCXTColumns.REALISED_PNL.value, 0)}"),
                trading_enums.ExchangeConstantsPositionColumns.LIQUIDATION_PRICE.value:
                    decimal.Decimal(
                        f"{position_dict.get(trading_enums.ExchangePositionCCXTColumns.LIQUIDATION_PRICE.value, 0)}"),
                trading_enums.ExchangeConstantsPositionColumns.MARK_PRICE.value:
                    decimal.Decimal(
                        f"{position_dict.get(trading_enums.ExchangePositionCCXTColumns.MARK_PRICE.value, 0)}"),
                trading_enums.ExchangeConstantsPositionColumns.ENTRY_PRICE.value:
                    decimal.Decimal(
                        f"{position_dict.get(trading_enums.ExchangePositionCCXTColumns.ENTRY_PRICE.value, 0)}"),
            })
        except KeyError as e:
            self.logger.error(f"Fail to parse position dict ({e})")
        return position_dict
