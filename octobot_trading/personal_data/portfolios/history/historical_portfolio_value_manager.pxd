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


cimport octobot_trading.util as util
cimport octobot_trading.personal_data.portfolios.portfolio_manager as portfolio_manager

cdef class HistoricalPortfolioValueManager(util.Initializable):
    cdef public object logger

    cdef public portfolio_manager.PortfolioManager portfolio_manager

    cdef public list saved_time_frames
    cdef public str data_source
    cdef public str version
    cdef public object starting_time
    cdef public object last_update_time
    cdef public dict starting_portfolio
    cdef public dict ending_portfolio
    cdef public dict historical_ending_portfolio
    cdef public dict historical_starting_portfolio_values

    cdef public int max_history_size
    cdef public object historical_portfolio_value

    cpdef object get_historical_values(self, str currency, object time_frame, object from_timestamp=*, object to_timestamp=*)
    cpdef object get_historical_value(self, object timestamp)
    cpdef dict get_metadata(self)
    cpdef list get_dict_historical_values(self)
    cpdef bint has_previous_session_portfolio(self)
    cpdef bint has_historical_starting_portfolio_value(self, str unit)
    cpdef object get_historical_starting_starting_portfolio_value(self, str unit)

    cdef void _add_historical_portfolio_value(self, double timestamp, dict value_by_currency)
    cdef void _load_metadata(self, list metadata)
    cdef void _load_historical_starting_portfolio_values(self)
    cdef bint _is_historical_timestamp_relevant(self, double timestamp, object time_frame_seconds, object from_timestamp, object to_timestamp)
    cdef set _get_relevant_timestamps(self, double timestamp, object currencies, list time_frames, bint force_update, bint include_past_data)
    cdef bint _should_update_timestamp(self, object currencies, object time_frame_allowed_window_start, bint force_update)
    cdef object _get_value_in_currency(self, object historical_value, str currency)
    cdef object _convert_historical_value(self, object historical_value, str target_currency)
    cdef object _update_portfolios(self)
