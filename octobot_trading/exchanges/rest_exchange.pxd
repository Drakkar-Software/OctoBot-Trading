# cython: language_level=3
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
#  Lesser General License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
from octobot_trading.exchanges.abstract_exchange cimport AbstractExchange

cdef class RestExchange(AbstractExchange):
    cdef public bint is_authenticated
    cdef public bint is_sandboxed

    cdef object all_currencies_price_ticker
    cdef public object client

    cdef public object current_account

    # private
    cdef void _create_client(self)
    cdef void _log_error(self, object error, object order_type, str symbol, double quantity, double price, double stop_price)

    # @staticmethod TODO
    # cdef bint _ensure_order_details_completeness(object order, list order_required_fields=*)

    @staticmethod
    cdef str _get_side(object order_type)

    # public
    cpdef get_market_status(self, str symbol, object price_example=*, bint with_fixer=*)
    cpdef dict get_trade_fee(self, str symbol, object order_type, double quantity, double price, str taker_or_maker)
    cpdef dict get_fees(self, str symbol)
    cpdef double get_uniform_timestamp(self, double timestamp)
    cpdef str get_pair_from_exchange(self, str pair)
    cpdef str get_exchange_pair(self, str pair)
    cpdef str get_pair_cryptocurrency(self, str pair)
    cpdef tuple get_split_pair_from_exchange(self, str pair)
    cpdef dict get_default_balance(self)
    cpdef void set_sandbox_mode(self, bint is_sandboxed)
    cpdef long long get_candle_since_timestamp(self, object time_frame, int count)

    # parsers
    cpdef dict parse_balance(self, dict balance)
    cpdef dict parse_trade(self, dict trade)
    cpdef dict parse_order(self, dict order)
    cpdef dict parse_ticker(self, dict ticker)
    cpdef dict parse_ohlcv(self, dict ohlcv)
    cpdef dict parse_order_book(self, dict order_book)
    cpdef dict parse_order_book_ticker(self, dict order_book_ticker)
    cpdef double parse_timestamp(self, dict data_dict, str timestamp_key, object default_value=*, bint ms=*)
    cpdef str parse_currency(self, str currency)
    cpdef str parse_order_id(self, dict order)
    cpdef object parse_status(self, str status)
    cpdef object parse_side(self, str side)
    cpdef object parse_account(self, str account)

    # cleaners
    cpdef dict clean_recent_trade(self, dict recent_trade)
    cpdef dict clean_trade(self, dict trade)
    cpdef dict clean_order(self, dict order)
