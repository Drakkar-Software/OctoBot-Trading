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
            "fees_amount": float(order.origin_quantity * decimal.Decimal("0.1")),  # TODO
            "fees_currency": symbol_util.split_symbol(order.symbol)[1],  # TODO
        }
        for order in orders
    ]
    await ctx.orders_writer.log_many(trading_enums.DBTables.ORDERS.value, order_data)


async def plot_candles(ctx, symbol, time_frame, chart=trading_enums.PlotCharts.MAIN_CHART.value):
    table = trading_enums.DBTables.CANDLES_SOURCE.value
    candles_data = {
        "time_frame": time_frame,
        "value": trading_api.get_backtesting_data_file(ctx.exchange_manager, symbol, commons_enums.TimeFrames(time_frame)) \
            if trading_api.get_is_backtesting(ctx.exchange_manager) else commons_constants.LOCAL_BOT_DATA,
        "chart": chart
    }
    search_query = await ctx.symbol_writer.search()
    if (not ctx.run_data_writer.are_data_initialized and
        await ctx.symbol_writer.count(
            table,
            ((search_query.time_frame == time_frame) & (search_query.value == candles_data["value"]))) == 0):
        await ctx.symbol_writer.log(table, candles_data)


async def plot(ctx, title, x=None,
               y=None, z=None, open=None, high=None, low=None, close=None, volume=None,
               kind="scatter", mode="lines", init_only=True,
               condition=None, x_function=exchange_public_data.Time,
               x_multiplier=1000, time_frame=None,
               chart=trading_enums.PlotCharts.SUB_CHART.value,
               cache_value=None, own_yaxis=False, color=None):
    time_frame = time_frame or ctx.time_frame
    if condition is not None and cache_value is None:
        if isinstance(ctx.symbol_writer.get_serializable_value(condition), bool):
            if condition:
                x = numpy.array((x_function(ctx, ctx.symbol, time_frame)[-1],))
                y = numpy.array((y[-1], ))
            else:
                x = []
                y = []
        else:
            candidate_y = []
            candidate_x = []
            x_data = x_function(ctx, ctx.symbol, time_frame)[-len(condition):]
            y_data = y[-len(condition):]
            for index, value in enumerate(condition):
                if value:
                    candidate_y.append(y_data[index])
                    candidate_x.append(x_data[index])
            x = numpy.array(candidate_x)
            y = numpy.array(candidate_y)
    indicator_query = await ctx.symbol_writer.search()
    # needs parentheses to evaluate the right side of the equality first
    count_query = ((indicator_query.kind == kind)
                    & (indicator_query.mode == mode)
                    & (indicator_query.time_frame == ctx.time_frame))
    if cache_value is not None:
        count_query = ((indicator_query.kind == kind)
                        & (indicator_query.mode == mode)
                        & (indicator_query.time_frame == ctx.time_frame)
                        & (indicator_query.title == title))
    if init_only and not ctx.run_data_writer.are_data_initialized and await ctx.symbol_writer.count(
            trading_enums.DBTables.CACHE_SOURCE.value if cache_value is not None else title,
            count_query) == 0:
        if cache_value is not None:
            cache_dir, cache_path = ctx.get_cache_path()
            table = trading_enums.DBTables.CACHE_SOURCE.value
            cache_identifier = {
                "title": title,
                "time_frame": ctx.time_frame,
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
            # TODO multiple updates on init
            # update = [
            #         ({
            #             "x": value,
            #             "y": ctx.symbol_writer.get_value_from_array(y, index),
            #             "z": ctx.symbol_writer.get_value_from_array(z, index),
            #             "open": ctx.symbol_writer.get_value_from_array(open, index),
            #             "high": ctx.symbol_writer.get_value_from_array(high, index),
            #             "low": ctx.symbol_writer.get_value_from_array(low, index),
            #             "close": ctx.symbol_writer.get_value_from_array(close, index),
            #             "volume": ctx.symbol_writer.get_value_from_array(volume, index),
            #             "time_frame": ctx.time_frame,
            #             "kind": kind,
            #             "mode": mode,
            #             "chart": chart,
            #             "own_yaxis": own_yaxis,
            #             "color": color,
            #         }, (await ctx.symbol_writer.search()).x == value)
            #         for index, value in enumerate(adapted_x)
            #     ]
            # await ctx.symbol_writer.update_many(title, update)
            await ctx.symbol_writer.log_many(
                title,
                [
                    {
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
        x_value = ctx.symbol_writer.get_value_from_array(x, -1) * x_multiplier
        await ctx.symbol_writer.upsert(
            title,
            {
                "time_frame": ctx.time_frame,
                "x": x_value,
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
            },
            (await ctx.symbol_writer.search()).x == x_value
        )


async def plot_shape(ctx, title, value, y_value,
                     chart=trading_enums.PlotCharts.SUB_CHART.value,
                     kind="markers", mode="lines", x_multiplier=1000):
    count_query = await ctx.symbol_writer.search()
    count_query = ((count_query.x == ctx.x)
                    & (count_query.mode == mode)
                    & (count_query.time_frame == ctx.time_frame)
                    & (count_query.kind == kind))
    if ctx.symbol_writer.count(title, count_query) == 0:
        await ctx.symbol_writer.log(
            title,
            {
                "time_frame": ctx.time_frame,
                "x": exchange_public_data.current_time(ctx) * x_multiplier,
                "y": y_value,
                "value": ctx.symbol_writer.get_serializable_value(value),
                "kind": kind,
                "mode": mode,
                "chart": chart,
            }
        )


async def clear_run_data(writer):
    await writer.delete(
        trading_enums.DBTables.METADATA.value,
        None,
    )
    await writer.delete(
        trading_enums.DBTables.PORTFOLIO.value,
        None,
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
