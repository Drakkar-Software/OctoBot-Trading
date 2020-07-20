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

from octobot_trading.exchanges.abstract_exchange cimport AbstractExchange
from octobot_trading.exchanges.data.exchange_config_data cimport ExchangeConfig
from octobot_trading.exchanges.data.exchange_personal_data cimport ExchangePersonalData
from octobot_trading.exchanges.data.exchange_symbol_data cimport ExchangeSymbolData
from octobot_trading.exchanges.data.exchange_symbols_data cimport ExchangeSymbolsData
from octobot_trading.exchanges.websockets.abstract_websocket cimport AbstractWebsocket
from octobot_trading.traders.trader cimport Trader
from octobot_trading.util.initializable cimport Initializable

cdef class ExchangeManager(Initializable):
    cdef public str id
    cdef public dict config
    cdef object tentacles_setup_config

    cdef public object exchange_type
    cdef object _logger

    cdef public Trader trader
    cdef public list trading_modes

    cdef public str exchange_class_string
    cdef public str exchange_name

    cdef public object backtesting

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

    cdef public AbstractExchange exchange
    cdef public AbstractWebsocket exchange_web_socket
    cdef public ExchangeConfig exchange_config
    cdef public ExchangePersonalData exchange_personal_data
    cdef public ExchangeSymbolsData exchange_symbols_data

    cdef public list client_time_frames
    cdef public list client_symbols

    # private
    cdef void _load_config_symbols_and_time_frames(self)
    cdef void _load_constants(self)
    cdef void _load_config_symbols_and_time_frames(self)
    cdef void _initialize_simulator_time_frames(self)
    cdef object _uniformize_candles_timestamps(self, list candles)
    cdef void _uniformize_candle_timestamps(self, list candle)
    cdef void _raise_exchange_load_error(self)
    cdef bint _is_managed_by_websocket(self, object channel)

    # public
    cpdef bint enabled(self)
    cpdef str get_exchange_symbol(self, str symbol)
    cpdef str get_exchange_symbol_id(self, str symbol)
    cpdef tuple get_exchange_quote_and_base(self, str symbol)
    cpdef object get_rest_pairs_refresh_threshold(self)
    cpdef bint need_user_stream(self)
    cpdef void reset_exchange_symbols_data(self)
    cpdef void reset_exchange_personal_data(self)
    cpdef bint check_config(self, str exchange_name)
    cpdef bint symbol_exists(self, str symbol)
    cpdef bint time_frame_exists(self, object time_frame)
    cpdef int get_rate_limit(self)
    cpdef object uniformize_candles_if_necessary(self, object candle_or_candles)
    cpdef str get_exchange_name(self)
    cpdef tuple get_exchange_credentials(self, object logger, str exchange_name)
    cpdef bint should_decrypt_token(self, object logger)
    cpdef ExchangeSymbolData get_symbol_data(self, str symbol)
    cpdef bint requires_refresh_trigger(self, str channel)
