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
import octobot_trading.exchanges.connectors as exchange_connectors
import octobot_trading.exchanges.types as exchanges_types


class SpotExchangeSimulator(exchanges_types.SpotExchange):
    def __init__(self, config, exchange_manager, backtesting):
        super().__init__(config, exchange_manager)
        self.connector = exchange_connectors.ExchangeSimulator(config, exchange_manager, backtesting=backtesting)

    async def initialize_impl(self):
        await self.connector.initialize()

    async def stop(self) -> None:
        await self.connector.stop()
        await super().stop()
        self.exchange_manager = None

    @classmethod
    def is_supporting_exchange(cls, exchange_candidate_name) -> bool:
        return exchange_connectors.ExchangeSimulator.is_supporting_exchange(exchange_candidate_name)

    @classmethod
    def is_simulated_exchange(cls) -> bool:
        return exchange_connectors.ExchangeSimulator.is_simulated_exchange()

    def get_exchange_current_time(self):
        return self.connector.get_exchange_current_time()

    def get_market_status(self, symbol, price_example=None, with_fixer=True):
        return self.connector.get_market_status(symbol=symbol, price_example=price_example, with_fixer=with_fixer)

    def get_uniform_timestamp(self, timestamp):
        return self.connector.get_uniform_timestamp(timestamp=timestamp)

    def get_fees(self, symbol):
        return self.connector.get_fees(symbol=symbol)

    def get_trade_fee(self, symbol, order_type, quantity, price, taker_or_maker):
        return self.connector.get_trade_fee(symbol=symbol, order_type=order_type, quantity=quantity,
                                            price=price, taker_or_maker=taker_or_maker)
