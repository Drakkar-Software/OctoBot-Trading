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

from octobot_trading.enums import TraderOrderType


class OrdersApi:
    # Orders list
    @staticmethod
    def get_open_orders(exchange_manager, symbol: str):
        return exchange_manager.exchange_personal_data.orders_manager.get_open_orders(symbol)

    # Order creation
    @staticmethod
    async def create_order(exchange_manager,
                           order_type: TraderOrderType,
                           symbol: str,
                           current_price: float,
                           quantity: float,
                           price: float):
        await exchange_manager.trader.create_order(exchange_manager.trader.create_order_instance(order_type=order_type,
                                                                                                 symbol=symbol,
                                                                                                 current_price=current_price,
                                                                                                 quantity=quantity,
                                                                                                 price=price))
