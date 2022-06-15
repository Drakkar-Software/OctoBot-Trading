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
import octobot_trading.personal_data as personal_data


_LOSING_ORDER_TYPES = [
    trading_enums.TradeOrderType.STOP_LOSS,
    trading_enums.TradeOrderType.STOP_LOSS_LIMIT,
]


def compute_win_rate(exchange_manager):
    lost_trades_count = constants.ZERO
    won_trades_count = constants.ZERO
    entries = constants.ZERO
    if exchange_manager.is_future:
        for trade in exchange_manager.exchange_personal_data.trades_manager.trades.values():
            if trade.status is trading_enums.OrderStatus.FILLED:
                if trade.reduce_only:
                    if trade.exchange_trade_type in _LOSING_ORDER_TYPES:
                        lost_trades_count += constants.ONE
                    else:
                        won_trades_count += constants.ONE
                else:
                    entries += constants.ONE
        total_exits = lost_trades_count + won_trades_count
        if total_exits > entries:
            # multiple take profits and SL not handled yet
            win_rate = constants.ZERO
        else:
            win_rate = won_trades_count / total_exits if total_exits else constants.ZERO
        if win_rate != constants.ZERO:
            return win_rate
        else:  # try fallback to transactions for trailing stops and multiple exits
            lost_trades_count = constants.ZERO
            won_trades_count = constants.ZERO
            for transaction in exchange_manager.exchange_personal_data.transactions_manager.transactions.values():
                if isinstance(transaction, personal_data.RealisedPnlTransaction) and transaction.is_closed_pnl():
                    if (transaction.side is trading_enums.PositionSide.SHORT and
                            transaction.average_entry_price > transaction.average_exit_price) or (
                        transaction.side is trading_enums.PositionSide.LONG and
                            transaction.average_entry_price < transaction.average_exit_price
                    ):
                        won_trades_count += constants.ONE
                    else:
                        lost_trades_count += constants.ONE
    else:
        for trade in exchange_manager.exchange_personal_data.trades_manager.trades.values():
            if trade.status is trading_enums.OrderStatus.FILLED and trade.side is trading_enums.TradeOrderSide.SELL:
                if trade.exchange_trade_type in _LOSING_ORDER_TYPES:
                    lost_trades_count += constants.ONE
                else:
                    won_trades_count += constants.ONE
    total_counted_trades = won_trades_count + lost_trades_count
    if total_counted_trades > constants.ZERO:
        return won_trades_count / total_counted_trades
    return constants.ZERO
