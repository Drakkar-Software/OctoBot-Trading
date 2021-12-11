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
cimport octobot_trading.personal_data.positions.channel.positions as positions_channel

cimport octobot_commons.async_job as async_job

cdef class PositionsUpdater(positions_channel.PositionsProducer):
    cdef public bint should_use_position_per_symbol

    cdef async_job.AsyncJob position_update_job

    cdef bint _should_run(self)
    cdef bint _should_push_mark_price(self)
    cdef bint _has_mark_price_in_position(self)
