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
import copy

import octobot_trading.enums as trading_enums
import octobot_commons.symbol_util as symbol_util
import octobot_commons.constants


async def get_candles(reader, pair):
    return await reader.select(trading_enums.DBTables.CANDLES.value, ((await reader.search()).pair == pair))


async def get_trades(reader, pair):
    return await reader.select(trading_enums.DBTables.ORDERS.value, (await reader.search()).pair == pair)


async def get_metadata(reader):
    return (await reader.all(trading_enums.DBTables.METADATA.value))[0]


async def get_starting_portfolio(reader) -> dict:
    return (await reader.all(trading_enums.DBTables.PORTFOLIO.value))[0]


async def plot_historical_portfolio_value(reader, plotted_element):
    starting_portfolio = await get_starting_portfolio(reader)
    price_data = {}
    trades_data = {}
    moving_portfolio_data = {}
    metadata = await get_metadata(reader)
    ref_market = metadata[trading_enums.DBRows.REFERENCE_MARKET.value]
    # init data
    for symbol, values in starting_portfolio.items():
        if symbol != ref_market:
            pair = symbol_util.merge_currencies(symbol, ref_market)
            if pair not in price_data:
                price_data[pair] = await get_candles(reader, pair)
            if pair not in trades_data:
                trades_data[pair] = await get_trades(reader, pair)
        moving_portfolio_data[symbol] = values[octobot_commons.constants.PORTFOLIO_TOTAL]
    time_data = []
    value_data = []
    for pair, candles in price_data.items():
        symbol, ref_market = symbol_util.split_symbol(pair)
        if candles and not time_data:
            time_data = [candle[trading_enums.PlotAttributes.X.value] for candle in candles]
            value_data = [0] * len(candles)
        for index, candle in enumerate(candles):
            print(candle)
            value_data[index] = \
                value_data[index] + \
                moving_portfolio_data[symbol] * candle[trading_enums.PlotAttributes.CLOSE.value]
            for trade in trades_data[pair]:
                if trade[trading_enums.PlotAttributes.X.value] == candle[trading_enums.PlotAttributes.X.value]:
                    if trade[trading_enums.PlotAttributes.SIDE.value] == "sell":
                        moving_portfolio_data[symbol] -= trade[trading_enums.PlotAttributes.VOLUME.value]
                        moving_portfolio_data[ref_market] += trade[trading_enums.PlotAttributes.VOLUME.value] * \
                                                             trade[trading_enums.PlotAttributes.Y.value]
                    else:
                        moving_portfolio_data[symbol] += trade[trading_enums.PlotAttributes.VOLUME.value]
                        moving_portfolio_data[ref_market] -= trade[trading_enums.PlotAttributes.VOLUME.value] * \
                                                             trade[trading_enums.PlotAttributes.Y.value]

    plotted_element.plot(
        kind="scatter",
        x=time_data,
        y=value_data,
        title="Portfolio value")
