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
import collections

import typing

import octobot_commons.logging as logging

import octobot_trading.enums as enums
import octobot_trading.util as util
import octobot_trading.personal_data.orders.order as order_class
import octobot_trading.personal_data.orders.order_factory as order_factory


class OrdersManager(util.Initializable):
    MAX_ORDERS_COUNT = 0

    def __init__(self, trader):
        super().__init__()
        self.logger = logging.get_logger(self.__class__.__name__)
        self.trader = trader
        self.orders_initialized = False  # TODO
        self.orders = collections.OrderedDict()
        # if this the orders manager completed the initial exchange orders sync phase (only on real trader)
        self.are_exchange_orders_initialized = self.trader.simulate

    async def initialize_impl(self):
        self._reset_orders()

    def update_order_attribute(self, order_id, key, value):
        self.orders[order_id][key] = value

    def get_all_orders(self, symbol=None, since=-1, limit=-1):
        return self._select_orders(None, symbol=symbol, since=since, limit=limit)

    def get_open_orders(self, symbol=None, since=-1, limit=-1):
        return self._select_orders(enums.OrderStatus.OPEN, symbol, since, limit)

    def get_closed_orders(self, symbol=None, since=-1, limit=-1):
        return self._select_orders(enums.OrderStatus.CLOSED, symbol, since, limit)

    def get_order(self, order_id):
        return self.orders[order_id]

    async def upsert_order_from_raw(self, order_id, raw_order) -> bool:
        if not self.has_order(order_id):
            self.logger.debug(f"Creating new order from exchange data: {raw_order}")
            new_order = order_factory.create_order_instance_from_raw(self.trader, raw_order)
            self.orders[order_id] = new_order
            await new_order.initialize(is_from_exchange_data=True)
            self._check_orders_size()
            return True
        return await _update_order_from_raw(self.orders[order_id], raw_order)

    async def upsert_order_close_from_raw(self, order_id, raw_order) -> typing.Optional[order_class.Order]:
        if self.has_order(order_id):
            order = self.orders[order_id]
            await _update_order_from_raw(self.orders[order_id], raw_order)
            return order
        return None

    def upsert_order_instance(self, order) -> bool:
        if not self.has_order(order.order_id):
            self.orders[order.order_id] = order
            self._check_orders_size()
            return True
        # TODO
        return False

    def has_order(self, order_id) -> bool:
        return order_id in set(self.orders.keys())

    def remove_order_instance(self, order):
        if self.has_order(order.order_id):
            self.orders.pop(order.order_id, None)
            order.clear()
        else:
            self.logger.warning(f"Attempt to remove an order that is not in orders_manager: "
                                f"{order.order_type.name if order.order_type else ''} "
                                f"{order.symbol}: {order.origin_quantity} at {order.origin_price} "
                                f"(id: {order.order_id})")

    # private methods
    def _reset_orders(self):
        self.orders_initialized = False
        self.orders = collections.OrderedDict()

    def _check_orders_size(self):
        if self.MAX_ORDERS_COUNT and len(self.orders) > self.MAX_ORDERS_COUNT:
            self._remove_oldest_orders(int(self.MAX_ORDERS_COUNT / 2))

    def _select_orders(self, state=None, symbol=None, since=-1, limit=-1):
        orders = [
            order
            for order in self.orders.values()
            if (
                    (state is None or order.status == state) and
                    (symbol is None or (symbol and order.symbol == symbol)) and
                    (since == -1 or (since and order.timestamp < since))
            )
        ]
        return orders if limit == -1 else orders[0:limit]

    def _remove_oldest_orders(self, nb_to_remove):
        for _ in range(nb_to_remove):
            self.orders.popitem(last=False)

    def clear(self):
        for order in self.orders.values():
            order.clear()
        self._reset_orders()


async def _update_order_from_raw(order, raw_order):
    """
    Calling order update from raw method
    :param order: the order to update
    :param raw_order: the order raw value to use for updating
    :return: the result of order.update_from_raw
    """
    async with order.lock:
        if order.is_to_be_maintained():
            return order.update_from_raw(raw_order)
    return False
