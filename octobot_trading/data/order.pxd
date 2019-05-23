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
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.


""" Order class will represent an open order in the specified exchange
In simulation it will also define rules to be filled / canceled
It is also use to store creation & fill values of the order """


cdef class Order:
    cdef object trader
    cdef object exchange

    cdef object side # TradeOrderSide
    cdef object status # OrderStatus -> OrderStatus.OPEN
    cdef object order_type # TraderOrderType
    cdef object linked_to
    cdef object linked_portfolio
    cdef object order_notifier
    cdef object taker_or_maker # ExchangeConstantsMarketPropertyColumns
    cdef object lock # Lock

    cdef bint is_simulated
    cdef bint is_from_this_octobot

    cdef char* symbol
    cdef char* currency
    cdef char* market
    cdef char* order_id

    cdef float origin_price
    cdef float origin_stop_price
    cdef float origin_quantity
    cdef float market_total_fees
    cdef float filled_quantity
    cdef float filled_price
    cdef float total_cost
    cdef float timestamp
    cdef float creation_time
    cdef float canceled_time
    cdef float executed_time
    cdef float created_last_price
    cdef float order_profitability

    cdef dict fee

    cdef list last_prices
    cdef list linked_orders

    cdef void new(self, object order_type,
                  char* symbol,
                  float current_price,
                  float quantity,
                  float price,
                  float stop_price,
                  object status,
                  object order_notifier,
                  char* order_id,
                  float quantity_filled,
                  float timestamp,
                  object linked_to,
                  object linked_portfolio)

    cdef bint check_last_prices(self, list last_prices, float price_to_check, bint inferior, bint simulated_time=*)
    cdef object get_currency_and_market(self)
    cdef float get_total_fees(self, char* currency)
    cdef bint is_filled(self)
    cdef bint is_cancelled(self)
    cdef bint matches_description(self, char* description)
    cdef object infer_taker_or_maker(self)
    cdef dict get_computed_fee(self, forced_value=*)
    cdef float get_profitability(self)
    cdef float generate_executed_time(self, simulated_time=*)
