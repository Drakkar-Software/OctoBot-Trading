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
import octobot_trading.enums as enums


class TradingSignal:
    def __init__(self, strategy, exchange, exchange_type, symbol, description, state, orders,
                 identifier=None, version=None):
        self.strategy = strategy
        self.exchange = exchange
        self.exchange_type = exchange_type
        self.symbol = symbol
        self.description = description
        self.state = state
        self.orders = orders

        self.identifier = identifier
        self.version = version or self._get_version()

    def to_dict(self):
        return {
            enums.TradingSignalAttrs.STRATEGY.value: self.strategy,
            enums.TradingSignalAttrs.EXCHANGE.value: self.exchange,
            enums.TradingSignalAttrs.EXCHANGE_TYPE.value: self.exchange_type,
            enums.TradingSignalAttrs.SYMBOL.value: self.symbol,
            enums.TradingSignalAttrs.DESCRIPTION.value: self.description,
            enums.TradingSignalAttrs.STATE.value: self.state,
            enums.TradingSignalAttrs.ORDERS.value: self.orders,
        }

    def __str__(self):
        return f"{self.to_dict()}"

    def _get_version(self):
        try:
            import octobot.constants
            return octobot.constants.COMMUNITY_FEED_CURRENT_MINIMUM_VERSION
        except ImportError:
            return "1.0.0"
