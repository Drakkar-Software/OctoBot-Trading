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
    cdef public list watched_pairs
    cdef public list filtered_timeframes

    cdef public object min_timeframe
    cdef public object candle_callback
    cdef public object cryptofeed_exchange
    cdef public object client_logger
    cdef public object client_config

    cdef public object local_loop
    cdef public bint is_websocket_restarting

    cpdef void start(self)
    cpdef void _set_async_callbacks(self)

    cdef void _create_client(self)
    cdef void _create_client_config(self)
    cdef dict _get_credentials_config(self)
    cdef void _init_client(self)
    cdef void _start_client(self, bint should_create_loop=*)
    cdef bint _should_use_authenticated_feeds(self)
    cdef void _subscribe_feeds(self)
    cdef void _add_pair(self, str pair, bint watching_only)
    cdef void _add_time_frame(self, object time_frame)
    cdef void _subscribe_feeds(self)
    cdef bint _is_supported_channel(self, str channel)
    cdef bint _is_supported_pair(self, pair)
    cdef bint _is_supported_time_frame(self, object time_frame)
    cdef bint _is_pair_independent_feed(self, feed)
    cdef void _subscribe_feed(self, list channels, dict callbacks, list symbols=*, str candle_interval=*)
    cdef void _filter_exchange_pairs_and_timeframes(self)
    cdef void _filter_exchange_symbols(self)
    cdef void _filter_exchange_time_frames(self)
    cdef void _subscribe_candle_feed(self)
    cdef void _subscribe_channels_feeds(self)
    cdef void _subscribe_traded_pairs_feed(self)
    cdef void _subscribe_pair_independent_feed(self)
    cdef void _subscribe_watched_pairs_feed(self)
    cdef bint _should_run_candle_feed(self)
    cdef void _remove_all_feeds(self)
    cdef void _remove_feed(self, object feed)
    cdef void _fix_signal_handler(self)
    cdef void _fix_logger(self)
    cdef list _convert_book_prices_to_orders(self, dict book_prices, str book_side)
    cdef str _parse_order_type(self, str raw_order_type)
    cdef str _parse_order_status(self, str raw_order_status)
    cdef str _parse_order_side(self, str raw_order_side)
