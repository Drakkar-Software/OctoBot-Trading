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
cimport octobot_trading.exchanges.exchange_config_data as exchange_config_data
cimport octobot_trading.exchanges.abstract_websocket_exchange as abstract_websocket
# cimport octobot_trading.exchange_data.exchange_symbols_data as exchange_symbols_data
# cimport octobot_trading.exchange_data.exchange_symbol_data as exchange_symbol_data
cimport octobot_trading.util as util

cdef class ExchangeManager(util.Initializable):
    cdef public str id
    cdef public str exchange_class_string
    cdef public str exchange_name

    cdef public dict config

    cdef public object tentacles_setup_config
    cdef public object logger
    cdef public object backtesting
    cdef public object trader

    cdef public list client_time_frames
    cdef public list client_symbols
    cdef public list trading_modes

    cdef public bint rest_only
    cdef public bint ignore_config
    cdef public bint is_ready
    cdef public bint is_simulated
    cdef public bint is_backtesting
    cdef public bint is_trader_simulated
    cdef public bint is_collecting
    cdef public bint is_spot_only
    cdef public bint is_margin
    cdef public bint is_future
    cdef public bint is_sandboxed
    cdef public bint is_trading
    cdef public bint has_websocket
    cdef public bint exchange_only
    cdef public bint without_auth

    cdef public abstract_exchange.AbstractExchange exchange
    cdef public abstract_websocket.AbstractWebsocketExchange exchange_web_socket
    cdef public exchange_config_data.ExchangeConfig exchange_config
    cdef public object exchange_backend
    cdef public bint is_valid_account
    cdef public object community_authenticator
    cdef public object exchange_symbols_data
    cdef public object exchange_personal_data

    # private
    cdef void _load_config_symbols_and_time_frames(self)
    cdef void _load_config_symbols_and_time_frames(self)

    # public
    cpdef bint enabled(self)
    cpdef void load_constants(self)
    cpdef str get_exchange_symbol(self, str symbol)
    cpdef tuple get_exchange_quote_and_base(self, str symbol)
    cpdef object get_rest_pairs_refresh_threshold(self)
    cpdef bint need_user_stream(self)
    cpdef void reset_exchange_symbols_data(self)
    cpdef void reset_exchange_personal_data(self)
    cpdef bint check_config(self, str exchange_name)
    cpdef bint symbol_exists(self, str symbol)
    cpdef bint time_frame_exists(self, object time_frame)
    cpdef str get_exchange_name(self)
    cpdef int get_currently_handled_pair_with_time_frame(self)
    cpdef bint get_is_overloaded(self)
    cpdef tuple get_exchange_credentials(self, object logger, str exchange_name)
    cpdef str get_exchange_sub_account_id(self, str exchange_name)
    cpdef bint should_decrypt_token(self, object logger)
    cpdef object get_symbol_data(self, str symbol)
