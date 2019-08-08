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
from octobot_channels.channels.channel cimport Channel, Channels
from octobot_channels.consumer cimport Consumer
from octobot_channels.producer cimport Producer

from octobot_trading.exchanges.abstract_exchange cimport AbstractExchange
from octobot_trading.exchanges.exchange_manager cimport ExchangeManager

cdef class ExchangeChannel(Channel):
    cdef public ExchangeManager exchange_manager
    cdef public AbstractExchange exchange

    cdef int filter_send_counter
    cdef bint should_send_filter

    cdef void _add_new_consumer_and_run(self, ExchangeChannelConsumer consumer, str symbol =*, bint with_time_frame =*)

    cpdef void will_send(self)
    cpdef void has_send(self)
    cpdef void new_consumer(self, object callback, int size=*, str symbol=*, bint filter_size=*)
    cpdef object get_consumers(self, str symbol=*)
    cpdef list get_consumers_by_timeframe(self, object time_frame, str symbol)

cdef class ExchangeChannelConsumer(Consumer):
    pass

cdef class ExchangeChannelProducer(Producer):
    pass

cdef class ExchangeChannels(Channels):
    pass
