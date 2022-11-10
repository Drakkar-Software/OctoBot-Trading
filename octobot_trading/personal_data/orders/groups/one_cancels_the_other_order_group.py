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
import octobot_trading.personal_data.orders.order_group as order_group
import octobot_trading.errors as errors
import octobot_trading.signals as signals


class OneCancelsTheOtherOrderGroup(order_group.OrderGroup):
    """
    OneCancelsTheOtherOrderGroup is linking orders together in the way that if any order of the group is filled
    order cancelled, all the orders are cancelled.
    Mostly used to pair stop and limit orders together in a stop-loss / take-profit setup
    """

    async def on_fill(self, filled_order, ignored_orders=None):
        """
        Called when an order referencing this group is filled
        This is called right before updating portfolio for this filled order and the
        order fill publication
        :param filled_order: the filled order
        :param ignored_orders: orders that should be ignored
        """
        if not self.enabled:
            return
        for order in self.get_group_open_orders():
            if order is not filled_order and order.is_open():
                self.logger.info(f"Cancelling order [{order}] from order group as {filled_order} is filled")
                async with signals.remote_signal_publisher(order.trader.exchange_manager, order.symbol, True):
                    await signals.cancel_order(
                        order.trader.exchange_manager,
                        signals.should_emit_trading_signal(order.trader.exchange_manager),
                        order,
                        ignored_order=filled_order
                    )

    async def on_cancel(self, cancelled_order, ignored_orders=None):
        """
        Called when an order referencing this group is cancelled
        This is called before updating portfolio for this cancelled order and the
        order cancel publication
        :param cancelled_order: the cancelled order
        :param ignored_orders: orders that should be ignored
        """
        if not self.enabled:
            return
        if ignored_orders and len(ignored_orders) > 1:
            raise errors.OrderGroupTriggerArgumentError(f"ignored_orders supports at most 1 argument "
                                                        f"for {self.__class__.__name__}")
        ignored_order = ignored_orders[0] if ignored_orders else None
        for order in self.get_group_open_orders():
            if order is not cancelled_order and order.is_open():
                self.logger.info(f"Cancelling order [{order}] from order group as {cancelled_order} is cancelled")
                async with signals.remote_signal_publisher(order.trader.exchange_manager, order.symbol, True):
                    await signals.cancel_order(order.trader.exchange_manager,
                                               signals.should_emit_trading_signal(order.trader.exchange_manager),
                                               order,
                                               ignored_order=ignored_order)
