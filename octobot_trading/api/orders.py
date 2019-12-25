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

from octobot_trading.api import LOGGER_TAG
from octobot_commons.logging.logging_util import get_logger
from octobot_trading.enums import TraderOrderType

LOGGER = get_logger(LOGGER_TAG)


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


def get_open_orders(exchange_manager):
    return exchange_manager.exchange_personal_data.orders_manager.get_open_orders()


async def cancel_all_open_orders(exchange_manager):
    return await exchange_manager.trader.cancel_all_open_orders()


async def cancel_all_open_orders_with_currency(exchange_manager, currency):
    return await exchange_manager.trader.cancel_all_open_orders_with_currency(currency)


async def cancel_order_from_description(exchange_manager, order_description):
    LOGGER.error("from cancel_order_from_description: "
                 "exchange_manager.trader.cancel_order_from_description is not implemented yet")
    # TODO: uncomment when implemented
    # return await exchange_manager.trader.cancel_order_from_description(order_description)
    return 0
