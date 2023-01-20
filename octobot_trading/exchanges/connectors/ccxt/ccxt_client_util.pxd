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

# return object when an exception might be thrown
cpdef tuple create_client(object exchange_class, str exchange_name, object exchange_manager, object logger,
                                   dict options, dict headers, dict additional_config,
                                   bint should_authenticate, object unauthenticated_exchange_fallback=*)
cpdef object get_unauthenticated_exchange(object exchange_class, dict options, dict headers, dict additional_config)
cpdef object set_sandbox_mode(object client, bint is_sandboxed)
cpdef dict get_ccxt_client_login_options(object exchange_manager)
cpdef set get_symbols(object client)
cpdef set get_time_frames(object client)
cpdef set get_exchange_pair(object client, str pair)
cpdef str get_pair_cryptocurrency(object client, str pair)
cpdef object get_contract_size(object client, str pair)
cpdef object add_headers(object client, dict headers_dict)
cpdef object add_options(object client, dict options_dict)

cdef object _use_http_proxy_if_necessary(object client)
cdef dict _get_client_config(dict options, dict headers, dict additional_config,
                              object api_key=*, object secret=*, object password=*)
