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


import octobot_trading.api as api


# Use capital letters to avoid python native lib conflicts
def Open(exchange_manager, symbol, time_frame):
    return _get_candle_manager(exchange_manager, symbol, time_frame).get_symbol_close_candles()


def _get_candle_manager(exchange_manager, symbol, time_frame):
    return api.get_symbol_candles_manager(api.get_symbol_data(exchange_manager, symbol), time_frame)
