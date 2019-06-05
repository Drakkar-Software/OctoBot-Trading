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

cpdef object interpret_file_name(str file_name)
cpdef str build_file_name(str exchange, str symbol, str ending=*)
cpdef void write_data_file(str file_name, dict content)
cpdef dict read_data_file(str file_name)
cpdef object get_data_type(str file_name)
cpdef str get_file_ending(object data_type)
cpdef dict get_time_frames(str file_path, dict content)
cpdef dict get_ohlcv_per_timeframe(str file_path, dict content)
cpdef int get_candles_count(str file_path, list tf_content)
cpdef int get_number_of_candles(str file_path)
cpdef float get_date(str time_info)
cpdef dict get_file_description(str data_collector_path, str file_name)
cpdef bint is_valid_ending(str ending)
cpdef list get_all_available_data_files(str data_collector_path)
cpdef object delete_data_file(str data_collector_path, str file_name)
