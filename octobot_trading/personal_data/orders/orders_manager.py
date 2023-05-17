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
import uuid
import typing

import octobot_commons.logging as logging

import octobot_trading.enums as enums
import octobot_trading.constants as constants
import octobot_trading.util as util
import octobot_trading.errors as errors
import octobot_trading.personal_data.orders.order as order_class
import octobot_trading.personal_data.orders.order_factory as order_factory
import octobot_trading.personal_data.orders.order_util as order_util


class OrdersManager(util.Initializable):
    MAX_ORDERS_COUNT = 0

    def __init__(self, trader):
        super().__init__()
        self.logger = logging.get_logger(self.__class__.__name__)
        self.trader = trader
        self.orders_initialized = False  # TODO
        self.orders = collections.OrderedDict()
        self.order_groups = {}
        # orders that are expected from exchange but have not yet been fetched: will be removed when fetched
        self.pending_creation_orders = []
        # if this the orders manager completed the initial exchange orders sync phase (only on real trader)
        self.are_exchange_orders_initialized = self.trader.simulate

    async def initialize_impl(self):
        self._reset_orders()

    def get_all_orders(
        self, symbol=None, since=constants.NO_DATA_LIMIT, 
        until=constants.NO_DATA_LIMIT, limit=constants.NO_DATA_LIMIT, tag=None):
        return self._select_orders(
            None, symbol=symbol, since=since,
            until=until, limit=limit, tag=tag
        )

    def get_open_orders(
        self, symbol=None, since=constants.NO_DATA_LIMIT, until=constants.NO_DATA_LIMIT,
        limit=constants.NO_DATA_LIMIT, tag=None):
        return self._select_orders(
            enums.OrderStatus.OPEN, symbol, since=since,
            until=until, limit=limit, tag=tag
        )

    def get_pending_cancel_orders(
        self, symbol=None, since=constants.NO_DATA_LIMIT, until=constants.NO_DATA_LIMIT,
        limit=constants.NO_DATA_LIMIT, tag=None):
        return self._select_orders(
            enums.OrderStatus.PENDING_CANCEL, symbol, since=since, 
            until=until, limit=limit, tag=tag
        )

    def get_closed_orders(
        self, symbol=None, since=constants.NO_DATA_LIMIT, until=constants.NO_DATA_LIMIT,
        limit=constants.NO_DATA_LIMIT, tag=None):
        return self._select_orders(
            enums.OrderStatus.CLOSED, symbol, since=since,
            until=until, limit=limit, tag=tag
        )

    def get_order(self, order_id, exchange_order_id=None):
        if order_id is None:
            for order in self.orders.values():
                if order.exchange_order_id == exchange_order_id:
                    return order
            raise KeyError(exchange_order_id)
        return self.orders[order_id]

    def get_order_from_group(self, group_name):
        return [
            order
            for order in self.orders.values()
            if order.order_group is not None and order.order_group.name == group_name
        ]

    def get_or_create_group(self, group_type, group_name):
        """
        Should be used to manage long lasting groups that are meant to be re-used
        :param group_type: the OrderGroup class of the group
        :param group_name: the name to identify the group
        :return: the retrieved / created group
        """
        try:
            group = self.order_groups[group_name]
            if isinstance(group, group_type):
                return group
            raise errors.ConflictingOrderGroupError(f"The order group named {group_name} is of "
                                                    f"type: {group.__class__.__name__} instead of  {group_type}")
        except KeyError:
            return self.create_group(group_type, group_name)

    def create_group(self, group_type, group_name=None):
        """
        Should be used to create temporary groups binding localized orders, where this group can be
        created once and directly associated to each order
        :param group_type:
        :param group_name:
        :return:
        """
        group_name = group_name or str(uuid.uuid4())
        if group_name in self.order_groups:
            raise errors.ConflictingOrderGroupError(f"Can't create a new order group named '{group_name}': "
                                                    f"one with this name already exists")
        group = group_type(group_name, self)
        self.order_groups[group_name] = group
        return group

    async def upsert_order_from_raw(self, exchange_order_id, raw_order, is_from_exchange) -> (bool, order_class.Order):
        if not self.has_order(None, exchange_order_id=exchange_order_id):
            self.logger.info(f"Including new order fetched from exchange: {raw_order}")
            new_order = order_factory.create_order_instance_from_raw(self.trader, raw_order)
            # replace new_order by previously created pending_order if any relevant pending_order
            new_order = await self.get_and_update_pending_order(new_order) or new_order
            if is_from_exchange:
                new_order.is_synchronized_with_exchange = True
            self._add_order(new_order.order_id, new_order)
            self._check_orders_size()
            await new_order.initialize(is_from_exchange_data=True)
            return True, new_order
        order = self.get_order(None, exchange_order_id=exchange_order_id)
        return await _update_order_from_raw(order, raw_order), order

    def register_pending_creation_order(self, pending_order):
        if self.trader.simulate:
            self.logger.error(f"Called register_pending_creation_order on an simulated trader, "
                              f"this should not happen. Order: {pending_order}")
        self.pending_creation_orders.append(pending_order)

    async def get_and_update_pending_order(self, created_order):
        pending_order = self._get_pending_order(created_order, True)
        # TODO refactor to := when cython will support it
        if pending_order is None:
            return None
        await order_util.apply_pending_order_from_created_order(pending_order, created_order, True)
        created_order.clear()
        return pending_order

    def _get_pending_order(self, created_order, should_pop):
        for index, pending_order in enumerate(self.pending_creation_orders):
            if order_util.is_associated_pending_order(pending_order, created_order):
                if should_pop:
                    self.pending_creation_orders.pop(index)
                return pending_order
        return None

    def get_all_active_and_pending_orders_id(self) -> list:
        return [
            order.order_id
            for order in self._select_orders()
        ] + [
            order.order_id
            for order in self.pending_creation_orders
        ]

    async def upsert_order_close_from_raw(self, exchange_order_id, raw_order) -> typing.Optional[order_class.Order]:
        if self.has_order(None, exchange_order_id=exchange_order_id):
            order = self.get_order(None, exchange_order_id=exchange_order_id)
            await _update_order_from_raw(order, raw_order)
            return order
        return None

    async def upsert_order_instance(self, order) -> bool:
        if not self.has_order(order.order_id):
            # this should not consume pending orders
            if self._get_pending_order(order, False):
                self.logger.error(f"Called upsert_order_instance on an order that fits a pending order, "
                                  f"this should not happen. Order: {order}")
            order = await self.get_and_update_pending_order(order) or order
            self._add_order(order.order_id, order)
            self._check_orders_size()
            return True
        # TODO
        return False

    def _add_order(self, order_id, order):
        if order_id is None:
            self.logger.warning(f"Adding order with None order_id to order manager: {order}")
        self.orders[order_id] = order

    def has_order(self, order_id, exchange_order_id=None) -> bool:
        if order_id is None:
            try:
                self.get_order(None, exchange_order_id=exchange_order_id)
                return True
            except KeyError:
                return False
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

    def replace_order(self, previous_id, order):
        if self.has_order(previous_id):
            self.orders.pop(previous_id, None)
        self._add_order(order.order_id, order)
        self._check_orders_size()

    # private methods
    def _reset_orders(self):
        self.orders_initialized = False
        self.orders = collections.OrderedDict()
        for group in self.order_groups.values():
            group.clear()
        self.order_groups = {}

    def _check_orders_size(self):
        if self.MAX_ORDERS_COUNT and len(self.orders) > self.MAX_ORDERS_COUNT:
            self._remove_oldest_orders(int(self.MAX_ORDERS_COUNT / 2))

    def _select_orders(
        self, state=None, symbol=None, since=constants.NO_DATA_LIMIT, 
        until=constants.NO_DATA_LIMIT, limit=constants.NO_DATA_LIMIT, tag=None):
        orders = [
            order
            for order in self.orders.values()
            if (
                    (state is None or order.status == state) and
                    (symbol is None or (symbol and order.symbol == symbol)) and
                    (since == constants.NO_DATA_LIMIT or (since and order.timestamp >= since)) and
                    (until == constants.NO_DATA_LIMIT or (until and order.timestamp <= until)) and
                    (tag is None or order.tag == tag)
            )
        ]
        return orders if limit == constants.NO_DATA_LIMIT else orders[0:limit]

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
