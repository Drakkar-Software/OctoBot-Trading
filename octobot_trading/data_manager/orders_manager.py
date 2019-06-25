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
from collections import OrderedDict

from octobot_commons.logging.logging_util import get_logger

from octobot_trading.data.order import Order
from octobot_trading.enums import OrderStatus
from octobot_trading.util.initializable import Initializable


class OrdersManager(Initializable):
    MAX_ORDERS_COUNT = 2000

    def __init__(self, config, trader, exchange_manager):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.config, self.trader, self.exchange_manager = config, trader, exchange_manager
        self.orders_initialized = False  # TODO
        self.orders = OrderedDict()

    async def initialize_impl(self):
        self._reset_orders()

    def update_order_attribute(self, order_id, key, value):
        self.orders[order_id][key] = value

    def get_all_orders(self, symbol=None, since=-1, limit=-1):
        return self._select_orders(None, symbol=symbol, since=since, limit=limit)

    def get_open_orders(self, symbol=None, since=-1, limit=-1):
        return self._select_orders(OrderStatus.OPEN.value, symbol, since, limit)

    def get_closed_orders(self, symbol=None, since=-1, limit=-1):
        return self._select_orders(OrderStatus.CLOSED.value, symbol, since, limit)

    def get_order(self, order_id):
        return self.orders[order_id]

    def upsert_order(self, order_id, raw_order) -> (bool, bool):
        if order_id not in self.orders:
            self.orders[order_id] = self._create_order_from_raw(raw_order)
            self._check_orders_size()
            return True, False
        return self._update_order_from_raw(self.orders[order_id], raw_order), True

    def upsert_order_close(self, order_id, raw_order):
        if order_id in self.orders:
            self._update_order_from_raw(self.orders[order_id], raw_order)
            # TODO order -> trade
            self.orders.pop(order_id)
            return True
        return False

    def upsert_order_instance(self, order):
        if order.order_id not in self.orders:
            self.orders[order.order_id] = order
            self._check_orders_size()
        else:
            # TODO
            pass

    # private methods
    def _reset_orders(self):
        self.orders_initialized = False
        self.orders = OrderedDict()

    def _check_orders_size(self):
        if len(self.orders) > self.MAX_ORDERS_COUNT:
            self._remove_oldest_orders(int(self.MAX_ORDERS_COUNT / 2))

    def _create_order_from_raw(self, raw_order):
        order = Order(self.trader)
        order.update_from_raw(raw_order)
        return order

    def _update_order_from_raw(self, order, raw_order):
        return order.update_from_raw(raw_order)

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
