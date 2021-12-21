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
import octobot_backtesting.api as backtesting_api
import octobot_commons.symbol_util as symbol_util
import octobot_commons.constants
import octobot_commons.databases as databases
import octobot_commons.enums as commons_enums
import octobot_commons.errors as commons_errors
import octobot_commons.time_frame_manager as time_frame_manager
import octobot_commons.logging


def get_logger():
    return octobot_commons.logging.get_logger("BacktestingRunData")


async def get_candles(candles_sources, exchange, symbol, time_frame, metadata):
    return await backtesting_api.get_all_ohlcvs(candles_sources[0][trading_enums.DBRows.VALUE.value],
                                                exchange,
                                                symbol,
                                                commons_enums.TimeFrames(time_frame),
                                                inferior_timestamp=metadata[trading_enums.DBRows.START_TIME.value],
                                                superior_timestamp=metadata[trading_enums.DBRows.END_TIME.value])


async def get_trades(meta_database, symbol):
    return await meta_database.get_trades_db().select(trading_enums.DBTables.TRADES.value,
                                                     (await meta_database.get_orders_db().search()).symbol == symbol)


async def get_metadata(meta_database):
    return (await meta_database.get_run_db().all(trading_enums.DBTables.METADATA.value))[0]


async def get_starting_portfolio(meta_database) -> dict:
    return (await meta_database.get_run_db().all(trading_enums.DBTables.PORTFOLIO.value))[0]


async def _load_historical_values(meta_database, exchange, with_candles=True,
                                  with_trades=True, with_portfolio=True, time_frame=None):
    price_data = {}
    trades_data = {}
    moving_portfolio_data = {}
    try:
        starting_portfolio = await get_starting_portfolio(meta_database)
        metadata = await get_metadata(meta_database)
        run_global_metadata = await meta_database.get_backtesting_metadata_from_run()

        exchange = exchange or meta_database.database_manager.context.exchange_name \
                   or metadata[trading_enums.DBRows.EXCHANGES.value][0]    # TODO handle multi exchanges
        ref_market = metadata[trading_enums.DBRows.REFERENCE_MARKET.value]
        # init data
        for pair in run_global_metadata[trading_enums.DBRows.SYMBOLS.value]:
            symbol, _ = symbol_util.split_symbol(pair)
            if symbol != ref_market:
                candles_sources = await meta_database.get_symbol_db(exchange, pair).all(
                    trading_enums.DBTables.CANDLES_SOURCE.value
                )
                if time_frame is None:
                    time_frames = [source[trading_enums.DBRows.TIME_FRAME.value] for source in candles_sources]
                    time_frame = time_frame_manager.find_min_time_frame(time_frames) if time_frames else time_frame
                if with_candles and pair not in price_data:
                    # convert candles timestamp in millis
                    raw_candles = await get_candles(candles_sources, exchange, pair, time_frame, metadata)
                    for candle in raw_candles:
                        candle[commons_enums.PriceIndexes.IND_PRICE_TIME.value] = \
                            candle[commons_enums.PriceIndexes.IND_PRICE_TIME.value] * 1000
                    price_data[pair] = raw_candles
                if with_trades and pair not in trades_data:
                    trades_data[pair] = await get_trades(meta_database, pair)
            if with_portfolio:
                try:
                    moving_portfolio_data[symbol] = starting_portfolio[symbol][octobot_commons.constants.PORTFOLIO_TOTAL]
                except KeyError:
                    moving_portfolio_data[symbol] = 0
                try:
                    moving_portfolio_data[ref_market] = starting_portfolio[ref_market][octobot_commons.constants.PORTFOLIO_TOTAL]
                except KeyError:
                    moving_portfolio_data[ref_market] = 0
    except IndexError:
        pass
    return price_data, trades_data, moving_portfolio_data


async def backtesting_data(meta_database, data_label):
    for reader in meta_database.all_basic_db():
        for table in await reader.tables():
            if table == data_label:
                return await reader.all(table)
            for row in await reader.all(table):
                for key, value in row.items():
                    if key == data_label:
                        return value
    return None


async def plot_historical_portfolio_value(meta_database, plotted_element, exchange=None, own_yaxis=False):
    price_data, trades_data, moving_portfolio_data = await _load_historical_values(meta_database, exchange)
    time_data = []
    value_data = []
    pairs = list(trades_data)
    if pairs:
        pair = pairs[0]
        symbol, ref_market = symbol_util.split_symbol(pair)
        candles = price_data[pair]
        time_data = [candle[commons_enums.PriceIndexes.IND_PRICE_TIME.value] for candle in candles]
        value_data = [0] * len(candles)
        candles = price_data[pair]
        for index, ref_candle in enumerate(candles):
            handled_currencies = []
            for pair in pairs:
                other_candle = price_data[pair][index]
                # part 1: compute portfolio total value
                if other_candle[commons_enums.PriceIndexes.IND_PRICE_TIME.value] == \
                   ref_candle[commons_enums.PriceIndexes.IND_PRICE_TIME.value]:
                    symbol, ref_market = symbol_util.split_symbol(pair)
                    if symbol not in handled_currencies:
                        value_data[index] = \
                            value_data[index] + \
                            moving_portfolio_data[symbol] * other_candle[commons_enums.PriceIndexes.IND_PRICE_OPEN.value]
                        handled_currencies.append(symbol)
                    if ref_market not in handled_currencies:
                        value_data[index] = value_data[index] + moving_portfolio_data[ref_market]
                        handled_currencies.append(ref_market)
                # part 2: compute portfolio total value after trade update when any
                for trade in trades_data[pair]:
                    if trade[trading_enums.PlotAttributes.X.value] == ref_candle[commons_enums.PriceIndexes.IND_PRICE_TIME.value]:
                        if trade[trading_enums.PlotAttributes.SIDE.value] == "sell":
                            moving_portfolio_data[symbol] -= trade[trading_enums.PlotAttributes.VOLUME.value]
                            moving_portfolio_data[ref_market] += trade[trading_enums.PlotAttributes.VOLUME.value] * \
                                trade[trading_enums.PlotAttributes.Y.value]
                        else:
                            moving_portfolio_data[symbol] += trade[trading_enums.PlotAttributes.VOLUME.value]
                            moving_portfolio_data[ref_market] -= trade[trading_enums.PlotAttributes.VOLUME.value] * \
                                trade[trading_enums.PlotAttributes.Y.value]
                        moving_portfolio_data[trade[trading_enums.DBTables.FEES_CURRENCY.value]] -= \
                            trade[trading_enums.DBTables.FEES_AMOUNT.value]

    plotted_element.plot(
        kind="scatter",
        x=time_data,
        y=value_data,
        title="Portfolio value",
        own_yaxis=own_yaxis)


async def _get_historical_pnl(meta_database, plotted_element, cumulative, exchange=None, x_as_trade_count=True, own_yaxis=False):
    # PNL:
    # 1. open position: consider position opening fee from PNL
    # 2. close position: consider closed amount + closing fee into PNL
    # what is a trade ?
    #   futures: when position going to 0 (from long/short) => trade is closed
    #   spot: when position lowered => trade is closed
    price_data, trades_data, _ = await _load_historical_values(meta_database, exchange)
    if not (price_data and next(iter(price_data.values()))):
        return
    x_data = [0 if x_as_trade_count else next(iter(price_data.values()))[0][commons_enums.PriceIndexes.IND_PRICE_TIME.value]]
    pnl_data = [0]
    buy_order_volume_by_price_by_currency = {
        symbol_util.split_symbol(symbol)[0]: {}
        for symbol in trades_data.keys()
    }
    all_trades = []
    for trades in trades_data.values():
        all_trades += trades
    for trade in sorted(all_trades, key=lambda x: x[trading_enums.PlotAttributes.X.value]):
        currency, ref_market = symbol_util.split_symbol(trade[trading_enums.DBTables.SYMBOL.value])
        trade_volume = trade[trading_enums.PlotAttributes.VOLUME.value]
        buy_order_volume_by_price = buy_order_volume_by_price_by_currency[currency]
        if trade[trading_enums.PlotAttributes.SIDE.value] == trading_enums.TradeOrderSide.BUY.value:
            if trade[trading_enums.PlotAttributes.Y.value] in buy_order_volume_by_price:
                buy_order_volume_by_price[trade[trading_enums.PlotAttributes.Y.value]] += trade_volume
            else:
                buy_order_volume_by_price[trade[trading_enums.PlotAttributes.Y.value]] = trade_volume
        elif trade[trading_enums.PlotAttributes.SIDE.value] == trading_enums.TradeOrderSide.SELL.value:
            remaining_sell_volume = trade_volume
            volume_by_bought_prices = {}
            for order_price in sorted(buy_order_volume_by_price.keys()):
                if buy_order_volume_by_price[order_price] > remaining_sell_volume:
                    buy_order_volume_by_price[order_price] -= remaining_sell_volume
                    volume_by_bought_prices[order_price] = remaining_sell_volume
                    remaining_sell_volume = 0
                elif buy_order_volume_by_price[order_price] == remaining_sell_volume:
                    buy_order_volume_by_price.pop(order_price)
                    volume_by_bought_prices[order_price] = remaining_sell_volume
                    remaining_sell_volume = 0
                else:
                    # buy_order_volume_by_price[order_price] < remaining_sell_volume
                    buy_volume = buy_order_volume_by_price.pop(order_price)
                    volume_by_bought_prices[order_price] = buy_volume
                    remaining_sell_volume -= buy_volume
                if remaining_sell_volume <= 0:
                    break
            if volume_by_bought_prices:
                # use total_bought_volume only to avoid taking pre-existing open positions into account
                # (ex if started with already 10 btc)
                total_bought_volume = sum(volume for volume in volume_by_bought_prices.values())
                average_buy_price = sum(price * (volume/total_bought_volume)
                                        for price, volume in volume_by_bought_prices.items())
                fees = trade[trading_enums.DBTables.FEES_AMOUNT.value]
                fees_multiplier = 1 if trade[trading_enums.DBTables.FEES_CURRENCY.value] == ref_market \
                    else trade[trading_enums.PlotAttributes.Y.value]
                pnl = (trade[trading_enums.PlotAttributes.Y.value] - average_buy_price) * total_bought_volume - \
                      fees * fees_multiplier
                if cumulative:
                    pnl += pnl_data[-1]
                pnl_data.append(pnl)
                if x_as_trade_count:
                    x_data.append(len(pnl_data) - 1)
                else:
                    x_data.append(trade[trading_enums.PlotAttributes.X.value])
        else:
            get_logger().error(f"Unknown trade side: {trade}")

    plotted_element.plot(
        kind="scatter",
        x=x_data,
        y=pnl_data,
        x_type="tick0" if x_as_trade_count else "date",
        title="Cumulative P&L" if cumulative else "P&L per trade",
        own_yaxis=own_yaxis)


async def plot_historical_pnl_value(meta_database, plotted_element, exchange=None, x_as_trade_count=True, own_yaxis=False):
    return await _get_historical_pnl(meta_database, plotted_element, False, exchange=exchange,
                                     x_as_trade_count=x_as_trade_count, own_yaxis=own_yaxis)


async def plot_cumulative_historical_pnl_value(meta_database, plotted_element, exchange=None, x_as_trade_count=True, own_yaxis=False):
    return await _get_historical_pnl(meta_database, plotted_element, True, exchange=exchange,
                                     x_as_trade_count=x_as_trade_count, own_yaxis=own_yaxis)


async def plot_trades(meta_database, plotted_element):
    data = await meta_database.get_trades_db().all(trading_enums.DBTables.TRADES.value)
    if not data:
        get_logger().debug(f"Nothing to create a table from when reading {trading_enums.DBTables.TRADES.value}")
        return
    column_render = _get_default_column_render()
    types = _get_default_types()
    key_to_label = {
        **plotted_element.TABLE_KEY_TO_COLUMN,
        **{
            "y": "Price",
            "type": "Type",
            "side": "Side",
        }
    }
    columns = _get_default_columns(plotted_element, data, column_render, key_to_label)
    columns.append({
        "field": "total",
        "label": "Total",
        "render": None
    })
    columns.append({
        "field": "fees",
        "label": "Fees",
        "render": None
    })
    for datum in data:
        datum["total"] = datum["y"] * datum["volume"]
        datum["fees"] = f'{datum["fees_amount"]} {datum["fees_currency"]}'
    rows = _get_default_rows(data, columns)
    searches = _get_default_searches(columns, types)
    plotted_element.table(
        trading_enums.DBTables.TRADES.value,
        columns=columns,
        rows=rows,
        searches=searches)


async def display(plotted_element, label, value):
    plotted_element.value(label, value)


async def display_html(plotted_element, html):
    plotted_element.html_value(html)


async def plot_table(meta_database, plotted_element, data_source, columns=None, rows=None,
                     searches=None, column_render=None, types=None, cache_value=None):
    data = []
    if data_source == trading_enums.DBTables.TRADES.value:
        data = await meta_database.get_trades_db().all(trading_enums.DBTables.TRADES.value)
    elif data_source == trading_enums.DBTables.ORDERS.value:
        data = await meta_database.get_orders_db().all(trading_enums.DBTables.ORDERS.value)
    else:
        exchange = meta_database.database_manager.context.exchange_name
        symbol = meta_database.database_manager.context.symbol
        symbol_db = meta_database.get_symbol_db(exchange, symbol)
        if cache_value is None:
            data = await symbol_db.all(data_source)
        else:
            query = (await symbol_db.search()).title == data_source
            cache_data = await symbol_db.select(trading_enums.DBTables.CACHE_SOURCE.value, query)
            if cache_data:
                try:
                    cache_database = databases.CacheDatabase(cache_data[0][trading_enums.PlotAttributes.VALUE.value])
                    cache = await cache_database.get_cache()
                    data = [
                        {
                            "x": cache_element[commons_enums.CacheDatabaseColumns.TIMESTAMP.value] * 1000,
                            "y": cache_element[cache_value]
                        }
                        for cache_element in cache
                    ]
                except KeyError as e:
                    get_logger().warning(f"Missing cache values when plotting data: {e}")
                except commons_errors.DatabaseNotFoundError as e:
                    get_logger().warning(f"Missing cache values when plotting data: {e}")

    if not data:
        get_logger().debug(f"Nothing to create a table from when reading {data_source}")
        return
    column_render = column_render or _get_default_column_render()
    types = types or _get_default_types()
    columns = columns or _get_default_columns(plotted_element, data, column_render)
    rows = rows or _get_default_rows(data, columns)
    searches = searches or _get_default_searches(columns, types)
    plotted_element.table(
        data_source,
        columns=columns,
        rows=rows,
        searches=searches)


def _get_default_column_render():
    return {
        "Time": "datetime"
    }


def _get_default_types():
    return {
        "Time": "datetime"
    }


def _get_default_columns(plotted_element, data, column_render, key_to_label=None):
    key_to_label = key_to_label or plotted_element.TABLE_KEY_TO_COLUMN
    return [
        {
            "field": row_key,
            "label": key_to_label[row_key],
            "render": column_render.get(key_to_label[row_key], None)
        }
        for row_key, row_value in data[0].items()
        if row_key in key_to_label and row_value is not None
    ]


def _get_default_rows(data, columns):
    column_fields = set(col["field"] for col in columns)
    return [
        {key: val for key, val in row.items() if key in column_fields}
        for row in data
    ]


def _get_default_searches(columns, types):
    return [
        {
            "field": col["field"],
            "label": col["label"],
            "type": types.get(col["label"])
        }
        for col in columns
    ]
