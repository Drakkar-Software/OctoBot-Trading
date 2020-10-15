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
cimport octobot_trading.personal_data as personal_data
cimport octobot_trading.exchanges as exchanges
cimport octobot_trading.util as util

cdef class ExchangePersonalData(util.Initializable):
    cdef public object logger
    cdef public object exchange

    cdef public dict config

    cdef public exchanges.ExchangeManager exchange_manager
    cdef public exchanges.Trader trader

    cdef public personal_data.PortfolioManager portfolio_manager
    cdef public personal_data.TradesManager trades_manager
    cdef public personal_data.OrdersManager orders_manager
    cdef public personal_data.PositionsManager positions_manager

    cpdef object get_order_portfolio(self, Order order)
    cpdef void clear(self)
