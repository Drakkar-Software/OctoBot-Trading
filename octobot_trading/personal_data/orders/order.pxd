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
cimport octobot_trading.util as util
cimport octobot_trading.personal_data.orders.order_state as orders_states

cdef class Order(util.Initializable):
    cdef public object trader
    cdef public object exchange_manager

    cdef public object side # TradeOrderSide
    cdef public object status # OrderStatus
    cdef public object order_type # TraderOrderType
    cdef public object lock # Lock

    cdef public orders_states.OrderState state

    cdef public bint is_synchronized_with_exchange
    cdef public bint is_from_this_octobot
    cdef public bint simulated
    cdef public bint reduce_only
    cdef public bint close_position

    cdef public bint created
    cdef public str symbol
    cdef public str currency
    cdef public str market
    cdef public str quantity_currency
    cdef public str taker_or_maker
    cdef public str order_id
    cdef public str logger_name
    cdef public str tag

    cdef readonly str shared_signal_order_id

    cdef public object origin_price
    cdef public object origin_stop_price
    cdef public object origin_quantity
    cdef public object filled_quantity
    cdef public object filled_price
    cdef public object total_cost
    cdef public object created_last_price
    cdef public object order_profitability
    cdef public object position_side

    cdef public object order_group

    cdef public double timestamp
    cdef public double creation_time
    cdef public double canceled_time
    cdef public double executed_time

    cdef public dict fee # Dict[str, Union[str, decimal.Decimal]]
    cdef public object fees_currency_side   # trading_enums.FeesCurrencySide

    cdef list last_prices
    cdef public list chained_orders # List[Order]
    cdef public object triggered_by # Order
    cdef public bint has_been_bundled
    cdef public bint is_waiting_for_chained_trigger
    cdef public dict exchange_creation_params
    cdef public dict trader_creation_kwargs


    cdef public object exchange_order_type # raw exchange order type, used to create order dict

    cpdef bint update(self,
            str symbol,
            str order_id=*,
            object status=*,
            object current_price=*,
            object quantity=*,
            object price=*,
            object stop_price=*,
            object quantity_filled=*,
            object filled_price=*,
            object average_price=*,
            dict fee=*,
            object total_cost=*,
            object timestamp=*,
            object order_type=*,
            object reduce_only=*,
            object close_position=*,
            object position_side=*,
            object fees_currency_side=*,
            object group=*,
            str tag=*,
            str quantity_currency=*)
    cdef object _update_type_from_raw(self, dict raw_order)  # return object to allow exception raising
    cdef void _update_taker_maker(self)
    cdef object _on_origin_price_change(self, object previous_price, object price_time)

    cpdef str to_string(self)
    cpdef object get_total_fees(self, str currency)
    cpdef bint is_created(self)
    cpdef bint is_open(self)
    cpdef bint is_filled(self)
    cpdef bint is_cancelled(self)
    cpdef bint is_closed(self)
    cpdef bint is_long(self)
    cpdef bint is_short(self)
    cpdef bint is_refreshing(self)
    cpdef bint can_be_edited(self)
    cpdef object get_position_side(self, object future_contract)
    cpdef void on_fill_actions(self)
    cpdef dict get_computed_fee(self, object forced_value=*)
    cpdef object get_profitability(self)
    cpdef double generate_executed_time(self)
    cpdef bint is_counted_in_available_funds(self)
    cpdef bint is_self_managed(self)
    cpdef object update_from_raw(self, dict raw_order)
    cpdef void consider_as_filled(self)
    cpdef void consider_as_canceled(self)
    cpdef dict to_dict(self)
    cpdef void clear(self)
    cpdef bint is_to_be_maintained(self)
    cpdef str get_logger_name(self)
    cpdef void add_chained_order(self, object chained_order)
    cpdef bint should_be_created(self)
    cpdef void add_to_order_group(self, object order_group)
    cdef void _update_total_cost(self)

cdef object _get_sell_and_buy_types(object order_type)
cdef object _infer_order_type_from_maker_or_taker(dict raw_order, object side)

cpdef tuple parse_order_type(dict raw_order)
