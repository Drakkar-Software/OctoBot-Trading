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
import octobot_trading.enums as enums
import octobot_commons.tentacles_management as tentacles_management
import octobot_commons.logging as logging


def get_group_class(group_type_str: str):
    for group_class in tentacles_management.get_all_classes_from_parent(order_group.OrderGroup):
        if group_type_str == group_class.__name__:
            return group_class
    raise KeyError(group_type_str)


def get_or_create_order_group_from_storage_order_details(order_details, exchange_manager):
    group = order_details.get(enums.StoredOrdersAttr.GROUP.value, None)
    if group:
        try:
            group_name = group.get(enums.StoredOrdersAttr.GROUP_ID.value, None)
            if group_name:
                group = exchange_manager.exchange_personal_data.orders_manager.get_or_create_group(
                    get_group_class(group[enums.StoredOrdersAttr.GROUP_TYPE.value]),
                    group_name,
                )
                logging.get_logger("GroupUtil").debug(f"Restored {group} order group")
                return group
        except KeyError as err:
            logging.get_logger("GroupUtil").error(f"Unhandled group type: {err}")
    return None
