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
from octobot_trading.exchanges.rest_exchange import RestExchange


class FutureExchange(RestExchange):
    LONG_STR = "long"
    SHORT_STR = "short"

    # Mark price params
    MARK_PRICE_IN_POSITION = False
    MARK_PRICE_IN_TICKER = False

    # Funding rate params
    FUNDING_WITH_MARK_PRICE = False
    FUNDING_IN_TICKER = False

    """
    CCXT future library wrapper
    """
    async def get_symbol_open_positions(self, symbol: str) -> list:
        raise NotImplementedError("get_symbol_open_positions is not implemented")

    async def get_open_positions(self) -> dict:
        raise NotImplementedError("get_open_positions is not implemented")

    async def get_symbol_leverage(self, symbol: str):
        raise NotImplementedError("get_symbol_leverage is not implemented")

    async def get_mark_price(self, symbol: str) -> dict:
        raise NotImplementedError("get_mark_price is not implemented")

    async def get_mark_price_history(self, symbol: str, limit: int = 1) -> list:
        raise NotImplementedError("get_mark_price_history is not implemented")

    async def get_funding_rate(self, symbol: str) -> dict:
        raise NotImplementedError("get_funding_rate is not implemented")

    async def get_funding_rate_history(self, symbol: str, limit: int = 1) -> list:
        raise NotImplementedError("get_funding_rate_history is not implemented")

    async def get_mark_price_and_funding(self, symbol: str) -> tuple:
        """
        Returns the exchange mark_price and funding rate when they can be requested together
        :param symbol: the pair to request
        :return: mark_price, funding
        """
        raise NotImplementedError("get_funding_and_mark_price is not implemented")

    async def set_symbol_leverage(self, symbol: str, leverage: int):
        raise NotImplementedError("set_symbol_leverage is not implemented")

    async def set_symbol_margin_type(self, symbol: str, isolated: bool):
        # If not isolated = cross
        raise NotImplementedError("set_symbol_margin_type is not implemented")

    """
    Parsers
    """
    def parse_position(self, position_dict) -> dict:
        return position_dict

    def parse_funding(self, funding_dict, from_ticker=False) -> dict:
        return funding_dict

    def parse_mark_price(self, mark_price_dict, from_ticker=False) -> dict:
        return mark_price_dict

    def parse_liquidation(self, liquidation_dict) -> dict:
        return liquidation_dict

    def parse_position_status(self, status):
        return status

    def parse_position_side(self, side):
        return PositionSide.LONG.value if side == self.LONG_STR else PositionSide.SHORT.value

    def calculate_position_value(self, quantity, mark_price):
        if mark_price:
            return quantity / mark_price
        return 0
