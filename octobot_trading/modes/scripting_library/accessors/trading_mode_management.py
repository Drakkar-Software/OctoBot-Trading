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
import octobot_trading.api as trading_api
import octobot_commons.errors as errors


def set_minimum_candles(context, candles_count):
    available_candles = trading_api.get_symbol_candles_count(
        trading_api.get_symbol_data(context.exchange_manager, context.symbol, allow_creation=False),
        context.time_frame
    )
    if available_candles <= candles_count:
        raise errors.MissingDataError(f"Missing candles: available: {available_candles}, required: {candles_count}")
