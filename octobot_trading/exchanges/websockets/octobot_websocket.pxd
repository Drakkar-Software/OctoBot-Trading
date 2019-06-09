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
from octobot_websockets.feeds.feed cimport Feed
from octobot_trading.exchanges.websockets.abstract_websocket cimport AbstractWebsocket


cdef class OctoBotWebSocketClient(AbstractWebsocket):
    cdef public str exchange_name

    cdef public list octobot_websockets
    cdef public list octobot_websockets_t
    cdef public list trader_pairs
    cdef public list time_frames
    cdef public list channels

    cdef public object octobot_websockets_executors
    cdef public object exchange_class

    cdef public dict open_sockets_keys
    cdef public dict callbacks

    cdef public bint is_handling_ohlcv
    cdef public bint is_handling_price_ticker
    cdef public bint is_handling_order_book
    cdef public bint is_handling_recent_trades
    cdef public bint is_handling_funding

    # private
    cdef bint _is_feed_available(self, Feed feed)
    cdef void _add_feed_and_run_if_required(self, list feed, object callback)
    cdef void _create_octobot_feed_feeds(self)

    @staticmethod
    cdef object _convert_seconds_to_time_frame(int time_frame_seconds)

    @staticmethod
    cdef int _convert_time_frame_minutes_to_seconds(object time_frame)

    # public
    cpdef void init_web_sockets(self, list time_frames, list trader_pairs)
    cpdef void add_recent_trade_feed(self)
    cpdef void add_order_book_feed(self)
    cpdef void add_tickers_feed(self)
    cpdef void start_sockets(self)
    cpdef void close_and_restart_sockets(self)
    cpdef void stop_sockets(self)
    cpdef bint handles_order_book(self)
    cpdef bint handles_price_ticker(self)
    cpdef bint handles_funding(self)
    cpdef bint handles_ohlcv(self)
    cpdef bint handles_balance(self)
    cpdef bint handles_orders(self)
