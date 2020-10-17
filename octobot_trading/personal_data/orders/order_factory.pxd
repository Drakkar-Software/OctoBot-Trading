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
cimport octobot_trading.personal_data.orders as orders_personal_data
cimport octobot_trading.exchanges as exchanges

cpdef orders_personal_data.Order create_order_from_raw(exchanges.Trader trader,
                                                       dict raw_order)

cpdef orders_personal_data.Order create_order_instance_from_raw(exchanges.Trader trader,
                                                                dict raw_order,
                                                                bint force_open= *)

cpdef orders_personal_data.Order create_order_from_type(exchanges.Trader trader,
                                                        object order_type,
                                                        object side= *)

cpdef orders_personal_data.Order create_order_instance(exchanges.Trader trader,
                                                       object order_type,
                                                       str symbol,
                                                       double current_price,
                                                       double quantity,
                                                       double price= *,
                                                       double stop_price= *,
                                                       object linked_to= *,
                                                       object status= *,
                                                       str order_id= *,
                                                       double filled_price= *,
                                                       double average_price= *,
                                                       double quantity_filled= *,
                                                       double total_cost= *,
                                                       double timestamp= *,
                                                       object linked_portfolio= *,
                                                       object side= *)
