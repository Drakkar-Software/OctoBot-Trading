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
from octobot_trading.enums import PositionSide
import octobot_trading.exchanges as exchanges


class FutureExchange(exchanges.AbstractExchange):
    LONG_STR = "long"
    SHORT_STR = "short"

    # Mark price params
    MARK_PRICE_IN_POSITION = False
    MARK_PRICE_IN_TICKER = False

    # Funding rate params
    FUNDING_WITH_MARK_PRICE = False
    FUNDING_IN_TICKER = False

    async def get_symbol_open_positions(self, symbol: str, **kwargs: dict) -> list:
        """
        Get the current position associated to the symbol
        :param symbol: the symbol
        :return: the user position associated to the symbol
        """
        raise NotImplementedError("get_symbol_open_positions is not implemented")

    async def get_open_positions(self, **kwargs: dict) -> dict:
        """
        Get the user current positions
        :return: the user positions
        """
        raise NotImplementedError("get_open_positions is not implemented")

    async def get_symbol_leverage(self, symbol: str, **kwargs: dict):
        """
        :param symbol: the symbol
        :return: the leverage associated to the symbol
        """
        raise NotImplementedError("get_symbol_leverage is not implemented")

    async def get_mark_price(self, symbol: str, **kwargs: dict) -> dict:
        """
        :param symbol: the symbol
        :return: the current symbol mark price
        """
        raise NotImplementedError("get_mark_price is not implemented")

    async def get_mark_price_history(self, symbol: str, limit: int = 1, **kwargs: dict) -> list:
        """
        Get the mark price history
        :param symbol: the symbol
        :param limit: the history limit size
        :return: the mark price history list
        """
        raise NotImplementedError("get_mark_price_history is not implemented")

    async def get_funding_rate(self, symbol: str, **kwargs: dict) -> dict:
        """
        :param symbol: the symbol
        :return: the current symbol funding rate
        """
        raise NotImplementedError("get_funding_rate is not implemented")

    async def get_funding_rate_history(self, symbol: str, limit: int = 1, **kwargs: dict) -> list:
        """
        :param symbol: the symbol
        :param limit: the history limit size
        :return: the funding rate history
        """
        raise NotImplementedError("get_funding_rate_history is not implemented")

    async def get_mark_price_and_funding(self, symbol: str, **kwargs: dict) -> tuple:
        """
        Returns the exchange mark_price and funding rate when they can be requested together
        :param symbol: the pair to request
        :return: mark_price, funding
        """
        raise NotImplementedError("get_funding_and_mark_price is not implemented")

    async def set_symbol_leverage(self, symbol: str, leverage: int):
        """
        Set the symbol leverage
        :param symbol: the symbol
        :param leverage: the leverage
        :return: the update result
        """
        raise NotImplementedError("set_symbol_leverage is not implemented")

    async def set_symbol_margin_type(self, symbol: str, isolated: bool):
        """
        Set the symbol margin type
        :param symbol: the symbol
        :param isolated: when False, margin type is cross, else it's isolated
        :return: the update result
        """
        raise NotImplementedError("set_symbol_margin_type is not implemented")

    """
    Parsers
    """

    def parse_position(self, position_dict) -> dict:
        """
        :param position_dict: the position dict
        :return: the uniformized position dict
        """
        raise NotImplementedError("parse_position is not implemented")

    def parse_funding(self, funding_dict, from_ticker=False) -> dict:
        """
        :param from_ticker: when True, the funding dict is extracted from ticker data
        :param funding_dict: the funding dict
        :return: the uniformized funding dict
        """
        raise NotImplementedError("parse_funding is not implemented")

    def parse_mark_price(self, mark_price_dict, from_ticker=False) -> dict:
        """
        :param from_ticker: when True, the mark price dict is extracted from ticker data
        :param mark_price_dict: the mark price dict
        :return: the uniformized mark price status
        """
        raise NotImplementedError("parse_mark_price is not implemented")

    def parse_liquidation(self, liquidation_dict) -> dict:
        """
        :param liquidation_dict: the liquidation dict
        :return: the uniformized liquidation dict
        """
        raise NotImplementedError("parse_liquidation is not implemented")

    def parse_position_status(self, status):
        """
        :param status: the position raw status
        :return: the uniformized position status
        """
        raise NotImplementedError("parse_position_status is not implemented")

    def parse_position_side(self, side):
        """
        :param side: the raw side
        :return: the uniformized PositionSide instance from the raw side
        """
        return PositionSide.LONG.value if side == self.LONG_STR else PositionSide.SHORT.value

    def calculate_position_value(self, quantity, mark_price):
        """
        Calculates the position value
        :param quantity: the position quantity
        :param mark_price: the position symbol mark price
        :return: the position value
        """
        if mark_price:
            return quantity / mark_price
        return 0
