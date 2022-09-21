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
import collections

import octobot_commons.logging as logging
import octobot_commons.enums as commons_enums
import octobot_commons.tree as commons_tree

import octobot_trading.personal_data.positions.position_factory as position_factory
import octobot_trading.util as util
import octobot_trading.enums as enums


class PositionsManager(util.Initializable):
    POSITION_ID_SEPARATOR = "_"

    def __init__(self, trader):
        super().__init__()
        self.logger = logging.get_logger(self.__class__.__name__)
        self.trader = trader
        self.positions = collections.OrderedDict()

    async def initialize_impl(self):
        self._reset_positions()

    def get_symbol_position(self, symbol, side):
        """
        Returns or create the symbol position instance
        :param symbol: the position symbol
        :param side: the position side
        :return: the existing position or the newly created position
        """
        return self._get_or_create_position(symbol=symbol, side=side)

    def get_order_position(self, order, contract=None):
        """
        Returns the position that matches the order
        :param order: the order
        :param contract: the symbol contract (optional)
        :return: the existing position or the newly created position that matches the order
        """
        future_contract = contract if contract is not None \
            else self.trader.exchange_manager.exchange.get_pair_future_contract(order.symbol)
        return self.get_symbol_position(symbol=order.symbol,
                                        side=None if future_contract.is_one_way_position_mode()
                                        else order.get_position_side(future_contract))

    def get_symbol_positions(self, symbol=None):
        """
        Returns symbol positions if exist
        :param symbol: the position symbol
        :return: the symbol positions
        """
        if symbol is None:
            return list(self.positions.values())
        return self._get_symbol_positions(symbol)

    async def upsert_position(self, symbol: str, side, raw_position: dict) -> bool:
        """
        Create or update a position from a raw dictionary
        :param symbol: the position symbol
        :param side: the position side
        :param raw_position: the position raw dictionary
        :return: True when the creation or the update succeeded
        """
        position_id = self._generate_position_id(symbol=symbol, side=side)
        if position_id not in self.positions:
            new_position = position_factory.create_position_instance_from_raw(self.trader, raw_position=raw_position)
            new_position.position_id = position_id
            return await self._finalize_position_creation(new_position, is_from_exchange_data=True)

        return self.positions[position_id].update_from_raw(raw_position)

    def set_initialized_event(self, symbol):
        commons_tree.EventProvider.instance().trigger_event(
            self.trader.exchange_manager.bot_id, commons_tree.get_exchange_path(
                self.trader.exchange_manager.exchange_name,
                commons_enums.InitializationEventExchangeTopics.POSITIONS.value,
                symbol=symbol
            )
        )

    async def recreate_position(self, position) -> bool:
        """
        Recreate position from an existing position instance
        :param position: the position instance to recreate
        :return: True when the recreation succeeded
        """
        new_position = position_factory.create_position_instance_from_raw(self.trader, raw_position=position.to_dict())
        position.clear()
        position.position_id = self._generate_position_id(symbol=position.symbol, side=position.side)
        return await self._finalize_position_creation(new_position)

    def upsert_position_instance(self, position) -> bool:
        """
        Save an existing position instance to positions list
        :param position: the position instance
        :return: True when the operation succeeded
        """
        if position.position_id not in self.positions:
            self.positions[position.position_id] = position
            return True
        return False

    def clear(self):
        """
        Clear all positions and the position OrderedDict
        """
        for position in self.positions.values():
            position.clear()
        self._reset_positions()

    # private
    def _generate_position_id(self, symbol, side, expiration_time=None):
        """
        Generate a position ID for one way and hedge position modes
        :param symbol: the position symbol
        :param side: the position side
        :param expiration_time: the symbol expiration timestamp
        :return: the computed position id
        """
        return f"{symbol}" \
               f"{'' if expiration_time is None else self.POSITION_ID_SEPARATOR + str(expiration_time)}" \
               f"{'' if side is enums.PositionSide.BOTH or side is None else self.POSITION_ID_SEPARATOR + side.value}"

    async def _finalize_position_creation(self, new_position, is_from_exchange_data=False) -> bool:
        """
        Ends a position creation process
        :param new_position: the new position instance
        :param is_from_exchange_data: True when the exchange creation comes from exchange data
        :return: True when the process succeeded
        """
        self.positions[new_position.position_id] = new_position
        await new_position.initialize(is_from_exchange_data=is_from_exchange_data)
        return True

    def _create_symbol_position(self, symbol, position_id):
        """
        Creates a position when it doesn't exist for the specified symbol
        :param symbol: the new position symbol
        :param side: the new position id
        :return: the new symbol position instance
        """
        new_position = position_factory.create_symbol_position(self.trader, symbol)
        new_position.position_id = position_id
        self.positions[position_id] = new_position
        return new_position

    def _get_or_create_position(self, symbol, side):
        """
        Get or create position by symbol and side
        :param symbol: the expected position symbol
        :param side: the expected position side
        :return: the matching position
        """
        expected_position_id = self._generate_position_id(symbol=symbol, side=side)
        try:
            return self.positions[expected_position_id]
        except KeyError:
            self.positions[expected_position_id] = self._create_symbol_position(symbol, expected_position_id)
        return self.positions[expected_position_id]

    def _get_symbol_positions(self, symbol):
        """
        Get symbol positions in each side
        :param symbol: the position symbol
        :return: existing symbol positions list
        """
        positions = []
        for side in [enums.PositionSide.BOTH, enums.PositionSide.SHORT, enums.PositionSide.LONG]:
            position_id = self._generate_position_id(symbol=symbol, side=side)
            try:
                positions.append(self.positions[position_id])
            except KeyError:
                pass
        return positions

    def _reset_positions(self):
        """
        Clear all position references
        """
        self.positions = collections.OrderedDict()
