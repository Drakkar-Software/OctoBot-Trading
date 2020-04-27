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
import copy

from octobot_commons.logging.logging_util import get_logger

from octobot_trading.channels.exchange_channel import get_chan
from octobot_trading.constants import MARK_PRICE_CHANNEL, POSITIONS_CHANNEL
from octobot_trading.data.position import Position
from octobot_trading.enums import PositionStatus
from octobot_trading.producers.positions_updater import PositionsUpdater


class PositionsUpdaterSimulator(PositionsUpdater):
    def __init__(self, channel):
        super().__init__(channel)
        self.exchange_manager = None

    async def start(self):
        self.exchange_manager = self.channel.exchange_manager
        self.logger = get_logger(f"{self.__class__.__name__}[{self.exchange_manager.exchange.name}]")
        await get_chan(MARK_PRICE_CHANNEL, self.channel.exchange_manager.id).new_consumer(self.handle_mark_price)

    async def handle_mark_price(self, exchange: str, exchange_id: str, cryptocurrency: str, symbol: str, mark_price):
        """
        MarkPrice channel consumer callback
        """
        try:
            await self._update_positions_status(cryptocurrency=cryptocurrency, symbol=symbol, mark_price=mark_price)
        except Exception as e:
            self.logger.exception(e, True, f"Fail to handle mark price : {e}")

    async def _update_positions_status(self, cryptocurrency: str, symbol: str, mark_price):
        """
        Ask positions to check their status
        Ask liquidation and P&L update process if required
        """
        for position in copy.copy(
                self.exchange_manager.exchange_personal_data.positions_manager.get_open_positions(symbol=symbol)):
            position_closed = False
            try:
                # ask orders to update their status
                async with position.lock:
                    position_closed = await self._update_position_status(position,
                                                                         mark_price)
            except Exception as e:
                raise e
            finally:
                # ensure always call fill callback
                if position_closed:
                    await get_chan(POSITIONS_CHANNEL, self.channel.exchange_manager.id).get_internal_producer() \
                        .send(cryptocurrency=cryptocurrency,
                              symbol=position.symbol,
                              order=position.to_dict(),
                              is_from_bot=True,
                              is_liquidated=position.is_liquidated(),
                              is_closed=True,
                              is_updated=False)

    async def _update_position_status(self,
                                      position: Position,
                                      mark_price):
        """
        Call position status update
        """
        position_closed = False
        try:
            await position.update_status(mark_price)

            if position.status in (PositionStatus.CLOSED, PositionStatus.LIQUIDATING):
                position_closed = True
                self.logger.debug(f"{position.symbol} (ID : {position.position_id})"
                                  f" closed on {self.channel.exchange.name} "
                                  f"at {position.mark_price} "
                                  f"by {'liquidation' if position.is_liquidated() else 'manual close'}")
                await position.close()
        except Exception as e:
            self.logger.exception(e, True, f"Fail to update position status : {e} (concerned position : {position}).")
        finally:
            return position_closed
