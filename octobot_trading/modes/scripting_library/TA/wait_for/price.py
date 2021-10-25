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
import octobot_trading.api as api
from octobot_trading.modes.scripting_library import current_price


async def wait_for_price(
    context,
    pair=None,
    offset=None,
    offset_percent=None,
    absolute=None,
    offset_entry=None,
    offset_entry_with_fees=None,    #TODO
    offset_entry_percent=None,
    order_tag=None
):
    price = await current_price(context.traded_pair or pair, context.exchange_manager)
    target_price = absolute
    if offset is not None:
        target_price = price + offset
    if offset_percent is not None:
        target_price = price * (1 + (offset_percent / 100))
    if offset_entry is not None:
        order = get_order_from_tag(context.exchange_manager, order_tag) #TODO order tags
        entry_price = order.filled_price
        target_price = entry_price + offset
    if offset_entry_percent is not None:
        order = get_order_from_tag(context.exchange_manager, order_tag) #TODO order tags
        entry_price = order.filled_price
        target_price = entry_price * (1 + (offset_percent / 100))
    if target_price is None:
        raise RuntimeError("No offset has been provided")
    trigger_above = target_price > price
    price_hit_event = context.exchange_manager.exchange_symbols_data. \
        get_exchange_symbol_data(pair).price_events_manager. \
        add_event(target_price, api.get_exchange_current_time(context.exchange_manager), trigger_above)
    await asyncio.wait_for(price_hit_event.wait(), timeout=None)
