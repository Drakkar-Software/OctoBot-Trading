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
import asyncio

from octobot_commons.logging.logging_util import get_logger
from octobot_trading.channels.exchange_channel import get_chan
from octobot_trading.constants import BALANCE_CHANNEL, ORDERS_CHANNEL, TRADES_CHANNEL, POSITIONS_CHANNEL, \
    BALANCE_PROFITABILITY_CHANNEL
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
        if self.trader.is_enabled:
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
                self.logger.exception(e, True, f"Error when initializing : {e}. "
                                               f"{self.exchange.name} personal data disabled.")

    # updates
    async def handle_portfolio_update(self, balance, should_notify: bool = True) -> bool:
        try:
            changed: bool = self.portfolio_manager.handle_balance_update(balance)
            if should_notify:
                await get_chan(BALANCE_CHANNEL, self.exchange_manager.id).get_internal_producer().send(balance)
            return changed
        except AttributeError as e:
            self.logger.exception(e, True, f"Failed to update balance : {e}")
            return False

    async def handle_portfolio_update_from_order(self, order, should_notify: bool = True) -> bool:
        try:
            changed: bool = await self.portfolio_manager.handle_balance_update_from_order(order)
            if should_notify:
                await get_chan(BALANCE_CHANNEL, self.exchange_manager.id). \
                    get_internal_producer().send(self.portfolio_manager.portfolio.portfolio)
            return changed
        except AttributeError as e:
            self.logger.exception(e, True, f"Failed to update balance : {e}")
            return False

    async def handle_portfolio_profitability_update(self, balance, mark_price, symbol, should_notify: bool = True):
        try:
            portfolio_profitability = self.portfolio_manager.portfolio_profitability

            if balance is not None:
                await portfolio_profitability.handle_balance_update(balance)

            if mark_price is not None and symbol is not None:
                await portfolio_profitability.handle_mark_price_update(symbol=symbol, mark_price=mark_price)

            if should_notify:
                await get_chan(BALANCE_PROFITABILITY_CHANNEL, self.exchange_manager.id).get_internal_producer() \
                    .send(profitability=portfolio_profitability.profitability,
                          profitability_percent=portfolio_profitability.profitability_percent,
                          market_profitability_percent=portfolio_profitability.market_profitability_percent,
                          initial_portfolio_current_profitability=portfolio_profitability.initial_portfolio_current_profitability)
        except Exception as e:
            self.logger.exception(e, True, f"Failed to update portfolio profitability : {e}")

    async def handle_order_update_from_raw(self, order_id, raw_order,
                                           is_new_order: bool = False,
                                           should_notify: bool = True) -> bool:
        try:
            changed: bool = await self.orders_manager.upsert_order_from_raw(order_id, raw_order)

            if changed:
                updated_order = self.orders_manager.get_order(order_id)
                asyncio.create_task(updated_order.state.on_order_refresh_successful())

                if should_notify:
                    await self.handle_order_update_notification(updated_order, is_new_order)

            return changed
        except KeyError as ke:
            self.logger.debug(f"Failed to update order : Order was not found ({ke})")
        except Exception as e:
            self.logger.exception(e, True, f"Failed to update order : {e}")
        return False

    async def handle_order_instance_update(self, order, is_new_order: bool = False, should_notify: bool = True):
        try:
            changed: bool = self.orders_manager.upsert_order_instance(order)

            if changed:
                asyncio.create_task(order.state.on_order_refresh_successful())

                if should_notify:
                    await self.handle_order_update_notification(order, is_new_order)

            return changed
        except Exception as e:
            self.logger.exception(e, True, f"Failed to update order instance : {e}")
            return False

    async def handle_order_update_notification(self, order, is_new_order):
        """
        Notify Orders channel for Order update
        :param order: the updated order
        :param is_new_order: True if the order was created during update
        """
        try:
            await get_chan(ORDERS_CHANNEL, self.exchange_manager.id).get_internal_producer() \
                .send(cryptocurrency=self.exchange_manager.exchange.get_pair_cryptocurrency(order.symbol),
                      symbol=order.symbol,
                      order=order.to_dict(),
                      is_from_bot=order.is_from_this_octobot,
                      is_new=is_new_order,
                      is_closed=order.is_closed())
        except ValueError as e:
            self.logger.error(f"Failed to send order update notification : {e}")

    async def handle_closed_order_update(self, order_id, raw_order) -> bool:
        """
        Handle closed order creation or update
        :param order_id: the closed order id
        :param raw_order: the closed order dict
        :return: True if the closed order has been created or updated
        """
        try:
            return await self.orders_manager.upsert_order_close_from_raw(order_id, raw_order) is not None
        except Exception as e:
            self.logger.exception(e, True, f"Failed to update order : {e}")
            return False

    async def handle_trade_update(self, symbol, trade_id, trade, should_notify: bool = True):
        try:
            changed: bool = self.trades_manager.upsert_trade(trade_id, trade)
            if should_notify:
                await get_chan(TRADES_CHANNEL, self.exchange_manager.id).get_internal_producer() \
                    .send(cryptocurrency=self.exchange_manager.exchange.get_pair_cryptocurrency(symbol),
                          symbol=symbol,
                          trade=trade.to_dict(),
                          old_trade=False)
            return changed
        except Exception as e:
            self.logger.exception(e, True, f"Failed to update trade : {e}")
            return False

    async def handle_trade_instance_update(self, trade, should_notify: bool = True):
        try:
            changed: bool = self.trades_manager.upsert_trade_instance(trade)
            if should_notify:
                await get_chan(TRADES_CHANNEL, self.exchange_manager.id).get_internal_producer() \
                    .send(cryptocurrency=self.exchange_manager.exchange.get_pair_cryptocurrency(trade.symbol),
                          symbol=trade.symbol,
                          trade=trade.to_dict(),
                          old_trade=False)
            return changed
        except Exception as e:
            self.logger.exception(e, True, f"Failed to update trade instance : {e}")
            return False

    async def handle_position_update(self, symbol, position_id, position, should_notify: bool = True):
        try:
            changed: bool = self.positions_manager.upsert_position(position_id, position)
            if should_notify:
                position_instance = self.positions_manager[position_id]
                await get_chan(POSITIONS_CHANNEL, self.exchange_manager.id).get_internal_producer() \
                    .send(cryptocurrency=self.exchange_manager.exchange.get_pair_cryptocurrency(symbol),
                          symbol=symbol,
                          position=position_instance.to_dict(),
                          is_closed=False,
                          is_updated=changed,
                          is_from_bot=True,
                          is_liquidated=position_instance.is_liquidated())
            return changed
        except Exception as e:
            self.logger.exception(e, True, f"Failed to update position : {e}")
            return False

    async def handle_position_instance_update(self, position, should_notify: bool = True):
        try:
            changed: bool = self.positions_manager.upsert_position_instance(position)
            if should_notify:
                await get_chan(POSITIONS_CHANNEL, self.exchange_manager.id).get_internal_producer() \
                    .send(cryptocurrency=self.exchange_manager.exchange.get_pair_cryptocurrency(position.symbol),
                          symbol=position.symbol,
                          position=position,
                          is_closed=False,
                          is_updated=changed,
                          is_from_bot=True,
                          is_liquidated=position.is_liquidated())
            return changed
        except Exception as e:
            self.logger.exception(e, True, f"Failed to update position instance : {e}")
            return False

    def get_order_portfolio(self, order):
        return order.linked_portfolio if order.linked_portfolio is not None else self.portfolio_manager.portfolio

    def clear(self):
        if self.portfolio_manager is not None:
            self.portfolio_manager.portfolio_profitability = None
        if self.orders_manager is not None:
            self.orders_manager.clear()
        if self.trades_manager is not None:
            self.trades_manager.clear()
