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
import octobot_trading.exchange_channel as exchanges_channel


class PositionsUpdater(positions_channel.PositionsProducer):
    """
    Update positions from exchange
    Can also be used to update a specific positions from exchange
    """

    CHANNEL_NAME = constants.POSITIONS_CHANNEL
    POSITIONS_STARTING_REFRESH_TIME = 12
    POSITION_REFRESH_TIME = 9
    TIME_BETWEEN_POSITIONS_REFRESH = 3

    def __init__(self, channel):
        super().__init__(channel)
        # Warning, when True, might result in missing contract details after bot startup as not every available
        # contract will be loaded (only the ones related to configured symbols will be loaded alongside
        # their position)
        self.should_use_position_per_symbol = False

        # create async jobs
        self.position_update_job = async_job.AsyncJob(self._positions_fetch_and_push,
                                                      execution_interval_delay=self.POSITION_REFRESH_TIME,
                                                      min_execution_delay=self.TIME_BETWEEN_POSITIONS_REFRESH)

    async def initialize(self) -> None:
        """
        Initialize positions and future contracts
        """
        # fetch future contracts from exchange
        await self.initialize_contracts()

        # subscribe to mark_price channel if necessary
        if not self._has_mark_price_in_position():
            await exchanges_channel.get_chan(constants.MARK_PRICE_CHANNEL, self.channel.exchange_manager.id) \
                .new_consumer(self.handle_mark_price)

        # fetch current positions from exchange
        await self.initialize_positions()

        for pair in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
            self.channel.exchange_manager.exchange_personal_data.positions_manager.set_initialized_event(pair)

    async def initialize_contracts(self) -> None:
        """
        Initialize exchange FutureContracts required to manage positions
        """
        for pair in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
            try:
                await self.channel.exchange_manager.exchange.load_pair_future_contract(pair)
            except NotImplementedError as e:
                self.logger.debug(f"Can't to load {pair} contract info from exchange: {e}. "
                                  f"This contract will be created from fetched positions.")
            except Exception as e:
                self.logger.warning(f"Failed to load {pair} contract info : {e}")

    async def initialize_positions(self) -> None:
        """
        Initialize data before starting jobs
        """
        try:
            await self.fetch_and_push()
        except NotImplementedError:
            self.should_use_position_per_symbol = True
            try:
                await self.fetch_and_push()
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
        await self.position_update_job.run()

    async def fetch_and_push(self):
        """
        Update positions from exchange
        """
        await self._positions_fetch_and_push()
        await asyncio.sleep(self.TIME_BETWEEN_POSITIONS_REFRESH)

    async def _positions_fetch_and_push(self):
        """
        Update positions from exchange
        """
        if self.should_use_position_per_symbol:
            await self.fetch_position_per_symbol()
        else:
            await self.fetch_positions()

    def _should_run(self):
        return self.channel.exchange_manager.is_future

    async def fetch_position_per_symbol(self):
        positions = []
        for symbol in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
            fetched_positions = await self.channel.exchange_manager.exchange.get_symbol_positions(symbol=symbol)
            if positions:
                positions += fetched_positions

        if positions:
            self._initialize_contract_if_necessary(positions)
            await self._push_positions(positions)

    def _is_relevant_position(self, position_dict):
        return position_dict and position_dict.get(enums.ExchangeConstantsPositionColumns.SYMBOL.value, None) \
               in self.channel.exchange_manager.exchange_config.traded_symbol_pairs

    async def fetch_positions(self):
        positions = [
            position
            for position in await self.channel.exchange_manager.exchange.get_positions()
        ]

        if positions:
            relevant_positions = [
                position
                for position in positions
                if self._is_relevant_position(position)
            ]
            # initialize relevant contracts first as they might be waited for
            self._initialize_contract_if_necessary(relevant_positions)
            self._initialize_contract_if_necessary(positions)
            # only consider positions that are relevant to the current setup
            await self._push_positions(relevant_positions)

    async def _push_positions(self, positions):
        await self.push(positions)

        if self._should_push_mark_price():
            for position in positions:
                await self.extract_mark_price(position)

    def _initialize_contract_if_necessary(self, positions):
        for position in positions:
            pair = position.get(enums.ExchangeConstantsPositionColumns.SYMBOL.value, None)
            if pair and pair not in self.channel.exchange_manager.exchange.pair_contracts:
                contract = self.channel.exchange_manager.exchange.create_pair_contract(
                    pair=pair,
                    current_leverage=position.get(
                        enums.ExchangeConstantsPositionColumns.LEVERAGE.value, constants.ZERO),
                    margin_type=position.get(enums.ExchangeConstantsPositionColumns.MARGIN_TYPE.value, None),
                    contract_type=position.get(enums.ExchangeConstantsPositionColumns.CONTRACT_TYPE.value, None),
                    position_mode=position.get(enums.ExchangeConstantsPositionColumns.POSITION_MODE.value, None),
                    maintenance_margin_rate=position.get(
                        enums.ExchangeConstantsPositionColumns.MAINTENANCE_MARGIN_RATE.value,
                        constants.DEFAULT_SYMBOL_MAINTENANCE_MARGIN_RATE))
                if not contract.is_handled_contract():
                    message = f"Unhandled contract {contract}. This contract can't be traded"
                    if pair in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
                        # inform user that the contract can't be used
                        self.logger.error(message)
                    else:
                        # no need to inform as the contract is not requested
                        self.logger.debug(message)

    async def extract_mark_price(self, position_dict: dict):
        try:
            await exchanges_channel.get_chan(constants.MARK_PRICE_CHANNEL,
                                             self.channel.exchange_manager.id).get_internal_producer(). \
                push(position_dict[enums.ExchangeConstantsPositionColumns.SYMBOL.value],
                     position_dict[enums.ExchangeConstantsPositionColumns.MARK_PRICE.value])
        except Exception as e:
            self.logger.exception(e, True, f"Fail to update mark price from position : {e}")

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

    def _should_push_mark_price(self):
        return self._has_mark_price_in_position()

    def _has_mark_price_in_position(self):
        return self.channel.exchange_manager.exchange.MARK_PRICE_IN_POSITION

    async def handle_mark_price(self, exchange: str, exchange_id: str, cryptocurrency: str, symbol: str, mark_price):
        """
        MarkPrice channel consumer callback
        """
        try:
            for symbol_position in self.channel.exchange_manager.exchange_personal_data.positions_manager. \
                    get_symbol_positions(symbol=symbol):
                await symbol_position.update(mark_price=mark_price)
        except Exception as e:
            self.logger.exception(e, True, f"Fail to handle mark price : {e}")

    async def stop(self) -> None:
        """
        Stop producer by stopping its jobs
        """
        await super().stop()
        if not self._should_run():
            return
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
