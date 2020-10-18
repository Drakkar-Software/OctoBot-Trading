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
import octobot_trading.personal_data.orders.order as order_class


class UnknownOrder(order_class.Order):
    """UnknownOrder is used when an exchange is giving an order without a type (ex: binance 2yo+ orders)"""
    async def update_order_status(self, force_refresh=False):
        if not self.trader.simulate:
            await self.default_exchange_update_order_status()
        else:
            # SHOULD NEVER HAPPEN
            raise RuntimeError(f"{self.get_name()} can't be updated and should not appear in simulation mode")
