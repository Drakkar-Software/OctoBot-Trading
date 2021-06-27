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
cimport octobot_trading.exchanges.abstract_websocket_exchange as abstract_websocket

cdef class CryptofeedWebsocketConnector(abstract_websocket.AbstractWebsocketExchange):
    cdef public dict callback_by_feed
    cdef public dict callbacks

    cdef public list filtered_pairs
    cdef public list filtered_timeframes

    cdef public object candle_callback
    cdef public object cryptofeed_exchange

    cpdef void start(self)
    cpdef void _set_async_callbacks(self)

    cdef void _subscribe_feeds(self)
    cdef bint _is_supported_pair(self, pair)
    cdef bint _is_supported_time_frame(self, object time_frame)
    cdef void _filter_exchange_pairs_and_timeframes(self)
    cdef void _filter_exchange_symbols(self)
    cdef void _filter_exchange_time_frames(self)
    cdef void _subscribe_candle_feed(self)
    cdef void _subscribe_all_pairs_feed(self)
    cdef bint _should_run_candle_feed(self)
    cdef void _remove_all_feeds(self)
    cdef void _remove_feed(self, object feed)
    cdef void _fix_signal_handler(self)
    cdef void _fix_logger(self)
    cdef list _convert_book_prices_to_orders(self, dict book_prices, str book_side)
