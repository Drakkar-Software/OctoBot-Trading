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
import typing

import octobot_commons.constants
import octobot_commons.enums as common_enums
import octobot_commons.logging as logging
import octobot_commons.timestamp_util as timestamp_util

import octobot_trading.constants
import octobot_trading.enums as enums
import octobot_trading.util as util


class AbstractExchange(util.Initializable):
    BUY_STR = enums.TradeOrderSide.BUY.value
    SELL_STR = enums.TradeOrderSide.SELL.value

    # order that should be self managed by OctoBot
    # can be override locally to match exchange support
    UNSUPPORTED_ORDERS = [enums.TraderOrderType.STOP_LOSS,
                          enums.TraderOrderType.STOP_LOSS_LIMIT,
                          enums.TraderOrderType.TAKE_PROFIT,
                          enums.TraderOrderType.TAKE_PROFIT_LIMIT,
                          enums.TraderOrderType.TRAILING_STOP,
                          enums.TraderOrderType.TRAILING_STOP_LIMIT]

    ACCOUNTS = {}

    def __init__(self, config, exchange_manager):
        super().__init__()
        self.config = config
        self.exchange_manager = exchange_manager
        self.connector = None

        # Initialized when initializing exchange connector
        self.symbols = set()
        self.time_frames = set()

        # exchange name related attributes
        self.name = self.exchange_manager.exchange_class_string
        self.logger = logging.get_logger(f"{self.__class__.__name__}[{self.name}]")

        # exchange related constants
        self.allowed_time_lag = octobot_trading.constants.DEFAULT_EXCHANGE_TIME_LAG
        self.current_account = enums.AccountTypes.CASH

    async def initialize_impl(self):
        """
        Contains the exchange initialization code
        """
        raise NotImplementedError("initialize_impl not implemented")

    async def stop(self) -> None:
        """
        Implement the exchange stopping process
        """
        raise NotImplementedError("stop not implemented")

    @classmethod
    def get_name(cls) -> str:
        """
        :return: the exchange name
        """
        raise NotImplementedError("get_name is not implemented")

    @classmethod
    def is_simulated_exchange(cls) -> bool:
        """
        :return: True if this implementation corresponds to a simulated exchange
        """
        return False

    def authenticated(self) -> bool:
        return self.connector.is_authenticated

    @classmethod
    def is_default_exchange(cls) -> bool:
        """
        :return: True if this implementation corresponds to a default exchange implementation
        """
        return False

    @classmethod
    def is_supporting_exchange(cls, exchange_candidate_name) -> bool:
        """
        :param exchange_candidate_name: the exchange name
        :return: True if this implementation supports the exchange name
        """
        raise NotImplementedError("is_supporting_exchange is not implemented")

    @classmethod
    def is_supporting_sandbox(cls) -> bool:
        """
        :return: True if the exchange is supporting sandbox mode
        """
        return True

    def get_exchange_current_time(self):
        """
        :return: the exchange current time in seconds
        """
        raise NotImplementedError("get_exchange_current_time is not implemented")

    def get_uniform_timestamp(self, timestamp):
        """
        :param timestamp: the timestamp to uniformize
        :return: the uniformized timestamp
        """
        raise NotImplementedError("get_uniform_timestamp not implemented")

    def get_market_status(self, symbol, price_example=None, with_fixer=True):
        """
        Return the market status
        :param symbol: the symbol
        :param price_example: a price example to be used in MarketStatusFixer
        :param with_fixer: when True, return a new instance of MarketStatusFixer
        :return: market status dict
        """
        raise NotImplementedError("get_market_status is not implemented")

    async def get_balance(self, **kwargs: dict):
        """
        :return: current user balance from exchange
        """
        raise NotImplementedError("get_balance is not implemented")

    async def get_symbol_prices(self,
                                symbol: str,
                                time_frame: common_enums.TimeFrames,
                                limit: int = None,
                                **kwargs: dict) -> typing.Optional[list]:
        """
        Return the candle history
        :param symbol: the symbol
        :param time_frame: the timeframe
        :param limit: the history limit size
        :return: the symbol candle history
        """
        raise NotImplementedError("get_symbol_prices is not implemented")

    async def get_kline_price(self,
                              symbol: str,
                              time_frame: common_enums.TimeFrames,
                              **kwargs: dict) -> typing.Optional[list]:
        """
        Return the symbol current kline dict
        :param symbol: the symbol
        :param time_frame: the timeframe
        :return: the symbol current klint
        """
        raise NotImplementedError("get_symbol_prices is not implemented")

    async def get_order_book(self, symbol: str, limit: int = 5, **kwargs: dict) -> typing.Optional[dict]:
        """
        Return the current symbol order book snapshot
        :param symbol: the symbol
        :param limit: the order book size
        :return: the order book snapshot
        """
        raise NotImplementedError("get_order_book is not implemented")

    async def get_recent_trades(self, symbol: str, limit: int = 50, **kwargs: dict) -> typing.Optional[list]:
        """
        Return the last "limit" recent trades for the specified symbol
        :param symbol: the symbol
        :param limit: the recent trade history size
        :return: the recent trade history for the symbol
        """
        raise NotImplementedError("get_recent_trades is not implemented")

    async def get_price_ticker(self, symbol: str, **kwargs: dict) -> typing.Optional[dict]:
        """
        Get the symbol ticker from the exchange
        :param symbol: the symbol
        :return: the symbol ticker
        """
        raise NotImplementedError("get_price_ticker is not implemented")

    async def get_all_currencies_price_ticker(self, **kwargs: dict) -> typing.Optional[list]:
        """
        Get all exchange currency tickers
        :return: the list of exchange currencies tickers
        """
        raise NotImplementedError("get_all_currencies_price_ticker is not implemented")

    async def get_order(self, order_id: str, symbol: str = None, **kwargs: dict) -> dict:
        """
        Get the order data from the exchange
        :param order_id: the order id
        :param symbol: the order symbol
        :return: the order data
        """
        raise NotImplementedError("get_order is not implemented")

    async def get_all_orders(self, symbol: str = None, since: int = None,
                             limit: int = None, **kwargs: dict) -> list:
        """
        Get the current user order list
        :param symbol: the order symbol
        :param since: the starting timestamp
        :param limit: the list limit size
        :return: the user order list
        """
        raise NotImplementedError("get_all_orders is not implemented")

    async def get_open_orders(self, symbol: str = None, since: int = None,
                              limit: int = None, **kwargs: dict) -> list:
        """
        Get the current user open order list
        :param symbol: the order symbol
        :param since: the starting timestamp
        :param limit: the list limit size
        :return: the user open order list
        """
        raise NotImplementedError("get_open_orders is not implemented")

    async def get_closed_orders(self, symbol: str = None, since: int = None,
                                limit: int = None, **kwargs: dict) -> list:
        """
        Get the user closed order list
        :param symbol: the order symbol
        :param since: the starting timestamp
        :param limit: the list limit size
        :return: the user closed order list
        """
        raise NotImplementedError("get_closed_orders is not implemented")

    async def get_my_recent_trades(self, symbol: str = None, since: int = None,
                                   limit: int = None, **kwargs: dict) -> list:
        """
        Get the user recent trades
        :param symbol: trades symbol
        :param since: the trade history starting timestamp
        :param limit: the history limit size
        :return: the user trades history list
        """
        raise NotImplementedError("get_my_recent_trades is not implemented")

    async def cancel_order(self, order_id: str, symbol: str = None, **kwargs: dict) -> bool:
        """
        Cancel a order on the exchange
        :param order_id: the order id
        :param symbol: the order symbol
        :return: True if the order is successfully cancelled
        """
        raise NotImplementedError("cancel_order is not implemented")

    async def create_order(self, order_type: enums.TraderOrderType, symbol: str, quantity: float,
                           price: float = None, stop_price=None, params: dict = None, **kwargs: dict) -> dict:
        """
        Create a order on the exchange
        :param order_type: the order type
        :param symbol: the order symbol
        :param quantity: the order quantity
        :param price: the order price
        :param stop_price: the order stop price
        :param params: the order request params
        :return: the created order dict
        """
        raise NotImplementedError("create_order is not implemented")

    def is_supported_order_type(self, order_type):
        """
        Check if the order type is supported by the current exchange instance
        Should be used to know if we should simulate this order or create it on the exchange
        :param order_type: the order type, should be a member of enums.TraderOrderType
        :return: True if the order type is supported by the exchange, else False
        """
        return order_type not in self.UNSUPPORTED_ORDERS

    def get_trade_fee(self, symbol, order_type, quantity, price, taker_or_maker):
        """
        Calculates fees resulting to a trade
        :param symbol: the symbol
        :param order_type: the order type
        :param quantity: the trade quantity
        :param price: the trade price
        :param taker_or_maker: if the trade was taker or maker
        :return: the trade fees
        """
        raise NotImplementedError("get_trade_fee is not implemented")

    def get_fees(self, symbol):
        """
        :param symbol: the symbol
        :return: the symbol fees dict
        """
        raise NotImplementedError("get_fees is not implemented")

    def get_pair_from_exchange(self, pair) -> str:
        """
        :param pair: the pair
        :return: the symbol associated to the pair
        """
        raise NotImplementedError("get_pair_from_exchange is not implemented")

    def get_split_pair_from_exchange(self, pair) -> (str, str):
        """
        :param pair: the pair
        :return: the currency, market tuple associated to the pair
        """
        raise NotImplementedError("get_split_pair_from_exchange is not implemented")

    def get_exchange_pair(self, pair) -> str:
        """
        :param pair: the pair
        :return: the exchange pair from an uniformized symbol
        """
        raise NotImplementedError("get_exchange_pair is not implemented")

    def get_pair_cryptocurrency(self, pair) -> str:
        """
        :param pair: the pair
        :return: the currency associated to the input pair
        """
        raise NotImplementedError("get_pair_cryptocurrency is not implemented")

    def get_default_balance(self):
        """
        :return: the default balance dict from exchange
        """
        raise NotImplementedError("get_default_balance is not implemented")

    def get_rate_limit(self):
        """
        :return: the exchange rate limit
        """
        raise NotImplementedError("get_default_balance is not implemented")

    async def switch_to_account(self, account_type: enums.AccountTypes):
        """
        Request to switch account from exchange
        :param account_type: the account destination
        """
        raise NotImplementedError("switch_to_account is not available on this exchange")

    async def get_sub_account_list(self):
        """
        :return: the exchange sub account list if supported by the exchange
        """
        raise NotImplementedError("get_sub_account_list is not available on this exchange")

    """
    Parsers
    """

    def parse_balance(self, balance):
        """
        :param balance: the balance dict
        :return: the uniformized balance dict
        """
        raise NotImplementedError("parse_balance is not implemented")

    def parse_trade(self, trade):
        """
        :param trade: the trade dict
        :return: the uniformized trade dict
        """
        raise NotImplementedError("parse_trade is not implemented")

    def parse_order(self, order):
        """
        :param order: the order dict
        :return: the uniformized order dict
        """
        raise NotImplementedError("parse_order is not implemented")

    def parse_ticker(self, ticker):
        """
        :param ticker: the ticker dict
        :return: the uniformized ticker dict
        """
        raise NotImplementedError("parse_ticker is not implemented")

    def parse_ohlcv(self, ohlcv):
        """
        :param ohlcv: the ohlcv dict
        :return: the uniformized ohlcv dict
        """
        raise NotImplementedError("parse_ohlcv is not implemented")

    def parse_order_book(self, order_book):
        """
        :param order_book: the order book data
        :return: the uniformized order book data
        """
        raise NotImplementedError("parse_order_book is not implemented")

    def parse_order_book_ticker(self, order_book_ticker):
        """
        :param order_book_ticker: the order book ticker
        :return: the uniformized order book ticker
        """
        raise NotImplementedError("parse_order_book_ticker is not implemented")

    def parse_timestamp(self, data_dict, timestamp_key, default_value=None, ms=False):
        """
        Uniformize a raw timestamp from an input dict
        :param data_dict: the input dict
        :param timestamp_key: the timestamp dict in the input dict
        :param default_value: the default timestamp value
        :param ms: when True, return the timestamp in milliseconds
        :return: the uniformized timestamp
        """
        raise NotImplementedError("parse_timestamp is not implemented")

    def parse_currency(self, currency):
        """
        :param currency: the raw currency
        :return: the uniformized currency
        """
        raise NotImplementedError("parse_currency is not implemented")

    def parse_order_id(self, order):
        """
        :param order: the order dict
        :return: the order id
        """
        raise NotImplementedError("parse_order_id is not implemented")

    def parse_order_symbol(self, order):
        """
        :param order: the order dict
        :return: the order symbol
        """
        raise NotImplementedError("parse_order_symbol is not implemented")

    def parse_status(self, status):
        """
        :param status: the raw status
        :return: the OrderStatus instance related to the row status
        """
        raise NotImplementedError("parse_status is not implemented")

    def parse_side(self, side):
        """
        :param side: the raw side
        :return: the TradeOrderSide related to the side
        """
        raise NotImplementedError("parse_side is not implemented")

    def parse_account(self, account):
        """
        :param account: the raw account
        :return: the AccountTypes related to the account
        """
        raise NotImplementedError("parse_account is not implemented")

    """
    Cleaners
    """

    def clean_recent_trade(self, recent_trade):
        """
        Clean the specified recent trade list
        :param recent_trade: the recent trade list
        :return: the cleaned recent trade list
        """
        raise NotImplementedError("clean_recent_trade is not implemented")

    def clean_trade(self, trade):
        """
        Clean the specified trade dict
        :param trade: the trade dict
        :return: the cleaned trade dict
        """
        raise NotImplementedError("clean_trade is not implemented")

    def clean_order(self, order):
        """
        Clean the specified order dict
        :param order: the order dict
        :return: the cleaned order dict
        """
        raise NotImplementedError("clean_order is not implemented")

    """
    Uniformization
    """

    def need_to_uniformize_timestamp(self, timestamp):
        """
        Return True if the timestamp should be uniformized
        :param timestamp: the timestamp to check
        :return: True if the timestamp should be uniformized
        """
        return not timestamp_util.is_valid_timestamp(timestamp)

    def get_uniformized_timestamp(self, timestamp):
        """
        Uniformize a timestamp
        :param timestamp: the timestamp to uniform
        :return: the timestamp uniformized
        """
        if self.need_to_uniformize_timestamp(timestamp):
            return self.get_uniform_timestamp(timestamp)
        return timestamp

    def uniformize_candles_if_necessary(self, candle_or_candles):
        """
        Uniform timestamps of a list of candles or a candle
        :param candle_or_candles: a list of candles or a candle to be uniformized
        :return: the list of candles or the candle uniformized
        """
        if candle_or_candles:  # TODO improve
            if isinstance(candle_or_candles[0], list):
                if self.need_to_uniformize_timestamp(
                        candle_or_candles[0][common_enums.PriceIndexes.IND_PRICE_TIME.value]):
                    self._uniformize_candles_timestamps(candle_or_candles)
            else:
                if self.need_to_uniformize_timestamp(candle_or_candles[common_enums.PriceIndexes.IND_PRICE_TIME.value]):
                    self._uniformize_candle_timestamps(candle_or_candles)
        return candle_or_candles

    def _uniformize_candles_timestamps(self, candles):
        """
        Uniformize a list candle timestamps
        :param candles: the list of candles to uniformize
        """
        for candle in candles:
            self._uniformize_candle_timestamps(candle)

    def _uniformize_candle_timestamps(self, candle):
        """
        Uniformize a candle timestamp
        :param candle: the candle to uniformize
        """
        candle[common_enums.PriceIndexes.IND_PRICE_TIME.value] = \
            self.get_uniform_timestamp(candle[common_enums.PriceIndexes.IND_PRICE_TIME.value])

    def get_candle_since_timestamp(self, time_frame, count):
        """
        :param time_frame: the time frame to use
        :param count: the number of candle
        :return: the timestamp since "count" candles
        """
        return self.get_exchange_current_time() - (common_enums.TimeFramesMinutes[time_frame]
                                                   * octobot_commons.constants.MSECONDS_TO_MINUTE
                                                   * count)

    def get_max_handled_pair_with_time_frame(self) -> int:
        """
        :return: the maximum number of simultaneous pairs * time_frame that this exchange can handle.
        """
        return self.connector.get_max_handled_pair_with_time_frame()

    def log_order_creation_error(self, error, order_type, symbol, quantity, price, stop_price):
        order_desc = f"order_type: {order_type}, symbol: {symbol}, quantity: {str(quantity)}, price: {str(price)}," \
                     f" stop_price: {str(stop_price)}"
        self.logger.error(f"Failed to create order : {error.__class__.__name__} {error}: ({order_desc})")

    def handle_token_error(self, error):
        self.logger.error(f"Exchange configuration is invalid : please check your configuration ! "
                          f"({error.__class__.__name__}: {error})")
