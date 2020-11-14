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
cimport octobot_trading.personal_data.portfolios.channel.balance as portfolios_channel

cdef class BalanceUpdater(portfolios_channel.BalanceProducer):
    pass

cdef class BalanceProfitabilityUpdater(portfolios_channel.BalanceProfitabilityProducer):
    cdef object exchange_personal_data
    cdef object balance_consumer
    cdef object mark_price_consumer
