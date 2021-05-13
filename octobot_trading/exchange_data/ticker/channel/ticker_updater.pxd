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
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
cimport octobot_trading.exchange_data.ticker.channel.ticker as ticker_channel

cdef class TickerUpdater(ticker_channel.TickerProducer):
    cdef list _added_pairs
    cdef bint is_fetching_future_data
    cdef int refresh_time

    cdef dict _cleanup_ticker_dict(self, dict ticker)
    cdef list _get_pairs_to_update(self)
    cdef bint _should_use_future(self)
    cdef void _update_refresh_time(self)
