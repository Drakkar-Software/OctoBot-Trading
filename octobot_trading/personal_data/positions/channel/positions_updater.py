# pylint: disable=E0611
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

import octobot_commons.async_job as async_job

import octobot_trading.errors as errors
import octobot_trading.enums as enums
import octobot_trading.personal_data.positions.channel.positions as positions_channel
import octobot_trading.constants as constants


class PositionsUpdater(positions_channel.PositionsProducer):
    """
    Update open and close positions from exchange
    Can also be used to update a specific positions from exchange
    """

    CHANNEL_NAME = constants.POSITIONS_CHANNEL
    POSITIONS_STARTING_REFRESH_TIME = 12
    OPEN_POSITION_REFRESH_TIME = 9
    CLOSE_POSITION_REFRESH_TIME = 137
    TIME_BETWEEN_POSITIONS_REFRESH = 3

    def __init__(self, channel):
        super().__init__(channel)
        self.should_use_open_position_per_symbol = False

        # create async jobs
        self.open_positions_job = async_job.AsyncJob(self._open_positions_fetch_and_push,
                                                     execution_interval_delay=self.OPEN_POSITION_REFRESH_TIME,
                                                     min_execution_delay=self.TIME_BETWEEN_POSITIONS_REFRESH)
        self.closed_positions_job = async_job.AsyncJob(self._closed_orders_fetch_and_push,
                                                       execution_interval_delay=self.CLOSE_POSITION_REFRESH_TIME,
                                                       min_execution_delay=self.TIME_BETWEEN_POSITIONS_REFRESH)
        self.position_update_job = async_job.AsyncJob(self._position_fetch_and_push,
                                                      is_periodic=False,
                                                      enable_multiple_runs=True)
        self.position_update_job.add_job_dependency(self.open_positions_job)
        self.open_positions_job.add_job_dependency(self.position_update_job)

    async def initialize(self) -> None:
        """
        Initialize data before starting jobs
        """
        try:
            await self.fetch_and_push(is_from_bot=False)
        except NotImplementedError:
            self.should_use_open_position_per_symbol = True
            try:
                await self.fetch_and_push(is_from_bot=False)
            except NotImplementedError:
                self.logger.warning("Position updater cannot fetch positions : required methods are not implemented")
                await self.stop()
        except errors.NotSupported:
            self.logger.warning(f"{self.channel.exchange_manager.exchange_name} is not supporting updates")
            await self.stop()
        except Exception as e:
            self.logger.error(f"Fail to initialize positions : {e}")

    async def start(self):
        """
        Start updater jobs
        """
        if not self._should_run():
            return

        await self.initialize()
        await asyncio.sleep(self.POSITIONS_STARTING_REFRESH_TIME)
        await self.open_positions_job.run()

    async def fetch_and_push(self, is_from_bot=True):
        """
        Update open and closed positions from exchange
        :param is_from_bot: True if the position was created by OctoBot
        :param limit: the exchange request positions count limit
        """
        await self._open_positions_fetch_and_push(is_from_bot=is_from_bot)
        await asyncio.sleep(self.TIME_BETWEEN_POSITIONS_REFRESH)
        await self._closed_orders_fetch_and_push()

    async def _open_positions_fetch_and_push(self, is_from_bot=True):
        """
        Update open positions from exchange
        :param is_from_bot: True if the position was created by OctoBot
        """
        try:
            if self.should_use_open_position_per_symbol:
                await self.fetch_open_position_per_symbol()
            else:
                await self.fetch_open_positions()
            # TODO handle_post_open_position_update
        except Exception as e:
            self.logger.exception(e, True, f"Fail to update open positions : {e}")

    async def _closed_orders_fetch_and_push(self) -> None:
        """
        Update closed positions from exchange
        """
        try:
            if self.should_use_open_position_per_symbol:
                await self.fetch_close_position_per_symbol()
            else:
                await self.fetch_close_positions()
        except Exception as e:
            self.logger.error(f"Fail to update open positions : {e}")

    def _should_run(self):
        return self.channel.exchange_manager.is_future

    async def fetch_open_position_per_symbol(self):
        open_positions = []
        for symbol in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
            positions: list = await self.channel.exchange_manager.exchange.get_symbol_open_positions(symbol=symbol)
            if positions:
                open_positions += positions

        if open_positions:
            await self.push(positions=open_positions, is_closed=False, is_liquidated=False)

    def _is_valid_position(self, position_dict):
        return position_dict and position_dict.get(enums.ExchangeConstantsPositionColumns.SYMBOL.value, None) \
               in self.channel.exchange_manager.exchange_config.traded_symbol_pairs

    async def fetch_open_positions(self):
        open_positions = [
            position
            for position in await self.channel.exchange_manager.exchange.get_open_positions()
            if self._is_valid_position(position)
        ]

        if open_positions:
            await self.push(positions=open_positions, is_closed=False, is_liquidated=False)

    async def fetch_close_position_per_symbol(self):
        pass  # TODO

    async def fetch_close_positions(self):
        pass  # TODO

    async def update_position_from_exchange(self, position,
                                            should_notify=False,
                                            wait_for_refresh=False,
                                            force_job_execution=False,
                                            create_position_producer_if_missing=True):
        """
        Trigger position job refresh from exchange
        :param position: the position to update
        :param wait_for_refresh: if True, wait until the position refresh task to finish
        :param should_notify: if Positions channel consumers should be notified
        :param force_job_execution: When True, position_update_job will bypass its dependencies check
        :param create_position_producer_if_missing: Should be set to False when called by self to prevent spamming
        :return: True if the position was updated
        """
        await self.position_update_job.run(force=True, wait_for_task_execution=wait_for_refresh,
                                           ignore_dependencies_check=force_job_execution,
                                           position=position, should_notify=should_notify)

    async def _position_fetch_and_push(self, position, should_notify=False):
        """
        Update Position from exchange
        :param position: the position to update
        :param should_notify: if Positions channel consumers should be notified
        :return: True if the position was updated
        """
        exchange_name = position.exchange_manager.exchange_name \
            if position.exchange_manager else "cleared order's exchange"
        self.logger.debug(f"Requested update for {position} on {exchange_name}")

        raw_position = await self.channel.exchange_manager.exchange.get_position(position.position_id, position.symbol)
        # TODO manage exchanges without get_position()
        if raw_position is not None:
            self.logger.debug(f"Received update for {position} on {exchange_name}: {raw_position}")
            await self.channel.exchange_manager.exchange_personal_data.handle_position_update_from_raw(
                position.position_id, raw_position, should_notify=should_notify)

    async def stop(self) -> None:
        """
        Stop producer by stopping its jobs
        """
        await super().stop()
        if not self._should_run():
            return
        self.open_positions_job.stop()
        self.closed_positions_job.stop()
        self.position_update_job.stop()

    async def resume(self) -> None:
        """
        Resume producer by restarting its jobs
        """
        await super().resume()
        if not self._should_run():
            return
        if not self.is_running:
            await self.run()
