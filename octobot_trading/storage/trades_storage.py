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
#  License along with this library
import octobot_commons.channels_name as channels_name
import octobot_commons.enums as commons_enums
import octobot_commons.databases as commons_databases

import octobot_trading.enums as enums
import octobot_trading.storage.abstract_storage as abstract_storage


class TradesStorage(abstract_storage.AbstractStorage):
    LIVE_CHANNEL = channels_name.OctoBotTradingChannelsName.TRADES_CHANNEL.value
    HISTORY_TABLE = commons_enums.DBTables.TRADES.value

    async def _live_callback(
        self,
        exchange: str,
        exchange_id: str,
        cryptocurrency: str,
        symbol: str,
        trade: dict,
        old_trade: bool
    ):
        if trade[enums.ExchangeConstantsOrderColumns.STATUS.value] != enums.OrderStatus.CANCELED.value:
            await self._get_db().log(
                self.HISTORY_TABLE,
                _format_trade(
                    trade,
                    self.exchange_manager,
                    self.plot_settings.chart,
                    self.plot_settings.x_multiplier,
                    self.plot_settings.kind,
                    self.plot_settings.mode
                )
            )

    async def _store_history(self):
        await self._get_db().log_many(
            self.HISTORY_TABLE,
            [
                _format_trade(
                    trade.to_dict(),
                    self.exchange_manager,
                    self.plot_settings.chart,
                    self.plot_settings.x_multiplier,
                    self.plot_settings.kind,
                    self.plot_settings.mode
                )
                for trade in self.exchange_manager.exchange_personal_data.trades_manager.trades.values()
                if trade.status is not enums.OrderStatus.CANCELED
            ]
        )

    def _get_db(self):
        return commons_databases.RunDatabasesProvider.instance().get_trades_db(
            self.exchange_manager.bot_id,
            self.exchange_manager.exchange_name
        )


def _format_trade(trade_dict, exchange_manager, chart, x_multiplier, kind, mode):
    tag = f"{trade_dict[enums.ExchangeConstantsOrderColumns.TAG.value]} " \
        if trade_dict[enums.ExchangeConstantsOrderColumns.TAG.value] else ""
    symbol = trade_dict[enums.ExchangeConstantsOrderColumns.SYMBOL.value]
    trade_side = trade_dict[enums.ExchangeConstantsOrderColumns.SIDE.value]
    is_using_positions = False
    color = shape = None
    if exchange_manager.is_future:
        positions = exchange_manager.exchange_personal_data.positions_manager.get_symbol_positions(symbol=symbol)
        if positions:
            is_using_positions = True
            # trading_side = next(iter(positions)).side
            # if trading_side is enums.PositionSide.LONG:
            if "stop_loss" in trade_dict[enums.ExchangeConstantsOrderColumns.TYPE.value]:
                shape = "x"
                color = "orange"
            elif trade_dict[enums.ExchangeConstantsOrderColumns.REDUCE_ONLY.value] is True:
                if trade_side == enums.TradeOrderSide.SELL.value:
                    # long tp
                    color = "magenta"
                    shape = "arrow-bar-left"
                else:
                    # short tp
                    color = "blue"
                    shape = "arrow-bar-left"
            else:
                if trade_side == enums.TradeOrderSide.BUY.value:
                    # long entry
                    color = "green"
                    shape = "arrow-bar-right"
                else:
                    # short entry
                    color = "red"
                    shape = "arrow-bar-right"

    if not is_using_positions:
        if trade_side == enums.TradeOrderSide.BUY.value:
            color = "blue"
            shape = "arrow-bar-right"
        elif "stop_loss" in trade_dict[enums.ExchangeConstantsOrderColumns.TYPE.value]:
            color = "orange"
            shape = "x"
        else:
            color = "magenta"
            shape = "arrow-bar-left"

    return {
        "x": trade_dict[enums.ExchangeConstantsOrderColumns.TIMESTAMP.value] * x_multiplier,
        "text": f"{tag}{trade_dict[enums.ExchangeConstantsOrderColumns.TYPE.value]} "
                f"{trade_dict[enums.ExchangeConstantsOrderColumns.SIDE.value]} "
                f"{trade_dict[enums.ExchangeConstantsOrderColumns.AMOUNT.value]} "
                f"{trade_dict[enums.ExchangeConstantsOrderColumns.QUANTITY_CURRENCY.value]} "
                f"at {trade_dict[enums.ExchangeConstantsOrderColumns.PRICE.value]}",
        "id": trade_dict[enums.ExchangeConstantsOrderColumns.ID.value],
        "symbol": trade_dict[enums.ExchangeConstantsOrderColumns.SYMBOL.value],
        "trading_mode": exchange_manager.trading_modes[0].get_name(),
        "type": trade_dict[enums.ExchangeConstantsOrderColumns.TYPE.value],
        "volume": float(trade_dict[enums.ExchangeConstantsOrderColumns.AMOUNT.value]),
        "y": float(trade_dict[enums.ExchangeConstantsOrderColumns.PRICE.value]),
        "cost": float(trade_dict[enums.ExchangeConstantsOrderColumns.COST.value]),
        "state": trade_dict[enums.ExchangeConstantsOrderColumns.STATUS.value],
        "chart": chart,
        "kind": kind,
        "side": trade_dict[enums.ExchangeConstantsOrderColumns.SIDE.value],
        "mode": mode,
        "shape": shape,
        "color": color,
        "size": "10",
        "fees_amount": float(trade_dict[enums.ExchangeConstantsOrderColumns.FEE.value]
                             [enums.ExchangeConstantsFeesColumns.COST.value] if
                             trade_dict[enums.ExchangeConstantsOrderColumns.FEE.value] else 0),
        "fees_currency": trade_dict[enums.ExchangeConstantsOrderColumns.FEE.value][
            enums.ExchangeConstantsFeesColumns.CURRENCY.value]
        if trade_dict[enums.ExchangeConstantsOrderColumns.FEE.value] else "",
    }
