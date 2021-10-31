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

import octobot_trading.modes.scripting_library.data.exchange_public_data as exchange_public_data
import octobot_trading.enums as trading_enums


def store_orders(ctx, orders,
                 chart=trading_enums.PlotCharts.MAIN_CHART.value,
                 x_multiplier=1000):
    order_data = [
        {
            "x": order.creation_time * x_multiplier,
            "pair": order.symbol,
            "type": order.order_type.name if order.order_type is not None else 'Unknown',
            "volume": float(order.origin_quantity),
            "price": float(order.origin_price),
            "state": order.state.state.value if order.state is not None else 'Unknown',
            "chart": chart,
        }
        for order in orders
    ]
    ctx.writer.log_many("orders", order_data)


def plot(ctx, title, x=None,
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
    indicator_query = ctx.writer.search()
    if init_only and not ctx.writer.are_data_initialized and ctx.writer.count(
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
        ctx.writer.log_many(
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
        ctx.writer.log(
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


def store_message(ctx, message, title="messages", y_value=None,
                  chart=trading_enums.PlotCharts.SUB_CHART.value, pair=None,
                  kind="markers", mode="lines", x_multiplier=1000):
    ctx.writer.log(
        title,
        {
            "x": exchange_public_data.current_time(ctx) * x_multiplier,
            "y": exchange_public_data.Close(ctx, pair or ctx.traded_pair, ctx.time_frame),
            "value": message,
            "pair": pair or ctx.traded_pair,
            "kind": kind,
            "mode": mode,
            "chart": chart,
        }
    )


def plot_shape(ctx, title, value, y_value,
               chart=trading_enums.PlotCharts.SUB_CHART.value, pair=None,
               kind="markers", mode="lines", x_multiplier=1000):
    ctx.writer.log(
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

