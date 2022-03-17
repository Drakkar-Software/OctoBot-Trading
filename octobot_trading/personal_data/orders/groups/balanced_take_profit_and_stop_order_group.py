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
import octobot_trading.personal_data.orders.order_util as order_util
import octobot_trading.constants as constants
import octobot_commons.logging as logging


class BalancedTakeProfitAndStopOrderGroup(order_group.OrderGroup):
    """
    BalancedTakeProfitAndStopOrderGroup is linking orders together in the way that if any order of the group is filled
    order cancelled, orders that are on the other extreme of the setup (extremes being take profits and stop losses)
    are reduced or cancelled symmetrically.
    Mostly used to pair stop and limit orders together in a stop-loss / take-profit setup using multiple stop losses
    and take profits.
    Orders that are the further from their last_created_price are reduced / cancelled first
    """
    TAKE_PROFIT = "take_profit"
    STOP = "stop"
    UPDATE = "update"
    CANCEL = "cancel"
    ORDER = "order"
    UPDATED_QUANTITY = "updated_quantity"

    def __init__(self, name, orders_manager):
        super().__init__(name, orders_manager)
        # keep track of orders being balanced to avoid nested balance issues
        self.balancing_orders = []

    async def on_fill(self, filled_order, ignored_orders=None):
        """
        Called when an order referencing this group is filled
        This is called right before updating portfolio for this filled order and the
        order fill publication
        :param filled_order: the filled order
        :param ignored_orders: orders that should be ignored
        """
        await self._balance_orders(filled_order, ignored_orders)

    async def on_cancel(self, cancelled_order, ignored_orders=None):
        """
        Called when an order referencing this group is cancelled
        This is called before updating portfolio for this cancelled order and the
        order cancel publication
        :param cancelled_order: the cancelled order
        :param ignored_orders: orders that should be ignored
        """
        await self._balance_orders(cancelled_order, ignored_orders)

    def can_create_order(self, order_type, quantity):
        """
        Returns True if there is an imbalance allowing to create an order of this type and with this quantity
        :param order_type: order type to create
        :param quantity: quantity to put in order
        :return: True when an imbalance allows it
        """
        balance = self._get_balance(None, None)
        if order_util.is_stop_order(order_type):
            return balance[self.STOP].get_balance() + quantity <= balance[self.TAKE_PROFIT].get_balance()
        return balance[self.TAKE_PROFIT].get_balance() + quantity <= balance[self.STOP].get_balance()

    def get_max_order_quantity(self, order_type):
        """
        Returns The maximum order quantity to reach the order side's balance
        :param order_type: order type to create
        :return: the balancing quantity
        """
        balance = self._get_balance(None, None)
        if order_util.is_stop_order(order_type):
            max_quantity = balance[self.TAKE_PROFIT].get_balance() - balance[self.STOP].get_balance()
        else:
            max_quantity = balance[self.STOP].get_balance() - balance[self.TAKE_PROFIT].get_balance()
        return max_quantity if max_quantity > constants.ZERO else constants.ZERO

    async def enable(self, enabled):
        # disable when creating order sequentially (and therefore pause balancing)
        # setting enabled to True will trigger an order balance
        await super().enable(enabled)
        if enabled:
            await self._balance_orders(None, None)

    async def _balance_orders(self, closed_order, ignored_orders):
        if not self.enabled:
            return
        locally_balancing_orders = []
        logger = logging.get_logger(self.__class__.__name__)
        try:
            updated_orders = False
            balance = self._get_balance(closed_order, ignored_orders)
            locally_balancing_orders = balance[self.TAKE_PROFIT].orders + balance[self.STOP].orders
            self.balancing_orders += locally_balancing_orders
            take_profit_actions = balance[self.TAKE_PROFIT].get_actions_to_balance(balance[self.STOP].get_balance())
            stop_actions = balance[self.STOP].get_actions_to_balance(balance[self.TAKE_PROFIT].get_balance())
            for order in take_profit_actions[self.CANCEL] + stop_actions[self.CANCEL]:
                logger.debug(f"Cancelling order to keep balance, order: {order}")
                await order.trader.cancel_order(order, ignored_order=closed_order)
                updated_orders = True
            for update_data in take_profit_actions[self.UPDATE] + stop_actions[self.UPDATE]:
                logger.debug(f"Updating order side to {update_data[self.UPDATED_QUANTITY]} to keep balance, "
                             f"order: {update_data[self.ORDER]}")
                await update_data[self.ORDER].trader.edit_order(
                    update_data[self.ORDER],
                    edited_quantity=update_data[self.UPDATED_QUANTITY])
                updated_orders = True
            if not updated_orders:
                logger.debug("Nothing to update, orders are already evenly balanced")
        except Exception as e:
            logger.exception(e, True, f"Error when balancing orders: {e}")
        finally:
            # remove locally_balancing_orders from self.balancing_orders
            self.balancing_orders = [order
                                     for order in self.balancing_orders
                                     if order not in locally_balancing_orders]

    def _get_balance(self, closed_order, ignored_orders):
        balance = {
            self.TAKE_PROFIT: _SideBalance(),
            self.STOP: _SideBalance()
        }
        for order in self.get_group_open_orders():
            if order is not closed_order \
                    and (ignored_orders is None or order not in ignored_orders) \
                    and order not in self.balancing_orders:
                if order_util.is_stop_order(order.order_type):
                    balance[self.STOP].add_order(order)
                else:
                    balance[self.TAKE_PROFIT].add_order(order)
        return balance


class _SideBalance:
    def __init__(self):
        self.orders = []

    def add_order(self, order):
        self.orders.append(order)
        # orders are sorted according to their distance from their last created price: the further the earlier in list
        # warning: not working with negative prices
        self.orders = sorted(self.orders, key=lambda o: -abs(o.origin_price-o.created_last_price))

    def get_actions_to_balance(self, target_balance):
        actions = {
            BalancedTakeProfitAndStopOrderGroup.CANCEL: [],
            BalancedTakeProfitAndStopOrderGroup.UPDATE: [],
        }
        balance = self.get_balance()
        if target_balance < constants.ZERO:
            target_balance = abs(target_balance)
        if balance <= target_balance:
            # only reducing the current balance is possible
            return actions
        to_be_reduced_amount = constants.ZERO
        remaining_orders = list(self.orders)
        while remaining_orders and balance - to_be_reduced_amount > target_balance:
            order_quantity = remaining_orders[0].origin_quantity
            if balance - to_be_reduced_amount - order_quantity >= target_balance:
                # cancel order and keep reducing
                actions[BalancedTakeProfitAndStopOrderGroup.CANCEL].append(remaining_orders.pop(0))
                to_be_reduced_amount += order_quantity
            else:
                # update order and stop reducing
                actions[BalancedTakeProfitAndStopOrderGroup.UPDATE].append({
                    BalancedTakeProfitAndStopOrderGroup.ORDER: remaining_orders.pop(0),
                    BalancedTakeProfitAndStopOrderGroup.UPDATED_QUANTITY:
                        target_balance - (balance - to_be_reduced_amount - order_quantity)
                })
                break
        return actions

    def get_balance(self):
        if self.orders:
            return sum(order.origin_quantity for order in self.orders)
        return constants.ZERO
