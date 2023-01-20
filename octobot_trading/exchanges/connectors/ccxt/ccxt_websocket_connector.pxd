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
cimport octobot_trading.exchanges.abstract_websocket_exchange as abstract_websocket_exchange

cdef class CCXTWebsocketConnector(abstract_websocket_exchange.AbstractWebsocketExchange):
    cdef public list filtered_pairs
    cdef public list watched_pairs
    cdef public object min_timeframe
    cdef dict _previous_open_candles
    cdef dict _subsequent_unordered_candles_count
    cdef object _start_time_millis
    cdef str websocket_name

    cdef public object local_loop

    cdef public bint should_stop
    cdef public bint is_authenticated
    cdef public object adapter
    cdef public object additional_config
    cdef public dict headers
    cdef public dict options
    cdef public dict feed_tasks
    cdef public object _reconnect_task
    cdef public double _last_close_time
    cdef public double throttled_ws_updates

    # return object when an exception might be thrown
    cpdef object add_headers(self, dict headers_dict)
    cpdef object add_options(self, dict options_dict)

    cdef object _create_client(self)
    cdef bint _has_authenticated_channel(self)
    cdef bint _is_authenticated_feed(self, object feed)
    cdef object _subscribe_feeds(self)
    cdef bint _should_use_authenticated_feeds(self)
    cdef bint _is_supported_channel(self, object channel)
    cdef object _subscribe_candle_feed(self)
    cdef object _subscribe_channels_feeds(self, bint pairs_related_channels_only)
    cdef object _subscribe_pair_independent_feed(self)
    cdef object _subscribe_traded_pairs_feed(self)
    cdef object _subscribe_watched_pairs_feed(self)
    cdef dict _get_feed_generator_by_feed(self)
    cdef object _get_generator(self, str method_name)
    cdef dict _get_callback_by_feed(self)
    cdef object _get_since_filter_value(self, object feed, str time_frame)
    cdef object _subscribe_feed(self, object feed, list symbols=*, str time_frame=*,
                                object since=*, object limit=*, object params=*)
    cdef str _get_feed_identifier(self, object feed_generator, dict kwargs)
    cdef object _filter_exchange_pairs_and_timeframes(self)
    cdef object _add_pair(self, str pair, bint watching_only)
    cdef object _add_exchange_symbols(self)
    cdef object _filter_exchange_symbols(self)
    cdef object _add_time_frame(self, list filtered_timeframes, object time_frame, bint log_on_error)
    cdef object _init_exchange_time_frames(self)
    cdef bint _should_run_candle_feed(self)
    cdef bint _is_supported_pair(self, str pair)
    cdef bint _is_supported_time_frame(self, object time_frame)
    cdef bint _is_pair_independent_feed(self, object feed)
    cdef list _convert_book_prices_to_orders(self, object book_prices_and_volumes, str book_side)
    cdef void _register_previous_open_candle(self, str time_frame, str symbol, list candle)
    cdef list _get_previous_open_candle(self, str time_frame, str symbol)
    cdef void _register_subsequent_unordered_candle(self, str time_frame, str symbol, object parsed_timeframe, double current_candle_time)
    cdef int _get_subsequent_unordered_candles_count(self, str time_frame, str symbol)
