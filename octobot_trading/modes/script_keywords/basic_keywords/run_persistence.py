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

import octobot_commons.enums as commons_enums
import octobot_commons.databases as commons_databases
import octobot_trading.enums as trading_enums


def set_plot_orders(ctx, value):
    ctx.plot_orders = value


async def disable_candles_plot(ctx, exchange_manager=None):
    storage = (exchange_manager or ctx.exchange_manager).storage_manager.candles_storage
    await storage.enable(False)
    await storage.clear_history()


async def store_orders(ctx, orders, exchange_manager,
                       chart=commons_enums.PlotCharts.MAIN_CHART.value,
                       x_multiplier=1000,
                       mode="markers",
                       kind="scattergl"):
    order_data = [
        {
            "x": order.creation_time * x_multiplier,
            "text": f"{order.order_type.name} {order.origin_quantity} {order.currency} at {order.origin_price}",
            "id": order.order_id,
            "symbol": order.symbol,
            "trading_mode": exchange_manager.trading_modes[0].get_name(),
            "type": order.order_type.name if order.order_type is not None else 'Unknown',
            "volume": float(order.origin_quantity),
            "y": float(order.created_last_price),
            "cost": float(order.total_cost),
            "state": order.state.state.value if order.state is not None else 'Unknown',
            "chart": chart,
            "kind": kind,
            "side": order.side.value,
            "mode": mode,
            "color": "red" if order.side is trading_enums.TradeOrderSide.SELL else "blue",
            "size": "10",
            "shape": "arrow-bar-left" if order.side is trading_enums.TradeOrderSide.SELL else "arrow-bar-right"
        }
        for order in orders
    ]
    await ctx.orders_writer.log_many(commons_enums.DBTables.ORDERS.value, order_data)


async def clear_orders_cache(writer):
    await _clear_table(writer, commons_enums.DBTables.ORDERS.value)
    await writer.clear()


async def clear_symbol_plot_cache(writer):
    await _clear_table(writer, commons_enums.DBTables.CACHE_SOURCE.value)
    await writer.clear()


async def _clear_table(writer, table, flush=True):
    await writer.delete(table, None)
    if flush:
        await writer.flush()


def get_shared_element(key):
    return commons_databases.GlobalSharedMemoryStorage.instance()[key]


def set_shared_element(key, element):
    commons_databases.GlobalSharedMemoryStorage.instance()[key] = element
