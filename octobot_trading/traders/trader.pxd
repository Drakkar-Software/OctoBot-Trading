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


""" Order class will represent an open order in the specified exchange
In simulation it will also define rules to be filled / canceled
It is also use to store creation & fill values of the order """
from octobot_trading.data.order cimport Order
from octobot_trading.exchanges.data.exchange_personal_data cimport ExchangePersonalData
from octobot_trading.exchanges.exchange_manager cimport ExchangeManager
from octobot_trading.util.initializable cimport Initializable


cdef class Trader(Initializable):
    cdef dict config

    cdef public float risk

    cdef public str trader_type_str

    cdef public bint simulate
    cdef public bint is_enabled
    cdef public bint loaded_previous_state

    cdef public object notifier
    cdef public object logger
    cdef public object previous_state_manager

    cdef public ExchangeManager exchange_manager
    cdef public ExchangePersonalData exchange_personal_data

    # methods
    cdef void _load_previous_state_if_any(self)
    cdef str _parse_order_id(self, str order_id)

    @staticmethod
    cdef bint enabled(dict config)

    cpdef float set_risk(self, float risk)
    cpdef Order create_order_instance(self,
                                      object order_type,
                                      str symbol,
                                      float current_price,
                                      float quantity,
                                      float price=*,
                                      float stop_price=*,
                                      object linked_to=*,
                                      object status=*,
                                      str order_id=*,
                                      float quantity_filled=*,
                                      float timestamp=*,
                                      object linked_portfolio=*)