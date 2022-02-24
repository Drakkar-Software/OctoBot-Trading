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
cimport octobot_trading.personal_data.orders.orders_manager as orders_manager
cimport octobot_trading.personal_data.orders.order as order_class
cimport octobot_trading.personal_data.portfolios.portfolio_manager as portfolio_manager
cimport octobot_trading.personal_data.positions.positions_manager as positions_manager
cimport octobot_trading.personal_data.trades.trades_manager as trades_manager
cimport octobot_trading.personal_data.transactions.transactions_manager as transactions_manager
cimport octobot_trading.util as util

cdef class ExchangePersonalData(util.Initializable):
    cdef public object logger
    cdef public object exchange

    cdef public dict config

    cdef public object exchange_manager
    cdef public object trader

    cdef public portfolio_manager.PortfolioManager portfolio_manager
    cdef public trades_manager.TradesManager trades_manager
    cdef public orders_manager.OrdersManager orders_manager
    cdef public positions_manager.PositionsManager positions_manager
    cdef public transactions_manager.TransactionsManager transactions_manager

    cpdef void clear(self)

    cdef bint _is_out_of_sync_order(self, str order_id)
