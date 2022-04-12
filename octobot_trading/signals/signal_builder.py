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
import octobot_trading.signals.trading_signal as trading_signal


class SignalBuilder:
    def __init__(self, strategy, exchange, exchange_type, symbol, description, state, orders):
        self.strategy = strategy
        self.exchange = exchange
        self.exchange_type = exchange_type
        self.symbol = symbol
        self.description = description
        self.state = state
        self.orders = orders
        self.signal = None
        self.reset()

    def add_created_order(self, order):
        pass

    def add_edited_order(self, order):
        pass

    def add_cancelled_order(self, order):
        pass

    def reset(self):
        self.signal = trading_signal.TradingSignal(
            self.strategy,
            self.exchange,
            self.exchange_type,
            self.symbol,
            self.description,
            self.state,
            self.orders
        )
