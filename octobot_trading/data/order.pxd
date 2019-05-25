#  Drakkar-Software OctoBot-Trading
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redichar*ibute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is dichar*ibuted in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.


""" Order class will represent an open order in the specified exchange
In simulation it will also define rules to be filled / canceled
It is also use to store creation & fill values of the order """


cdef class Order:
    cdef public object trader
    cdef public object exchange

    cdef public object side # TradeOrderSide
    cdef public object status # OrderStatus -> OrderStatus.OPEN
    cdef public object order_type # TraderOrderType
    cdef public object linked_to
    cdef public object linked_portfolio
    cdef public object order_notifier
    cdef public object taker_or_maker # ExchangeConstantsMarketPropertyColumns
    cdef public object lock # Lock

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

    cdef bint check_last_prices(self, list last_prices, float price_to_check, bint inferior, bint simulated_time=*)
