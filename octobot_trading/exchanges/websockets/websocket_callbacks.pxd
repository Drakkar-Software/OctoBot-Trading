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
from octobot_trading.channels.ohlcv cimport OHLCVProducer
from octobot_trading.channels.order_book cimport OrderBookProducer
from octobot_trading.channels.recent_trade cimport RecentTradeProducer
from octobot_trading.channels.ticker cimport TickerProducer

from octobot_trading.exchanges.websockets.abstract_websocket cimport AbstractWebsocket

cdef class OrderBookCallBack(OrderBookProducer):
    cdef public AbstractWebsocket parent

cdef class RecentTradesCallBack(RecentTradeProducer):
    cdef public AbstractWebsocket parent

cdef class TickersCallBack(TickerProducer):
    cdef public AbstractWebsocket parent

cdef class OHLCVCallBack(OHLCVProducer):
    cdef public AbstractWebsocket parent
