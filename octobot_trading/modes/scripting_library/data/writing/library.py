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

import numpy

import octobot_trading.modes.scripting_library.data.reading.exchange_public_data as exchange_public_data
import octobot_trading.enums as trading_enums
import octobot_trading.constants as trading_constants
import octobot_trading.api as trading_api
import octobot_commons.symbol_util as symbol_util
import octobot_commons.enums as commons_enums


async def store_orders(ctx, orders,
                       chart=trading_enums.PlotCharts.MAIN_CHART.value,
                       x_multiplier=1000,
                       kind="markers",
                       mode="lines"):
    order_data = [
        {
            trading_enums.PlotDBKeys.X.value: order.creation_time * x_multiplier,
            trading_enums.PlotDBKeys.PAIR.value: order.symbol,
            trading_enums.PlotDBKeys.TYPE.value: order.order_type.name if order.order_type is not None else 'Unknown',
            trading_enums.PlotDBKeys.VOLUME.value: float(order.origin_quantity),
            trading_enums.PlotDBKeys.Y.value: float(order.created_last_price),
            trading_enums.PlotDBKeys.STATE.value: order.state.state.value if order.state is not None else 'Unknown',
            trading_enums.PlotDBKeys.CHART.value: chart,
            trading_enums.PlotDBKeys.KIND.value: kind,
            trading_enums.PlotDBKeys.SIDE.value: order.side.value,
            trading_enums.PlotDBKeys.MODE.value: mode,
            trading_enums.PlotDBKeys.FEES_AMOUNT.value: float(order.origin_quantity * decimal.Decimal("0.1")),  # TODO
            trading_enums.PlotDBKeys.FEES_CURRENCY.value: symbol_util.split_symbol(order.symbol)[1],  # TODO
        }
        for order in orders
    ]
    await ctx.writer.log_many(trading_enums.DBTables.ORDERS.value, order_data)


async def plot_candles(ctx, pair, time_frame, chart=trading_enums.PlotCharts.MAIN_CHART.value):
    table = trading_enums.DBTables.CANDLES_SOURCE.value
    candles_identifier = {
        "pair": pair,
        "time_frame": time_frame,
        "exchange": ctx.exchange_name
    }
    if not (ctx.writer.are_data_initialized or
            ctx.writer.contains_values(table, candles_identifier)):
        candles_identifier["value"] =  \
            trading_api.get_backtesting_data_file(ctx.exchange_manager, pair, commons_enums.TimeFrames(time_frame)) \
            if trading_api.get_is_backtesting(ctx.exchange_manager) else trading_constants.LOCAL_BOT_DATA
        candles_identifier["chart"] = chart
        await ctx.writer.log(table, candles_identifier)


async def plot(ctx, title, x=None,
               y=None, z=None, open=None, high=None, low=None, close=None, volume=None,
               pair=None, kind=trading_enums.PlotDefaultValues.KIND.value,
               mode=trading_enums.PlotDefaultValues.MODE.value, init_only=True,
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
                _get_plotting_data(ctx, pair or ctx.traded_pair, value, y, z, open, high, low, close, volume, index,
                                   kind, mode, x_multiplier, chart)
                for index, value in enumerate(adapted_x)
            ]

        )
    elif not ctx.writer.contains_x(title, ctx.writer.get_value_from_array(x, -1) * x_multiplier):
        await ctx.writer.log(
            title,
            _get_plotting_data(ctx, pair, x, y, z, open, high, low, close, volume, -1, kind, mode, x_multiplier, chart)
        )


def _get_plotting_data(ctx, pair, x, y, z, open, high, low, close, volume, index,
                       kind=trading_enums.PlotDefaultValues.KIND.value,
                       mode=trading_enums.PlotDefaultValues.MODE.value,
                       x_multiplier=1000, chart=trading_enums.PlotCharts.SUB_CHART.value):
    data = {}
    if pair := pair or ctx.traded_pair:
        data[trading_enums.PlotDBKeys.PAIR.value] = pair
    if x is not None and len(x):
        data[trading_enums.PlotDBKeys.X.value] = ctx.writer.get_value_from_array(x, index) * x_multiplier
    if y is not None and len(y):
        data[trading_enums.PlotDBKeys.Y.value] = ctx.writer.get_value_from_array(y, index)
    if z is not None and len(z):
        data[trading_enums.PlotDBKeys.Z.value] = ctx.writer.get_value_from_array(z, index),
    if open is not None and len(open):
        data[trading_enums.PlotDBKeys.OPEN.value] = ctx.writer.get_value_from_array(open, index)
    if high is not None and len(high):
        data[trading_enums.PlotDBKeys.HIGH.value] = ctx.writer.get_value_from_array(high, index)
    if low is not None and len(low):
        data[trading_enums.PlotDBKeys.LOW.value] = ctx.writer.get_value_from_array(low, index)
    if close is not None and len(close):
        data[trading_enums.PlotDBKeys.CLOSE.value] = ctx.writer.get_value_from_array(close, index)
    if volume is not None and len(volume):
        data[trading_enums.PlotDBKeys.VOLUME.value] = ctx.writer.get_value_from_array(volume, index)
    if kind != trading_enums.PlotDefaultValues.KIND.value:
        data[trading_enums.PlotDBKeys.KIND.value] = kind
    if mode != trading_enums.PlotDefaultValues.MODE.value:
        data[trading_enums.PlotDBKeys.MODE.value] = mode
    if chart != trading_enums.PlotCharts.SUB_CHART.value:
        data[trading_enums.PlotDBKeys.CHART.value] = chart
    return data


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
