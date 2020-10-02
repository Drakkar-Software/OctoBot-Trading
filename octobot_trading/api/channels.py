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

async def subscribe_to_ohlcv_channel(callback, exchange_id):
    from octobot_trading.channels.ohlcv import OHLCVChannel
    await _subscribe_to_channel(callback, exchange_id, OHLCVChannel)


async def subscribe_to_trades_channel(callback, exchange_id):
    from octobot_trading.channels.trades import TradesChannel
    await _subscribe_to_channel(callback, exchange_id, TradesChannel)


async def subscribe_to_order_channel(callback, exchange_id):
    from octobot_trading.channels.orders import OrdersChannel
    await _subscribe_to_channel(callback, exchange_id, OrdersChannel)


async def _subscribe_to_channel(callback, exchange_id, channel):
    from octobot_trading.channels.exchange_channel import get_chan
    channel = get_chan(channel.get_name(), exchange_id)
    await channel.new_consumer(callback)
