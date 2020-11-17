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
import octobot_trading.exchanges.types as exchanges_types
import octobot_trading.exchanges.connectors as exchange_connectors
import octobot_trading.exchanges.implementations as exchange_implementations


class SpotExchangeSimulator(exchange_implementations.ExchangeSimulator, exchanges_types.SpotExchange):
    def __init__(self, config, exchange_manager):
        super().__init__(config, exchange_manager)
        self.connector = exchange_connectors.ExchangeSimulator(config, exchange_manager)

    async def stop(self):
        await super().stop()
        self.exchange_manager = None
