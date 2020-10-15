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
cimport async_channel.channels as channel 
cimport async_channel.consumer as consumer
cimport async_channel.producer as producer

cdef class ExchangeChannel(channel.Channel):
    cdef public object exchange_manager
    cdef public object exchange

    cdef int filter_send_counter
    cdef bint should_send_filter

    cpdef object get_filtered_consumers(self, str cryptocurrency=*, str symbol=*)

cdef class TimeFrameExchangeChannel(ExchangeChannel):
    cpdef object get_filtered_consumers(self, str cryptocurrency=*, str symbol=*, str time_frame=*)

cdef class ExchangeChannelConsumer(consumer.Consumer):
    pass

cdef class ExchangeChannelProducer(producer.Producer):
    cpdef void trigger_single_update(self)

cdef class ExchangeChannelInternalConsumer(consumer.InternalConsumer):
    pass

cdef class ExchangeChannelSupervisedConsumer(consumer.SupervisedConsumer):
    pass

cpdef ExchangeChannel get_chan(str chan_name, str exchange_id)
cpdef dict get_exchange_channels(str exchange_id)
cpdef void set_chan(ExchangeChannel chan, str name)
cpdef void del_exchange_channel_container(str exchange_id)
cpdef void del_chan(str name, str exchange_id)
