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
from octobot_trading.data.order cimport Order
from octobot_trading.data_manager.orders_manager cimport OrdersManager
from octobot_trading.data_manager.portfolio_manager cimport PortfolioManager
from octobot_trading.data_manager.positions_manager cimport PositionsManager
from octobot_trading.data_manager.trades_manager cimport TradesManager
from octobot_trading.exchanges.exchange_manager cimport ExchangeManager
from octobot_trading.traders.trader cimport Trader
from octobot_trading.util.initializable cimport Initializable

cdef class ExchangePersonalData(Initializable):
    cdef public object logger
    cdef public object exchange

    cdef public dict config

    cdef public ExchangeManager exchange_manager
    cdef public Trader trader

    cdef public PortfolioManager portfolio_manager
    cdef public TradesManager trades_manager
    cdef public OrdersManager orders_manager
    cdef public PositionsManager positions_manager

    cpdef object get_order_portfolio(self, Order order)
    cpdef void clear(self)
