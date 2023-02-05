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
import octobot_commons.logging as logging


class OrderGroup:
    def __init__(self, name, orders_manager):
        self.name = name
        self.orders_manager = orders_manager
        self.logger = logging.get_logger(str(self))
        self.enabled = True

    async def on_fill(self, filled_order, ignored_orders=None):
        """
        Called when an order referencing this group is filled
        This is called right before updating portfolio for this filled order and the
        order fill publication
        :param filled_order: the filled order
        :param ignored_orders: orders that should be ignored
        """

    async def on_cancel(self, cancelled_order, ignored_orders=None):
        """
        Called when an order referencing this group is cancelled
        This is called before updating portfolio for this cancelled order and the
        order cancel publication
        :param cancelled_order: the cancelled order
        :param ignored_orders: orders that should be ignored
        """

    async def enable(self, enabled):
        self.enabled = enabled

    def get_group_open_orders(self):
        return [
            order
            for order in self.orders_manager.get_order_from_group(self.name)
            if order.is_open() and not order.is_cancelling()
        ]

    def clear(self):
        self.orders_manager = None

    def __str__(self):
        return f"{self.__class__.__name__} #{self.name}"

    def __eq__(self, other):
        return self.__class__ is other.__class__ and \
               self.orders_manager is other.orders_manager \
               and self.name == other.name
