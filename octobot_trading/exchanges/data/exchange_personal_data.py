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
from octobot_commons.logging.logging_util import get_logger

from octobot_trading.data_manager.orders_manager import OrdersManager
from octobot_trading.data_manager.portfolio_manager import PortfolioManager
from octobot_trading.data_manager.positions_manager import PositionsManager
from octobot_trading.data_manager.trades_manager import TradesManager
from octobot_trading.util.initializable import Initializable


class ExchangePersonalData(Initializable):
    # note: symbol keys are without /
    def __init__(self, exchange_manager):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.exchange_manager = exchange_manager
        self.config = exchange_manager.config

    async def initialize_impl(self):
        self.trader = self.exchange_manager.trader
        self.exchange = self.exchange_manager.exchange
        if self.trader.enabled:
            try:
                self.portfolio_manager = PortfolioManager(self.config, self.trader, self.exchange_manager)
                self.trades_manager = TradesManager(self.config, self.trader, self.exchange_manager)
                self.orders_manager = OrdersManager(self.config, self.trader, self.exchange_manager)
                self.positions_manager = PositionsManager(self.config, self.trader, self.exchange_manager)
                await self.portfolio_manager.initialize()
                await self.trades_manager.initialize()
                await self.orders_manager.initialize()
                await self.positions_manager.initialize()
            except Exception as e:
                self.logger.error(f"Error when initializing portfolio: {e}. "
                                  f"{self.exchange.name} trader disabled.")
                self.logger.exception(e)

    # updates
    async def handle_portfolio_update(self, balance) -> bool:
        try:
            return await self.portfolio_manager.handle_balance_update(balance)
        except AttributeError as e:
            self.logger.exception(f"Failed to update balance : {e}")
            return False

    def handle_order_update(self, order_id, order) -> (bool, bool):
        try:
            return self.orders_manager.upsert_order(order_id, order)
        except Exception as e:
            self.logger.exception(f"Failed to update order : {e}")
            return False

    def handle_closed_order_update(self, order_id, order) -> bool:
        try:
            return self.orders_manager.upsert_order_close(order_id, order)
        except Exception as e:
            self.logger.exception(f"Failed to update order : {e}")
            return False

    def handle_trade_update(self, trade_id, trade):
        try:
            return self.trades_manager.upsert_trade(trade_id, trade)
        except Exception as e:
            self.logger.exception(f"Failed to update trade : {e}")
            return False

    def handle_position_update(self, position_id, position):
        try:
            return self.positions_manager.upsert_position(position_id, position)
        except Exception as e:
            self.logger.exception(f"Failed to update position : {e}")
            return False

    def get_order_portfolio(self, order):
        return order.linked_portfolio if order.linked_portfolio is not None else self.portfolio
