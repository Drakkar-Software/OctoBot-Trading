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

import octobot_commons.symbol_util as symbol_util
import octobot_trading.enums as trading_enums
import octobot_trading.api as trading_api


def set_plot_orders(ctx, value):
    ctx.plot_orders = value


async def store_orders(ctx, orders,
                       chart=trading_enums.PlotCharts.MAIN_CHART.value,
                       x_multiplier=1000,
                       kind="markers",
                       mode="lines"):
    order_data = [
        {
            "x": order.creation_time * x_multiplier,
            "text": f"{order.order_type.name} {order.origin_quantity} {order.currency} at {order.origin_price}",
            "id": order.order_id,
            "symbol": order.symbol,
            "type": order.order_type.name if order.order_type is not None else 'Unknown',
            "volume": float(order.origin_quantity),
            "y": float(order.created_last_price),
            "state": order.state.state.value if order.state is not None else 'Unknown',
            "chart": chart,
            "kind": kind,
            "side": order.side.value,
            "mode": mode,
            "color": "red" if order.side is trading_enums.TradeOrderSide.SELL else "blue",
        }
        for order in orders
    ]
    await ctx.orders_writer.log_many(trading_enums.DBTables.ORDERS.value, order_data)


async def store_trade(ctx,
                      trade_dict,
                      chart=trading_enums.PlotCharts.MAIN_CHART.value,
                      x_multiplier=1000,
                      kind="markers",
                      mode="lines",
                      writer=None):
    tag = f"{trade_dict[trading_enums.ExchangeConstantsOrderColumns.TAG.value]} " \
        if trade_dict[trading_enums.ExchangeConstantsOrderColumns.TAG.value] else ""
    trade_data = {
        "x": trade_dict[trading_enums.ExchangeConstantsOrderColumns.TIMESTAMP.value] * x_multiplier,
        "text": f"{tag}{trade_dict[trading_enums.ExchangeConstantsOrderColumns.TYPE.value]} "
                f"{trade_dict[trading_enums.ExchangeConstantsOrderColumns.SIDE.value]} "
                f"{trade_dict[trading_enums.ExchangeConstantsOrderColumns.AMOUNT.value]} "
                f"{symbol_util.split_symbol(trade_dict[trading_enums.ExchangeConstantsOrderColumns.SYMBOL.value])[0]} "
                f"at {trade_dict[trading_enums.ExchangeConstantsOrderColumns.PRICE.value]}",
        "id": trade_dict[trading_enums.ExchangeConstantsOrderColumns.ID.value],
        "symbol": trade_dict[trading_enums.ExchangeConstantsOrderColumns.SYMBOL.value],
        "type": trade_dict[trading_enums.ExchangeConstantsOrderColumns.TYPE.value],
        "volume": float(trade_dict[trading_enums.ExchangeConstantsOrderColumns.AMOUNT.value]),
        "y": float(trade_dict[trading_enums.ExchangeConstantsOrderColumns.PRICE.value]),
        "state": trade_dict[trading_enums.ExchangeConstantsOrderColumns.STATUS.value],
        "chart": chart,
        "kind": kind,
        "side": trade_dict[trading_enums.ExchangeConstantsOrderColumns.SIDE.value],
        "mode": mode,
        "color": "red" if trade_dict[trading_enums.ExchangeConstantsOrderColumns.SIDE.value] ==
        trading_enums.TradeOrderSide.SELL.value else "blue",
        "fees_amount": float(trade_dict[trading_enums.ExchangeConstantsOrderColumns.FEE.value]
                             [trading_enums.ExchangeConstantsFeesColumns.COST.value] if
                             trade_dict[trading_enums.ExchangeConstantsOrderColumns.FEE.value] else 0),
        "fees_currency": trade_dict[trading_enums.ExchangeConstantsOrderColumns.FEE.value][
            trading_enums.ExchangeConstantsFeesColumns.CURRENCY.value]
            if trade_dict[trading_enums.ExchangeConstantsOrderColumns.FEE.value] else "",
    }
    writer = writer or ctx.trades_writer
    await writer.log(trading_enums.DBTables.TRADES.value, trade_data)


async def save_metadata(writer, metadata):
    await writer.log(
        trading_enums.DBTables.METADATA.value,
        metadata
    )


async def save_portfolio(writer, context):
    await writer.log(
        trading_enums.DBTables.PORTFOLIO.value,
        trading_api.get_portfolio(context.exchange_manager, as_decimal=False)
    )


async def clear_run_data(writer):
    await _clear_table(writer, trading_enums.DBTables.METADATA.value, flush=False)
    await _clear_table(writer, trading_enums.DBTables.PORTFOLIO.value, flush=False)
    await writer.clear()


async def clear_orders_cache(writer):
    await _clear_table(writer, trading_enums.DBTables.ORDERS.value)
    await writer.clear()


async def clear_trades_cache(writer):
    await _clear_table(writer, trading_enums.DBTables.TRADES.value)
    await writer.clear()


async def clear_all_tables(writer_reader):
    for table in await writer_reader.tables():
        await _clear_table(writer_reader, table)
    await writer_reader.clear()


async def _clear_table(writer, table, flush=True):
    await writer.delete(table, None)
    if flush:
        await writer.flush()
