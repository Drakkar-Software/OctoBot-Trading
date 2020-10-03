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
from octobot_channels.consumer cimport Consumer

from octobot_backtesting.importers.exchanges.exchange_importer cimport ExchangeDataImporter

from octobot_trading.exchange_data.recent_trades.channel.recent_trade_updater cimport RecentTradeUpdater


cdef class RecentTradeUpdaterSimulator(RecentTradeUpdater):
    cdef ExchangeDataImporter exchange_data_importer

    cdef str exchange_name

    cdef double last_timestamp_pushed

    cdef public Consumer time_consumer

    cdef dict last_timestamp_pushed_by_symbol
    cdef str recent_trades_time_frame
