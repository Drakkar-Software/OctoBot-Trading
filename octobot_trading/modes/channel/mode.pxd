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
cimport octobot_trading.exchange_channel as exchanges_channel

cdef class ModeChannelConsumer(exchanges_channel.ExchangeChannelInternalConsumer):
    pass

cdef class ModeChannelProducer(exchanges_channel.ExchangeChannelProducer):
    pass

cdef class ModeChannel(exchanges_channel.ExchangeChannel):
    cpdef object get_filtered_consumers(self, str trading_mode_name=*, str state =*, str cryptocurrency=*,
                                        str symbol=*, str time_frame=*)
