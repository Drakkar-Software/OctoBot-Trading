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

    cpdef str get_pair_from_exchange(self, str pair)
    cpdef str get_exchange_pair(self, str pair)
    cpdef void start(self)
    cpdef void _set_async_callbacks(self)

    cdef void subscribe_feeds(self)
    cdef void _filter_exchange_pairs_and_timeframes(self)
    cdef void _filter_exchange_symbols(self, object exchange)
    cdef void _filter_exchange_time_frames(self, object exchange)
    cdef void subscribe_candle_feed(self, list exchange_symbols)
