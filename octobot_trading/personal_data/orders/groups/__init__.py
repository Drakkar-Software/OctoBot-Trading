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

from octobot_trading.personal_data.orders.groups import balanced_take_profit_and_stop_order_group
from octobot_trading.personal_data.orders.groups.balanced_take_profit_and_stop_order_group import (
    BalancedTakeProfitAndStopOrderGroup,
)

from octobot_trading.personal_data.orders.groups import one_cancels_the_other_order_group
from octobot_trading.personal_data.orders.groups.one_cancels_the_other_order_group import (
    OneCancelsTheOtherOrderGroup,
)

__all__ = [
    "BalancedTakeProfitAndStopOrderGroup",
    "OneCancelsTheOtherOrderGroup",
]
