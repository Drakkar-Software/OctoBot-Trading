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
cimport async_channel.consumer as consumer
cimport octobot_backtesting.importers as importers
cimport octobot_trading.exchange_data.ticker.channel.ticker_updater as ticker_updater


cdef class TickerUpdaterSimulator(ticker_updater.TickerUpdater):
    cdef importers.ExchangeDataImporter exchange_data_importer

    cdef str exchange_name

    cdef double last_timestamp_pushed

    cdef public consumer.Consumer time_consumer

    cdef dict last_timestamp_pushed_by_symbol
    cdef str ticker_time_frame
