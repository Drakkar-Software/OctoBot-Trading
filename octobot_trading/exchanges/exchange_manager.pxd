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
from octobot_trading.exchanges.data.exchange_personal_data cimport ExchangePersonalData
from octobot_trading.exchanges.data.exchange_symbol_data cimport ExchangeSymbolData
from octobot_trading.exchanges.data.exchange_symbols_data cimport ExchangeSymbolsData
from octobot_trading.exchanges.websockets.abstract_websocket cimport AbstractWebsocket
from octobot_trading.traders.trader cimport Trader
from octobot_trading.util.initializable cimport Initializable

cdef class ExchangeManager(Initializable):
    cdef public dict config

    cdef public object exchange_type
    cdef public object logger

    cdef public float last_web_socket_reset

    cdef public Trader trader

    cdef public str exchange_class_string

    cdef public bint  rest_only
    cdef public bint ignore_config
    cdef public bint is_ready
    cdef public bint is_simulated
    cdef public bint is_trader_simulated

    cdef public AbstractExchange exchange
    cdef public AbstractWebsocket exchange_web_socket
    cdef public ExchangePersonalData exchange_personal_data
    cdef public ExchangeSymbolsData exchange_symbols_data
    # exchange_consumers_manager

    cdef public dict client_time_frames
    cdef public dict cryptocurrencies_traded_pairs

    cdef public list client_symbols
    cdef public list traded_pairs
    cdef public list time_frames

    cdef public ExchangeSymbolData get_symbol_data(self, str symbol)

    # private
    cdef void _load_config_symbols_and_time_frames(self)
    cdef void _load_constants(self)
    cdef AbstractWebsocket _search_and_create_websocket(self, websocket_class)
    cdef void _load_config_symbols_and_time_frames(self)
    cdef void _set_config_traded_pairs(self)
    cdef list _create_wildcard_symbol_list(self, str crypto_currency)
    cdef list _add_tradable_symbols(self, str crypto_currency)
    cdef void _set_config_time_frame(self)
    cdef _uniformize_candles_timestamps(self, list candles)
    cdef void _uniformize_candle_timestamps(self, dict candle)
    cdef _raise_exchange_load_error(self)

    @staticmethod
    cdef bint _is_tradable_with_cryptocurrency(str symbol, str crypto_currency)

    # public
    cpdef bint enabled(self)
    cpdef str get_exchange_symbol(self, str symbol)
    cpdef str get_exchange_symbol_id(self, str symbol)
    cpdef tuple get_exchange_quote_and_base(self, str symbol)
    cpdef bint need_user_stream(self)
    cpdef void reset_exchange_symbols_data(self)
    cpdef void reset_exchange_personal_data(self)
    cpdef bint did_not_just_try_to_reset_web_socket(self)
    cpdef void reset_websocket_exchange(self)
    cpdef bint check_config(self, str exchange_name)
    cpdef force_disable_web_socket(self, str exchange_name)
    cpdef check_web_socket_config(self, str exchange_name)
    cpdef list get_traded_pairs(self, str crypto_currency=*)
    cpdef bint symbol_exists(self, str symbol)
    cpdef bint time_frame_exists(self, object time_frame, str symbol=*)
    cpdef int get_rate_limit(self)
    cpdef object uniformize_candles_if_necessary(self, object candle_or_candles)
    cpdef str get_exchange_name(self)
    cpdef bint should_decrypt_token(self, object logger)
    cpdef ExchangeSymbolData get_symbol_data(self, str symbol)
