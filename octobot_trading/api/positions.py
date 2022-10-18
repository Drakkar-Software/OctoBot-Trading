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
import decimal

import octobot_trading.enums as enums


def get_positions(exchange_manager) -> list:
    return exchange_manager.exchange_personal_data.positions_manager.get_symbol_positions()


async def close_position(exchange_manager, symbol: str, side: enums.PositionSide,
                         limit_price: decimal.Decimal = None, emit_trading_signals=True) -> int:
    for position in exchange_manager.exchange_personal_data.positions_manager.get_symbol_positions(symbol):
        if position.side is side:
            if position.is_idle():
                return 0
            return 1 if await exchange_manager.trader.close_position(
                position,
                limit_price=limit_price,
                emit_trading_signals=emit_trading_signals
            ) else 0
    return 0
