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

cpdef object get_margin_exchange_class(str exchange_name, object tentacles_setup_config)
cpdef object get_future_exchange_class(str exchange_name, object tentacles_setup_config)
cpdef object get_spot_exchange_class(str exchange_name, object tentacles_setup_config)
cpdef str get_order_side(object order_type)
cpdef void log_time_sync_error(object logger, str exchange_name, object error, str details)
cpdef str get_partners_explanation_message()
cpdef object get_exchange_type(object exchange_manager_instance)

cdef object search_exchange_class_from_exchange_name(object exchange_class,
                                                     str exchange_name,
                                                     object tentacles_setup_config,
                                                     bint enable_default=*)
cdef bint _is_exchange_candidate_matching(object exchange_candidate,
                                          str exchange_name,
                                          object tentacles_setup_config,
                                          bint enable_default=*)
cdef str _get_docs_url()
cdef str _get_exchanges_docs_url()
cdef str _get_time_sync_error_message(str exchange_name, str details)
cdef dict _get_minimal_exchange_config(str exchange_name, dict exchange_config)
