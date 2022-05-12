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

cpdef object create_order_from_raw(object trader,
                                   dict raw_order)

cpdef object create_order_instance_from_raw(object trader,
                                            dict raw_order,
                                            bint force_open= *)

cpdef object create_order_from_type(object trader,
                                    object order_type,
                                    object side= *)

cpdef object create_order_instance(object trader,
                                   object order_type,
                                   str symbol,
                                   object current_price,
                                   object quantity,
                                   object price= *,
                                   object stop_price= *,
                                   object status= *,
                                   str order_id= *,
                                   object filled_price= *,
                                   object average_price= *,
                                   object quantity_filled= *,
                                   object total_cost= *,
                                   double timestamp= *,
                                   object side= *,
                                   object fees_currency_side=*,
                                   object group=*,
                                   object tag=*,
                                   object reduce_only=*,
                                   str quantity_currency=*)
