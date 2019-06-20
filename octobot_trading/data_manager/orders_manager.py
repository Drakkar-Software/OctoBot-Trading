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

from octobot_trading.data.order import Order
from octobot_trading.enums import ExchangeConstantsOrderColumns, OrderStatus
from octobot_trading.util.initializable import Initializable


class OrdersManager(Initializable):
    MAX_ORDERS_COUNT = 2000

    def __init__(self, config, trader, exchange_manager):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.config, self.trader, self.exchange_manager = config, trader, exchange_manager

        self.orders = {}

    async def initialize_impl(self):
        self._reset_orders()

    def update_order_attribute(self, order_id, key, value):
        self.orders[order_id][key] = value

    def get_all_orders(self, symbol=None, since=None, limit=None):
        return self._select_orders(symbol=symbol, since=since, limit=limit)

    def get_open_orders(self, symbol=None, since=None, limit=None):
        return self._select_orders(OrderStatus.OPEN.value, symbol, since, limit)

    def get_closed_orders(self, symbol=None, since=None, limit=None):
        return self._select_orders(OrderStatus.CLOSED.value, symbol, since, limit)

    def get_order(self, order_id):
        return self.orders[order_id]

    def upsert_order(self, order_id, raw_order):
        if order_id not in self.orders:
            self.orders[order_id] = self._create_order_from_raw(raw_order)
            self._check_orders_size()
            return True
        self._update_order_from_raw(self.orders[order_id], raw_order)
        return True

    # private methods
    def _reset_orders(self):
        self.orders = {}

    def _check_orders_size(self):
        if len(self.orders) > self.MAX_ORDERS_COUNT:
            self._remove_oldest_orders(int(self.MAX_ORDERS_COUNT / 2))

    def _create_order_from_raw(self, raw_order):
        order = Order(self.trader)
        self._update_order_from_raw(order, raw_order)
        return order

    def _update_order_from_raw(self, order, raw_order):
        # TODO
        pass

    def _select_orders(self, state=None, symbol=None, since=None, limit=None):
        orders = [
            order
            for order in self.orders.values()
            if (
                    (state is None or order[ExchangeConstantsOrderColumns.STATUS.value] == state) and
                    (symbol is None or (symbol and order[ExchangeConstantsOrderColumns.SYMBOL.value] == symbol)) and
                    (since is None or (since and order[ExchangeConstantsOrderColumns.TIMESTAMP.value] < since))
            )
        ]
        return orders if limit is None else orders[0:limit]

    def _remove_oldest_orders(self, nb_to_remove):
        time_sorted_orders = sorted(self.orders.values(),
                                    key=lambda x: x.timestamp)
        shrinked_list = [time_sorted_orders[i]
                         for i in range(0, nb_to_remove)
                         if (time_sorted_orders[i].status == OrderStatus.OPEN.value
                             or time_sorted_orders[i].status == OrderStatus.PARTIALLY_FILLED.value)]

        shrinked_list += [time_sorted_orders[i] for i in range(nb_to_remove, len(time_sorted_orders))]
        self.orders = {order.order_id: order for order in shrinked_list}
