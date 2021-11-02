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
import numpy

import octobot_trading.modes.scripting_library.data.reading.exchange_public_data as exchange_public_data
import octobot_trading.enums as trading_enums
import octobot_trading.api as trading_api


async def store_orders(ctx, orders,
                       chart=trading_enums.PlotCharts.MAIN_CHART.value,
                       x_multiplier=1000,
                       kind="markers",
                       mode="lines"):
    order_data = [
        {
            "x": order.creation_time * x_multiplier,
            "pair": order.symbol,
            "type": order.order_type.name if order.order_type is not None else 'Unknown',
            "volume": float(order.origin_quantity),
            "y": float(order.created_last_price),
            "state": order.state.state.value if order.state is not None else 'Unknown',
            "chart": chart,
            "kind": kind,
            "side": order.side.value,
            "mode": mode,
        }
        for order in orders
    ]
    await ctx.writer.log_many(trading_enums.DBTables.ORDERS.value, order_data)


async def plot(ctx, title, x=None,
               y=None, z=None, open=None, high=None, low=None, close=None, volume=None,
               pair=None, kind="scatter", mode="lines", init_only=True,
               condition=None, x_function=exchange_public_data.Time,
               x_multiplier=1000,
               chart=trading_enums.PlotCharts.SUB_CHART.value):
    if condition is not None:
        candidate_y = []
        candidate_x = []
        x_data = x_function(ctx, ctx.traded_pair, ctx.time_frame)
        for index, value in enumerate(condition):
            if value:
                candidate_y.append(y[index])
                candidate_x.append(x_data[index])
        x = numpy.array(candidate_x)
        y = numpy.array(candidate_y)
    indicator_query = await ctx.writer.search()
    if init_only and not ctx.writer.are_data_initialized and await ctx.writer.count(
            title,
            # needs parentheses to evaluate the right side of the equality first
            (indicator_query.pair == (pair or ctx.traded_pair))
            & (indicator_query.kind == kind)
            & (indicator_query.mode == mode)) == 0:
        adapted_x = None
        if x is not None:
            min_available_data = len(x)
            if y is not None:
                min_available_data = len(y)
            if z is not None:
                min_available_data = min(min_available_data, len(z))
            adapted_x = x[-min_available_data:] if min_available_data != len(x) else x
        if adapted_x is None:
            raise RuntimeError("No confirmed adapted_x")
        adapted_x = adapted_x * x_multiplier
        await ctx.writer.log_many(
            title,
            [
                {
                    "pair": pair or ctx.traded_pair,
                    "x": value,
                    "y": ctx.writer.get_value_from_array(y, index),
                    "z": ctx.writer.get_value_from_array(z, index),
                    "open": ctx.writer.get_value_from_array(open, index),
                    "high": ctx.writer.get_value_from_array(high, index),
                    "low": ctx.writer.get_value_from_array(low, index),
                    "close": ctx.writer.get_value_from_array(close, index),
                    "volume": ctx.writer.get_value_from_array(volume, index),
                    "kind": kind,
                    "mode": mode,
                    "chart": chart,
                }
                for index, value in enumerate(adapted_x)
            ]

        )
    else:
        await ctx.writer.log(
            title,
            {
                "pair": pair or ctx.traded_pair,
                "x": ctx.writer.get_value_from_array(x, -1) * x_multiplier,
                "y": ctx.writer.get_value_from_array(y, -1),
                "z": ctx.writer.get_value_from_array(z, -1),
                "open": ctx.writer.get_value_from_array(open, -1),
                "high": ctx.writer.get_value_from_array(high, -1),
                "low": ctx.writer.get_value_from_array(low, -1),
                "close": ctx.writer.get_value_from_array(close, -1),
                "volume": ctx.writer.get_value_from_array(volume, -1),
                "kind": kind,
                "mode": mode,
                "chart": chart,
            }
        )


async def plot_shape(ctx, title, value, y_value,
               chart=trading_enums.PlotCharts.SUB_CHART.value, pair=None,
               kind="markers", mode="lines", x_multiplier=1000):
    await ctx.writer.log(
        title,
        {
            "x": exchange_public_data.current_time(ctx) * x_multiplier,
            "y": y_value,
            "value": ctx.writer.get_serializable_value(value),
            "pair": pair or ctx.traded_pair,
            "kind": kind,
            "mode": mode,
            "chart": chart,
        }
    )


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
