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


def get_trade_history(exchange_manager, symbol=None) -> list:
    if symbol is None:
        return exchange_manager.exchange_personal_data.trades_manager.trades.values()
    else:
        return [trade
                for trade in exchange_manager.exchange_personal_data.trades_manager.trades.values()
                if trade.symbol == symbol]


def get_total_paid_trading_fees(exchange_manager) -> dict:
    return exchange_manager.exchange_personal_data.trades_manager.get_total_paid_fees()


def get_trade_exchange_name(trade) -> str:
    return trade.exchange_manager.get_exchange_name()


def is_trade_simulated(trade) -> bool:
    return trade.trader.simulate
