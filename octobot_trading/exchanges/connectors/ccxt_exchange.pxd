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
cimport octobot_trading.exchanges.abstract_exchange as abstract_exchange
cimport decimal

cdef class CCXTExchange(abstract_exchange.AbstractExchange):
    cdef object all_currencies_price_ticker

    cdef public object client
    cdef public object exchange_type

    cdef public bint is_authenticated

    cdef dict options
    cdef dict headers

    cdef object additional_ccxt_config

    # private
    cdef void _create_client(self)

    # @staticmethod waiting for a future version of cython
    # cdef bint _ensure_order_details_completeness(object order, list order_required_fields=*)

    cpdef void add_headers(self, dict headers_dict)
    cpdef void add_options(self, dict options_dict)
    cpdef set get_client_symbols(self)
    cpdef set get_client_time_frames(self)
    cpdef dict get_ccxt_client_login_options(self)
    cpdef str get_ccxt_order_type(self, object order_type)
    cpdef void set_sandbox_mode(self, bint is_sandboxed)
    cpdef dict get_bundled_order_parameters(self, object stop_loss_price=*, object take_profit_price=*)

    cdef void _unauthenticated_exchange_fallback(self, object err)
    cdef object _get_unauthenticated_exchange(self)
    cdef object _get_client_config(self, object api_key=*, object secret=*, object password=*)
    cdef bint _should_authenticate(self)

    # get methods

    # get_order
    cdef dict get_order(self, str order_id, str symbol, bool check_completeness, dict **kwargs)
    cdef dict get_order_default(self, str order_id, str symbol, bool check_completeness, dict **kwargs)
    cdef dict get_order_private(self, str order_id, str symbol, bool check_completeness, dict **kwargs)
    cdef dict get_order_from_open_and_closed_orders(self, str order_id, str symbol, bool check_completeness, dict **kwargs)
    cdef dict get_order_using_stop_id(self, str order_id, str symbol, bool check_completeness, dict **kwargs)
    cdef dict get_order_from_trades(self, str order_id, str symbol, bool check_completeness, dict **kwargs)

    # get_all_orders
    cdef list get_all_order(self, str symbol, int since, int limit, bool check_completeness, dict **kwargs)
    cdef list get_all_order_default(self, str symbol, int since, int limit, bool check_completeness, dict **kwargs)

    # get_open_orders
    cdef list get_open_orders(self, str symbol, int since, int limit, bool check_completeness, dict **kwargs)
    cdef list get_open_orders_default(self, str symbol, int since, int limit, bool check_completeness, dict **kwargs)
    cdef list get_open_stop_orders_using_stop_loss_endpoint(self, str symbol, int since, int limit, 
                                                            bool check_completeness, dict **kwargs)

    # get_closed_orders
    cdef list get_closed_orders(self, str symbol, int since, int limit, bool check_completeness, dict **kwargs)
    cdef list get_closed_orders_default(self, str symbol, int since, int limit, bool check_completeness, dict **kwargs)
    cdef list get_closed_stop_orders_using_stop_loss_endpoint(self, str symbol, int since, int limit, 
                                                            bool check_completeness, dict **kwargs)

    # get_my_recent_trades
    cdef list get_my_recent_trades(self, str symbol, int since, int limit, bool check_completeness, dict **kwargs)
    cdef list get_my_recent_trades_default(self, str symbol, int since, int limit, bool check_completeness, dict **kwargs)
    cdef list GET_MY_RECENT_TRADES_USING_RECENT_TRADES(self, str symbol, int since, int limit, 
                                                            bool check_completeness, dict **kwargs)
    cdef list get_my_recent_trades_using_closed_orders(self, str symbol, int since, int limit, 
                                                            bool check_completeness, dict **kwargs)

    # parsers
    cpdef dict parse_order(self, dict raw_order, str order_type, decimal.Decimal quantity,
                           decimal.Decimal price, str status, str symbol,
                           str side, int or float timestamp, bool check_completeness)
    cpdef list parse_orders(self, list raw_orders, str order_type, decimal.Decimal quantity,
                           decimal.Decimal: price, str status, str symbol,
                           str side, int or float timestamp, bool check_completeness)
    cpdef dict parse_trade(self, dict raw_trade, bool check_completeness)
    cpdef list parse_trades(self, list raw_trades, bool check_completeness)
    cpdef dict parse_position(self, raw_position dict)
    cpdef list parse_positions(self, raw_positions list)
