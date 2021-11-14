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
cimport octobot_trading.personal_data.portfolios.asset as asset_class


cdef class FutureAsset(asset_class.Asset):
    cdef public object unrealized_pnl
    cdef public object initial_margin
    cdef public object wallet_balance
    cdef public object position_margin
    cdef public object order_margin

    cpdef bint update(self, object total=*, object available=*, object position_margin=*,
                      object unrealized_pnl=*, object initial_margin=*)
    cpdef bint set(self, object total=*, object available=*, object margin_balance=*, object initial_margin=*,
                   object position_margin=*, object order_margin=*, object unrealized_pnl=*)
    cpdef void set_unrealized_pnl(self, object unrealized_pnl)

    cdef void _update_total(self)
    cdef void _update_available(self)
