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
import octobot_trading.personal_data.orders.order_factory as order_factory
import octobot_trading.personal_data.orders.groups.group_util as group_util


LOGGER_NAME = "orders_storage_operations"


async def apply_order_storage_details_if_any(order, exchange_manager, pending_groups):
    # only real orders can be updated by stored orders
    if not exchange_manager.storage_manager.orders_storage \
            or not exchange_manager.storage_manager.orders_storage.should_store_data():
        return
    order_details = await exchange_manager.storage_manager.orders_storage.get_startup_order_details(
        order.exchange_order_id
    )
    if order_details:
        order.update_from_storage_order_details(order_details)
        await create_orders_storage_related_elements(order, order_details, exchange_manager, pending_groups)


async def create_orders_storage_related_elements(order, order_storage_details, exchange_manager, pending_groups):
    group = group_util.get_or_create_order_group_from_storage_order_details(order_storage_details, exchange_manager)
    if group:
        order.add_to_order_group(group)
        logging.get_logger(LOGGER_NAME).debug(f"Adding {order} to restored group {group}")
        pending_groups[group.name] = group
    await order_factory.restore_chained_orders_from_storage_order_details(
        order, order_storage_details, exchange_manager, pending_groups
    )


async def _create_storage_self_managed_orders_from_group(pending_group_id, exchange_manager, pending_groups):
    try:
        to_create_orders = exchange_manager.storage_manager.orders_storage \
            .get_startup_self_managed_orders_details_from_group(pending_group_id)
        for order_desc in to_create_orders:
            created_order = await order_factory.create_order_from_order_storage_details(
                order_desc, exchange_manager, pending_groups
            )
            await created_order.initialize()
    except Exception as err:
        logging.get_logger(LOGGER_NAME).exception(
            err, True, f"Error when creating {pending_group_id} group self-managed orders with stored data: {err}"
        )


async def create_missing_self_managed_orders_from_storage_order_groups(pending_groups, exchange_manager):
    # create order groups' associated self-managed orders if any
    to_complete_groups = list(pending_groups.keys())
    completed_groups = set()
    max_allowed_nested_chained_orders_groups = 100
    # Loop as created self_managed orders might carry chained orders
    # themselves linked to a group with self-managed orders.
    # This would be seen after each iteration only
    # However only loop a max amount of time as a huge looping amount would indicate an error.
    for _ in range(max_allowed_nested_chained_orders_groups):
        for pending_group_id in to_complete_groups:
            await _create_storage_self_managed_orders_from_group(pending_group_id, exchange_manager, pending_groups)
        # do not process the same group twice
        completed_groups = completed_groups.union(set(to_complete_groups))
        to_complete_groups = [
            group_id
            for group_id in pending_groups.keys()
            if group_id not in completed_groups
        ]
        if not to_complete_groups:
            return
    # if we arrived here, it means that after 100 iterations, still not every order group is complete,
    # there is an issue.
    logging.get_logger(LOGGER_NAME).error(
        f"Error when completing order groups: {len(to_complete_groups)} remaining order "
        f"groups to complete after maximum iterations."
    )
