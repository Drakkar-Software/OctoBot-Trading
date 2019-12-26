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

from octobot_trading.data.order cimport Order
from octobot_trading.traders.trader cimport Trader

cpdef Order create_order_from_raw(Trader trader, dict raw_order)

cpdef Order create_order_instance_from_raw(Trader trader, dict raw_order)

cpdef Order create_order_from_type(Trader trader, object order_type)

cpdef Order create_order_instance(Trader trader,
                                  object order_type,
                                  str symbol,
                                  float current_price,
                                  float quantity,
                                  float price=*,
                                  float stop_price=*,
                                  object linked_to=*,
                                  object status=*,
                                  str order_id=*,
                                  float filled_price=*,
                                  float quantity_filled=*,
                                  float total_cost=*,
                                  float timestamp=*,
                                  object linked_portfolio=*)
