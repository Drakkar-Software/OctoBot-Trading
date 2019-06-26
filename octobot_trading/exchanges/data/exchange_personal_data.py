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

from octobot_trading.channels import BALANCE_CHANNEL, ORDERS_CHANNEL, TRADES_CHANNEL, POSITIONS_CHANNEL
from octobot_trading.channels.exchange_channel import ExchangeChannels
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

        self.trader = None
        self.exchange = None
        self.portfolio_manager = None
        self.trades_manager = None
        self.orders_manager = None
        self.positions_manager = None

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
    async def handle_portfolio_update(self, balance, should_notify: bool = True) -> bool:
        try:
            changed: bool = await self.portfolio_manager.handle_balance_update(balance)
            if should_notify:
                await ExchangeChannels.get_chan(BALANCE_CHANNEL, self.exchange.name).get_global_producer().send(balance)
            return changed
        except AttributeError as e:
            self.logger.exception(f"Failed to update balance : {e}")
            return False

    async def handle_order_update(self, symbol, order_id, order, should_notify: bool = True) -> (bool, bool):
        try:
            changed: bool = self.orders_manager.upsert_order(order_id, order)
            if should_notify:
                await ExchangeChannels.get_chan(ORDERS_CHANNEL, self.exchange.name).get_global_producer() \
                    .send(symbol,
                          order,
                          is_from_bot=True,
                          is_closed=False,
                          is_updated=changed,
                          is_wildcard=False)
                await ExchangeChannels.get_chan(ORDERS_CHANNEL, self.exchange.name).get_global_producer() \
                    .send(order.symbol,
                          order,
                          is_from_bot=True,
                          is_closed=False,
                          is_updated=changed,
                          is_wildcard=True)
            return changed
        except Exception as e:
            self.logger.exception(f"Failed to update order : {e}")
            return False

    async def handle_order_instance_update(self, order, should_notify: bool = True):
        try:
            changed: bool = self.orders_manager.upsert_order_instance(order)
            if should_notify:
                await ExchangeChannels.get_chan(ORDERS_CHANNEL, self.exchange.name).get_global_producer()\
                    .send(order.symbol,
                          order,
                          is_from_bot=True,
                          is_closed=False,
                          is_updated=changed,
                          is_wildcard=False)
                await ExchangeChannels.get_chan(ORDERS_CHANNEL, self.exchange.name).get_global_producer() \
                    .send(order.symbol,
                          order,
                          is_from_bot=True,
                          is_closed=False,
                          is_updated=changed,
                          is_wildcard=True)
            return changed
        except Exception as e:
            self.logger.exception(f"Failed to update order instance : {e}")
            return False

    async def handle_closed_order_update(self, symbol, order_id, order, should_notify: bool = True) -> bool:
        try:
            changed: bool = self.orders_manager.upsert_order_close(order_id, order)
            if should_notify:
                await ExchangeChannels.get_chan(ORDERS_CHANNEL, self.exchange.name).get_global_producer() \
                    .send(symbol,
                          order,
                          is_from_bot=True,
                          is_closed=True,
                          is_updated=changed,
                          is_wildcard=False)
                await ExchangeChannels.get_chan(ORDERS_CHANNEL, self.exchange.name).get_global_producer() \
                    .send(symbol,
                          order,
                          is_from_bot=True,
                          is_closed=True,
                          is_updated=changed,
                          is_wildcard=True)
            return changed
        except Exception as e:
            self.logger.exception(f"Failed to update order : {e}")
            return False

    async def handle_trade_update(self, symbol, trade_id, trade, should_notify: bool = True):
        try:
            changed: bool = self.trades_manager.upsert_trade(trade_id, trade)
            if should_notify:
                await ExchangeChannels.get_chan(TRADES_CHANNEL, self.exchange.name).get_global_producer() \
                    .send(symbol,
                          trade,
                          old_trade=False,
                          is_wildcard=False)
                await ExchangeChannels.get_chan(TRADES_CHANNEL, self.exchange.name).get_global_producer() \
                    .send(symbol,
                          trade,
                          old_trade=False,
                          is_wildcard=True)
            return changed
        except Exception as e:
            self.logger.exception(f"Failed to update trade : {e}")
            return False

    async def handle_trade_instance_update(self, trade, should_notify: bool = True):
        try:
            changed: bool = self.trades_manager.upsert_trade_instance(trade)
            if should_notify:
                await ExchangeChannels.get_chan(TRADES_CHANNEL, self.exchange.name).get_global_producer() \
                    .send(trade.symbol,
                          trade,
                          old_trade=False,
                          is_wildcard=False)
                await ExchangeChannels.get_chan(TRADES_CHANNEL, self.exchange.name).get_global_producer() \
                    .send(trade.symbol,
                          trade,
                          old_trade=False,
                          is_wildcard=True)
            return changed
        except Exception as e:
            self.logger.exception(f"Failed to update trade instance : {e}")
            return False

    async def handle_position_update(self, symbol, position_id, position, should_notify: bool = True):
        try:
            changed: bool = self.positions_manager.upsert_position(position_id, position)
            if should_notify:
                await ExchangeChannels.get_chan(POSITIONS_CHANNEL, self.exchange.name).get_global_producer() \
                    .send(symbol,
                          position,
                          is_closed=False,
                          is_updated=changed,
                          is_from_bot=True,
                          is_wildcard=False)
                await ExchangeChannels.get_chan(POSITIONS_CHANNEL, self.exchange.name).get_global_producer() \
                    .send(symbol,
                          position,
                          is_closed=False,
                          is_updated=changed,
                          is_from_bot=True,
                          is_wildcard=True)
            return changed
        except Exception as e:
            self.logger.exception(f"Failed to update position : {e}")
            return False

    async def handle_position_instance_update(self, position, should_notify: bool = True):
        try:
            changed: bool = self.positions_manager.upsert_position_instance(position)
            if should_notify:
                await ExchangeChannels.get_chan(POSITIONS_CHANNEL, self.exchange.name).get_global_producer() \
                    .send(position.symbol,
                          position,
                          is_closed=False,
                          is_updated=changed,
                          is_from_bot=True,
                          is_wildcard=False)
                await ExchangeChannels.get_chan(POSITIONS_CHANNEL, self.exchange.name).get_global_producer() \
                    .send(position.symbol,
                          position,
                          is_closed=False,
                          is_updated=changed,
                          is_from_bot=True,
                          is_wildcard=True)
            return changed
        except Exception as e:
            self.logger.exception(f"Failed to update position instance : {e}")
            return False

    def get_order_portfolio(self, order):
        return order.linked_portfolio if order.linked_portfolio is not None else self.portfolio_manager.portfolio
