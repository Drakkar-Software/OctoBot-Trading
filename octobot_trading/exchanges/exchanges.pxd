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
cimport octobot_commons.singleton as singleton
cimport octobot_trading.exchanges.exchange_manager as trading_exchanges

cdef class ExchangeConfiguration(object):
    cdef public trading_exchanges.ExchangeManager exchange_manager

    cdef public str exchange_name
    cdef public str id
    cdef public str matrix_id

    cdef public dict symbols_by_crypto_currencies
    cdef public list symbols
    cdef public list real_time_time_frames
    cdef public list available_required_time_frames


cdef class Exchanges(singleton.Singleton):
    cdef public dict exchanges

    cpdef void add_exchange(self, trading_exchanges.ExchangeManager exchange_manager, str matrix_id)
    cpdef ExchangeConfiguration get_exchange(self, str exchange_name, str exchange_manager_id)
    cpdef dict get_exchanges(self, str exchange_name)
    cpdef list get_all_exchanges(self)
    cpdef list get_exchanges_list(self, str exchange_name)
    cpdef void del_exchange(self, str exchange_name, str exchange_manager_id, bint should_warn=*)
