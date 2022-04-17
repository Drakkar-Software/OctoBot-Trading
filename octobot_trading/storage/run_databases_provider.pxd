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
cimport octobot_commons.singleton as singleton

cdef class RunDatabasesProvider(singleton.Singleton):
    cdef public dict run_databases

    cpdef void add_bot_id(self, str bot_id, dict config, object tentacles_setup_config, bint with_lock=*, object cache_size=*)
    cpdef bint has_bot_id(self, str bot_id)
    cpdef object get_run_db(self, str bot_id)
    cpdef object get_orders_db(self, str bot_id, str exchange=*)
    cpdef object get_trades_db(self, str bot_id, str exchange=*)
    cpdef object get_transactions_db(self, str bot_id, str exchange=*)
    cpdef object get_backtesting_metadata_db(self, str bot_id)
    cpdef object get_symbol_db(self, str bot_id, str exchange, str symbol)
