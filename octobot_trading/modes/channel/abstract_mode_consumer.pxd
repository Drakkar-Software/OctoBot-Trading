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
cimport octobot_trading.modes.channel as modes_channel
cimport octobot_trading.exchanges as exchanges

cdef class AbstractTradingModeConsumer(modes_channel.ModeChannelConsumer):
    cdef public object trading_mode

    cdef public exchanges.ExchangeManager exchange_manager

    cpdef int get_number_of_traded_assets(self)

cpdef check_factor(min_val, max_val, factor)
