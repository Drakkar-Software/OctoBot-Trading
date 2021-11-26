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
import decimal
import os

import numpy

import octobot_trading.modes.scripting_library.data.reading.exchange_public_data as exchange_public_data
import octobot_trading.enums as trading_enums
import octobot_trading.api as trading_api
import octobot_commons.symbol_util as symbol_util
import octobot_commons.enums as commons_enums
import octobot_commons.constants as commons_constants


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
            "color": "red" if order.side is trading_enums.TradeOrderSide.SELL else "blue",
            "fees_amount": float(order.origin_quantity * decimal.Decimal("0.1")),  # TODO
            "fees_currency": symbol_util.split_symbol(order.symbol)[1],  # TODO
        }
        for order in orders
    ]
    await ctx.orders_writer.log_many(trading_enums.DBTables.ORDERS.value, order_data)


async def plot_candles(ctx, pair, time_frame, chart=trading_enums.PlotCharts.MAIN_CHART.value):
    table = trading_enums.DBTables.CANDLES_SOURCE.value
    candles_identifier = {
        "pair": pair,
        "time_frame": time_frame,
        "exchange": ctx.exchange_name
    }
    if not (ctx.run_data_writer.are_data_initialized or
            ctx.symbol_writer.contains_values(table, candles_identifier)):
        candles_identifier["value"] =  \
            trading_api.get_backtesting_data_file(ctx.exchange_manager, pair, commons_enums.TimeFrames(time_frame)) \
            if trading_api.get_is_backtesting(ctx.exchange_manager) else commons_constants.LOCAL_BOT_DATA
        candles_identifier["chart"] = chart
        await ctx.symbol_writer.log(table, candles_identifier)


async def plot(ctx, title, x=None,
               y=None, z=None, open=None, high=None, low=None, close=None, volume=None,
               pair=None, kind="scatter", mode="lines", init_only=True,
               condition=None, x_function=exchange_public_data.Time,
               x_multiplier=1000,
               chart=trading_enums.PlotCharts.SUB_CHART.value,
               cache_value=None, own_yaxis=False, color=None):
    if condition is not None and cache_value is None:
        if isinstance(ctx.symbol_writer.get_serializable_value(condition), bool):
            if condition:
                x = numpy.array((x_function(ctx, ctx.traded_pair, ctx.time_frame)[-1], ))
                y = numpy.array((y[-1], ))
            else:
                x = []
                y = []
        else:
            candidate_y = []
            candidate_x = []
            x_data = x_function(ctx, ctx.traded_pair, ctx.time_frame)[-len(condition):]
            y_data = y[-len(condition):]
            for index, value in enumerate(condition):
                if value:
                    candidate_y.append(y_data[index])
                    candidate_x.append(x_data[index])
            x = numpy.array(candidate_x)
            y = numpy.array(candidate_y)
    indicator_query = await ctx.symbol_writer.search()
    if init_only and not ctx.run_data_writer.are_data_initialized and await ctx.symbol_writer.count(
            title,
            # needs parentheses to evaluate the right side of the equality first
            (indicator_query.pair == (pair or ctx.traded_pair))
            & (indicator_query.kind == kind)
            & (indicator_query.mode == mode)) == 0:
        if cache_value is not None:
            cache_dir, cache_path = ctx.get_cache_path()
            table = trading_enums.DBTables.CACHE_SOURCE.value
            cache_identifier = {
                "title": title,
                "pair": pair or ctx.traded_pair,
                "time_frame": ctx.time_frame,
                "exchange": ctx.exchange_name,
                "value": os.path.join(cache_dir, cache_path),
                "cache_value": cache_value,
                "kind": kind,
                "mode": mode,
                "chart": chart,
                "own_yaxis": own_yaxis,
                "condition": condition,
                "color": color,
            }
            await ctx.symbol_writer.log(table, cache_identifier)
        else:
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
            await ctx.symbol_writer.log_many(
                title,
                [
                    {
                        "pair": pair or ctx.traded_pair,
                        "x": value,
                        "y": ctx.symbol_writer.get_value_from_array(y, index),
                        "z": ctx.symbol_writer.get_value_from_array(z, index),
                        "open": ctx.symbol_writer.get_value_from_array(open, index),
                        "high": ctx.symbol_writer.get_value_from_array(high, index),
                        "low": ctx.symbol_writer.get_value_from_array(low, index),
                        "close": ctx.symbol_writer.get_value_from_array(close, index),
                        "volume": ctx.symbol_writer.get_value_from_array(volume, index),
                        "time_frame": ctx.time_frame,
                        "kind": kind,
                        "mode": mode,
                        "chart": chart,
                        "own_yaxis": own_yaxis,
                        "color": color,
                    }
                    for index, value in enumerate(adapted_x)
                ]

            )
    elif cache_value is None and x is not None and len(x) \
            and not ctx.symbol_writer.contains_x(title, ctx.symbol_writer.get_value_from_array(x, -1) * x_multiplier):
        await ctx.symbol_writer.log(
            title,
            {
                "pair": pair or ctx.traded_pair,
                "time_frame": ctx.time_frame,
                "x": ctx.symbol_writer.get_value_from_array(x, -1) * x_multiplier,
                "y": ctx.symbol_writer.get_value_from_array(y, -1),
                "z": ctx.symbol_writer.get_value_from_array(z, -1),
                "open": ctx.symbol_writer.get_value_from_array(open, -1),
                "high": ctx.symbol_writer.get_value_from_array(high, -1),
                "low": ctx.symbol_writer.get_value_from_array(low, -1),
                "close": ctx.symbol_writer.get_value_from_array(close, -1),
                "volume": ctx.symbol_writer.get_value_from_array(volume, -1),
                "kind": kind,
                "mode": mode,
                "chart": chart,
                "own_yaxis": own_yaxis,
                "color": color,
            }
        )


async def plot_shape(ctx, title, value, y_value,
                     chart=trading_enums.PlotCharts.SUB_CHART.value, pair=None,
                     kind="markers", mode="lines", x_multiplier=1000):
    await ctx.symbol_writer.log(
        title,
        {
            "x": exchange_public_data.current_time(ctx) * x_multiplier,
            "y": y_value,
            "value": ctx.symbol_writer.get_serializable_value(value),
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
