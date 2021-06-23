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
import async_channel.channels as channels
import octobot_commons.channels_name as channels_name


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


async def pause_time_consumer(producer) -> None:
    """
    Unregister the provided producer's time consumer
    :param producer: the producer to pause
    """
    if producer.time_consumer is not None:
        await channels.get_chan(
            channels_name.OctoBotBacktestingChannelsName.TIME_CHANNEL.value).remove_consumer(producer.time_consumer)


async def resume_time_consumer(producer, producer_time_callback) -> None:
    """
    Register the provided producer's time consumer
    :param producer: the producer to resume
    :param producer_time_callback: the producer TIME_CHANNEL callback
    """
    if producer.time_consumer is None and not producer.channel.is_paused:
        producer.time_consumer = await channels.get_chan(
            channels_name.OctoBotBacktestingChannelsName.TIME_CHANNEL.value).new_consumer(producer_time_callback)
