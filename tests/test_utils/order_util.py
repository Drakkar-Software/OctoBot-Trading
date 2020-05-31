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
import asyncio

from tests.orders.types import ensure_filled
from tests.util.random_numbers import random_recent_trade, random_price


async def fill_limit_or_stop_order(limit_or_stop_order, min_price, max_price):
    # price_events_manager = limit_or_stop_order.exchange_manager.exchange_symbols_data.get_exchange_symbol_data(
    #     limit_or_stop_order.symbol).price_events_manager
    # price_events_manager.handle_recent_trades(
    #     [random_recent_trade(price=random_price(max_value=min_price),
    #                          timestamp=limit_or_stop_order.timestamp),
    #      random_recent_trade(price=random_price(min_value=max_price),
    #                          timestamp=limit_or_stop_order.timestamp)
    #      ])
    # await asyncio.create_task(ensure_filled())
    await limit_or_stop_order.on_fill()


async def fill_market_order(market_order, price):
    last_prices = [{
        "price": price
    }]

    await market_order.update_order_status(last_prices)
