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
import octobot_trading.constants as constants


def compute_win_rate(exchange_manager):
    losing_order_types = [
        trading_enums.TradeOrderType.STOP_LOSS,
        trading_enums.TradeOrderType.STOP_LOSS_LIMIT,
    ]
    lost_trades_count = constants.ZERO
    won_trades_count = constants.ZERO
    for trade in exchange_manager.exchange_personal_data.trades_manager.trades.values():
        if trade.status is trading_enums.OrderStatus.FILLED and trade.side is trading_enums.TradeOrderSide.SELL:
            if trade.exchange_trade_type in losing_order_types:
                lost_trades_count += constants.ONE
            else:
                won_trades_count += constants.ONE
    total_counted_trades = won_trades_count + lost_trades_count
    if total_counted_trades > constants.ZERO:
        return won_trades_count / total_counted_trades
    return constants.ZERO if total_counted_trades is constants.ZERO else constants.ONE
