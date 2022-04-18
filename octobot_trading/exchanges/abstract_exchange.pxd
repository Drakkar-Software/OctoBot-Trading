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
cimport octobot_trading.util as util


cdef class AbstractExchange(util.Initializable):
    cdef public dict config

    cdef public object logger
    cdef public object current_account
    cdef public object trader
    cdef public object exchange_manager
    cdef public object connector

    cdef public set symbols
    cdef public set time_frames

    cdef public double allowed_time_lag

    cdef public str name
    cdef public bint is_unreachable

    cpdef str get_name(cls)

    # exchange requests
    cpdef dict get_market_status(self, str symbol, object price_example=*, bint with_fixer=*)
    cpdef dict get_trade_fee(self, str symbol, object order_type, object quantity, object price, str taker_or_maker)
    cpdef dict get_fees(self, str symbol)
    cpdef double get_uniform_timestamp(self, double timestamp)
    cpdef str get_pair_from_exchange(self, str pair)
    cpdef str get_exchange_pair(self, str pair)
    cpdef str get_pair_cryptocurrency(self, str pair)
    cpdef tuple get_split_pair_from_exchange(self, str pair)
    cpdef int get_rate_limit(self)
    cpdef dict get_default_balance(self)

    # exchange settings
    cpdef bint authenticated(self)
    cpdef int get_max_handled_pair_with_time_frame(self)

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

    # uniformization
    cpdef double get_exchange_current_time(self)
    cpdef object uniformize_candles_if_necessary(self, object candle_or_candles)
    cpdef object get_uniformized_timestamp(self, object candle_or_candles)
    cpdef long long get_candle_since_timestamp(self, object time_frame, int count)

    cdef object _uniformize_candles_timestamps(self, list candles)
    cdef void _uniformize_candle_timestamps(self, list candle)

    # utils
    cpdef void log_order_creation_error(self, object error, object order_type, str symbol, object quantity,
                                        object price, object stop_price)
    cpdef void handle_token_error(self, object error)
    cpdef bint is_supported_order_type(self, object order_type)
    cpdef bint supports_bundled_order_on_order_creation(self, object base_order, object bundled_order_type)
