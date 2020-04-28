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

from octobot_trading.constants import OHLCV_CHANNEL
from octobot_trading.channels.exchange_channel import get_chan as get_exchange_chan


async def register_on_ohlcv_chan(exchange_id, callback) -> object:
    """
    Register a consumer on OHLCV channel
    :param exchange_id: the exchange id
    :param callback: the consumer callback
    :return: created consumer instance
    """
    ohlcv_chan = get_exchange_chan(OHLCV_CHANNEL, exchange_id)
    # Before registration, wait for producers to be initialized (meaning their historical candles are already
    # loaded) to avoid callback calls on historical (and potentially invalid) values
    for producer in ohlcv_chan.get_producers():
        await producer.wait_for_initialization()
    return await ohlcv_chan.new_consumer(callback)


async def stop_and_pause(producer) -> None:
    """
    Stop and pause the provided producer
    :param producer: the producer to stop and pause
    """
    await super(type(producer), producer).stop()
    try:
        await producer.pause()
    except KeyError:
        pass
    producer.time_consumer = None
