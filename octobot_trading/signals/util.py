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
import octobot_trading.enums as trading_enums


def get_signal_exchange_type(exchange_manager):
    if exchange_manager.is_spot_only:
        return trading_enums.TradingSignalExchangeTypes.SPOT
    if exchange_manager.is_future:
        return trading_enums.TradingSignalExchangeTypes.FUTURE
    if exchange_manager.is_margin:
        return trading_enums.TradingSignalExchangeTypes.MARGIN
    return trading_enums.TradingSignalExchangeTypes.UNKNOWN
