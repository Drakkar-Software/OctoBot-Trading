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
