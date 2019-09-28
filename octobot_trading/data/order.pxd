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
from octobot_trading.data.portfolio cimport Portfolio
from octobot_trading.exchanges.exchange_manager cimport ExchangeManager
from octobot_trading.traders.trader cimport Trader

cdef class Order:
    cdef public Trader trader
    cdef public ExchangeManager exchange_manager

    cdef public object side # TradeOrderSide
    cdef public object status # OrderStatus
    cdef public object order_type # TraderOrderType
    cdef public object taker_or_maker # ExchangeConstantsMarketPropertyColumns
    cdef public object lock # Lock

    cdef public Order linked_to
    cdef public Portfolio linked_portfolio

    cdef public bint is_simulated
    cdef public bint is_from_this_octobot

    cdef public str symbol
    cdef public str currency
    cdef public str market
    cdef public str order_id

    cdef public float origin_price
    cdef public float origin_stop_price
    cdef public float origin_quantity
    cdef public float market_total_fees
    cdef public float filled_quantity
    cdef public float filled_price
    cdef public float total_cost
    cdef public float timestamp
    cdef public float creation_time
    cdef public float canceled_time
    cdef public float executed_time
    cdef public float created_last_price
    cdef public float order_profitability

    cdef public dict fee # Dict[str, Union[str, float]]

    cdef list last_prices
    cdef public list linked_orders

    cpdef bint update(self,
            str symbol,
            str order_id=*,
            object status=*,
            float current_price=*,
            float quantity=*,
            float price=*,
            float stop_price=*,
            float quantity_filled=*,
            float filled_price=*,
            float fee=*,
            float total_cost=*,
            object timestamp=*,
            object linked_to=*,
            object linked_portfolio=*,
            object order_type=*)

    cdef void __update_type_from_raw(self, dict raw_order)
    cdef void __update_taker_maker_from_raw(self)
    cdef str to_string(self)

    cpdef bint check_last_prices(self, list last_prices, float price_to_check, bint inferior, bint simulated_time=*)
    cpdef tuple get_currency_and_market(self)
    cpdef float get_total_fees(self, str currency)
    cpdef bint is_filled(self)
    cpdef bint is_cancelled(self)
    cpdef dict get_computed_fee(self, object forced_value=*)
    cpdef float get_profitability(self)
    cpdef float generate_executed_time(self, bint simulated_time=*)
    cpdef bint is_self_managed(self)
    cpdef bint update_from_raw(self, dict raw_order)

