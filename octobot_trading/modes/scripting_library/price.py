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
import octobot_trading.constants as trading_constants


async def current_price(pair, exchange_manager):
    try:
        return await exchange_manager.exchange_symbols_data.get_exchange_symbol_data(pair) \
            .prices_manager.get_mark_price(timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT)
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError("Mark price is not available")
