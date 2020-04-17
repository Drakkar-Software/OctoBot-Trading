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

from octobot_trading.channels.exchange_channel cimport ExchangeChannel
from octobot_trading.channels.exchange_channel cimport ExchangeChannelInternalConsumer, ExchangeChannelProducer


cdef class ModeChannelConsumer(ExchangeChannelInternalConsumer):
    pass

cdef class ModeChannelProducer(ExchangeChannelProducer):
    pass

cdef class ModeChannel(ExchangeChannel):
    cpdef object get_filtered_consumers(self, str trading_mode_name=*, str state =*, str cryptocurrency=*,
                                        str symbol=*, str time_frame=*)
