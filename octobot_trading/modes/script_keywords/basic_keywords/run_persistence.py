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
import octobot_commons.constants as commons_constants
import octobot_commons.databases as commons_databases
import octobot_trading.enums as trading_enums
import octobot_backtesting.api as backtesting_api
import octobot_trading.personal_data as personal_data


def set_plot_orders(ctx, value):
    ctx.plot_orders = value


async def store_candles(exchange_manager, symbol, time_frame, chart=commons_enums.PlotCharts.MAIN_CHART.value,
                        symbol_db=None):
    symbol_db = symbol_db or commons_databases.RunDatabasesProvider.instance().get_symbol_db(
        exchange_manager.bot_id,
        exchange_manager.exchange_name,
        symbol
    )
    candles_data = {
        "time_frame": time_frame,
        "value": backtesting_api.get_data_file_from_importers(
            exchange_manager.exchange.connector.exchange_importers, symbol,
            commons_enums.TimeFrames(time_frame)
        )
        if exchange_manager.is_backtesting else commons_constants.LOCAL_BOT_DATA,
        "chart": chart
    }
    if (not await symbol_db.contains_row(
                commons_enums.DBTables.CANDLES_SOURCE.value,
                {
                    "time_frame": time_frame,
                    "value": candles_data["value"],
                })):
        await symbol_db.log(commons_enums.DBTables.CANDLES_SOURCE.value, candles_data)


async def store_orders(ctx, orders,
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


def _format_trade(trade_dict, exchange_manager, chart, x_multiplier, kind, mode):
    tag = f"{trade_dict[trading_enums.ExchangeConstantsOrderColumns.TAG.value]} " \
        if trade_dict[trading_enums.ExchangeConstantsOrderColumns.TAG.value] else ""
    symbol = trade_dict[trading_enums.ExchangeConstantsOrderColumns.SYMBOL.value]
    trade_side = trade_dict[trading_enums.ExchangeConstantsOrderColumns.SIDE.value]
    is_using_positions = False
    color = shape = None
    if exchange_manager.is_future:
        positions = exchange_manager.exchange_personal_data.positions_manager.get_symbol_positions(symbol=symbol)
        if positions:
            is_using_positions = True
            # trading_side = next(iter(positions)).side
            # if trading_side is trading_enums.PositionSide.LONG:
            if "stop_loss" in trade_dict[trading_enums.ExchangeConstantsOrderColumns.TYPE.value]:
                shape = "x"
                color = "orange"
            elif trade_dict[trading_enums.ExchangeConstantsOrderColumns.REDUCE_ONLY.value] is True:
                if trade_side == trading_enums.TradeOrderSide.SELL.value:
                    # long tp
                    color = "magenta"
                    shape = "arrow-bar-left"
                else:
                    # short tp
                    color = "blue"
                    shape = "arrow-bar-left"
            else:
                if trade_side == trading_enums.TradeOrderSide.BUY.value:
                    # long entry
                    color = "green"
                    shape = "arrow-bar-right"
                else:
                    # short entry
                    color = "red"
                    shape = "arrow-bar-right"

    if not is_using_positions:
        if trade_side == trading_enums.TradeOrderSide.BUY.value:
            color = "blue"
            shape = "arrow-bar-right"
        elif "stop_loss" in trade_dict[trading_enums.ExchangeConstantsOrderColumns.TYPE.value]:
            color = "orange"
            shape = "x"
        else:
            color = "magenta"
            shape = "arrow-bar-left"

    return {
        "x": trade_dict[trading_enums.ExchangeConstantsOrderColumns.TIMESTAMP.value] * x_multiplier,
        "text": f"{tag}{trade_dict[trading_enums.ExchangeConstantsOrderColumns.TYPE.value]} "
                f"{trade_dict[trading_enums.ExchangeConstantsOrderColumns.SIDE.value]} "
                f"{trade_dict[trading_enums.ExchangeConstantsOrderColumns.AMOUNT.value]} "
                f"{trade_dict[trading_enums.ExchangeConstantsOrderColumns.QUANTITY_CURRENCY.value]} "
                f"at {trade_dict[trading_enums.ExchangeConstantsOrderColumns.PRICE.value]}",
        "id": trade_dict[trading_enums.ExchangeConstantsOrderColumns.ID.value],
        "symbol": trade_dict[trading_enums.ExchangeConstantsOrderColumns.SYMBOL.value],
        "type": trade_dict[trading_enums.ExchangeConstantsOrderColumns.TYPE.value],
        "volume": float(trade_dict[trading_enums.ExchangeConstantsOrderColumns.AMOUNT.value]),
        "y": float(trade_dict[trading_enums.ExchangeConstantsOrderColumns.PRICE.value]),
        "cost": float(trade_dict[trading_enums.ExchangeConstantsOrderColumns.COST.value]),
        "state": trade_dict[trading_enums.ExchangeConstantsOrderColumns.STATUS.value],
        "chart": chart,
        "kind": kind,
        "side": trade_dict[trading_enums.ExchangeConstantsOrderColumns.SIDE.value],
        "mode": mode,
        "shape": shape,
        "color": color,
        "size": "10",
        "fees_amount": float(trade_dict[trading_enums.ExchangeConstantsOrderColumns.FEE.value]
                             [trading_enums.ExchangeConstantsFeesColumns.COST.value] if
                             trade_dict[trading_enums.ExchangeConstantsOrderColumns.FEE.value] else 0),
        "fees_currency": trade_dict[trading_enums.ExchangeConstantsOrderColumns.FEE.value][
            trading_enums.ExchangeConstantsFeesColumns.CURRENCY.value]
        if trade_dict[trading_enums.ExchangeConstantsOrderColumns.FEE.value] else "",
    }


async def store_trades(
        exchange_manager,
        trades,
        chart=commons_enums.PlotCharts.MAIN_CHART.value,
        x_multiplier=1000,
        kind="scattergl",
        mode="markers",
):
    trades_db = commons_databases.RunDatabasesProvider.instance().get_trades_db(
        exchange_manager.bot_id,
        exchange_manager.exchange_name
    )
    trades_data = [
        _format_trade(
            trade.to_dict(),
            exchange_manager,
            chart,
            x_multiplier,
            kind,
            mode
        )
        for trade in trades
    ]
    await trades_db.log_many(commons_enums.DBTables.TRADES.value, trades_data)


async def store_trade(ctx,
                      trade_dict,
                      chart=commons_enums.PlotCharts.MAIN_CHART.value,
                      x_multiplier=1000,
                      kind="scattergl",
                      mode="markers",
                      exchange_manager=None,
                      writer=None):
    await writer.log(
        commons_enums.DBTables.TRADES.value,
        _format_trade(
            trade_dict,
            exchange_manager or ctx.exchange_manager,
            chart,
            x_multiplier,
            kind,
            mode
        )
    )


def _format_transaction(transaction, chart, x_multiplier, kind, mode, y_data):
    return {
        "x": transaction.creation_time * x_multiplier,
        "type": transaction.transaction_type.value,
        "id": transaction.transaction_id,
        "symbol": transaction.symbol,
        "currency": transaction.currency,
        "quantity": float(transaction.quantity) if hasattr(transaction, "quantity") else None,
        "order_id": transaction.order_id if hasattr(transaction, "order_id") else None,
        "funding_rate": float(transaction.funding_rate) if hasattr(transaction, "funding_rate") else None,
        "realised_pnl": float(transaction.realised_pnl) if hasattr(transaction, "realised_pnl") else None,
        "transaction_fee": float(transaction.transaction_fee) if hasattr(transaction, "transaction_fee") else None,
        "closed_quantity": float(transaction.closed_quantity) if hasattr(transaction, "closed_quantity") else None,
        "cumulated_closed_quantity": float(transaction.cumulated_closed_quantity)
        if hasattr(transaction, "cumulated_closed_quantity") else None,
        "first_entry_time": float(transaction.first_entry_time) * x_multiplier
        if hasattr(transaction, "first_entry_time") else None,
        "average_entry_price": float(transaction.average_entry_price)
        if hasattr(transaction, "average_entry_price") else None,
        "average_exit_price": float(transaction.average_exit_price)
        if hasattr(transaction, "average_exit_price") else None,
        "order_exit_price": float(transaction.order_exit_price)
        if hasattr(transaction, "order_exit_price") else None,
        "leverage": float(transaction.leverage) if hasattr(transaction, "leverage") else None,
        "trigger_source": transaction.trigger_source.value if hasattr(transaction, "trigger_source") else None,
        "side": transaction.side.value if hasattr(transaction, "side") else None,
        "y": y_data,
        "chart": chart,
        "kind": kind,
        "mode": mode
    }


async def store_transaction(transaction,
                            chart=commons_enums.PlotCharts.MAIN_CHART.value,
                            x_multiplier=1000,
                            kind="scattergl",
                            mode="markers",
                            y_data=None,
                            writer=None):
    y_data = y_data or 0
    await writer.log(
        commons_enums.DBTables.TRANSACTIONS.value,
        _format_transaction(
            transaction,
            chart,
            x_multiplier,
            kind,
            mode,
            y_data
        )
    )


async def store_transactions(exchange_manager,
                             transactions,
                             chart=commons_enums.PlotCharts.MAIN_CHART.value,
                             x_multiplier=1000,
                             kind="scattergl",
                             mode="markers",
                             y_data=None):
    transactions_db = commons_databases.RunDatabasesProvider.instance().get_transactions_db(
        exchange_manager.bot_id,
        exchange_manager.exchange_name
    )
    y_data = y_data or [0] * len(transactions)
    transactions_data = [
        _format_transaction(transaction, chart, x_multiplier, kind, mode, y_data[index])
        for index, transaction in enumerate(transactions)
    ]
    await transactions_db.log_many(commons_enums.DBTables.TRANSACTIONS.value, transactions_data)


async def save_metadata(writer, metadata):
    await writer.log(
        commons_enums.DBTables.METADATA.value,
        metadata
    )


async def store_portfolio(exchange_manager):
    run_db = commons_databases.RunDatabasesProvider.instance().get_run_db(exchange_manager.bot_id)
    await run_db.log(
        commons_enums.DBTables.PORTFOLIO.value,
        personal_data.portfolio_to_float(
            exchange_manager.exchange_personal_data.portfolio_manager.portfolio.portfolio
        )
    )


async def clear_run_data(exchange_manager):
    run_db = commons_databases.RunDatabasesProvider.instance().get_run_db(exchange_manager.bot_id)
    await _clear_table(run_db, commons_enums.DBTables.METADATA.value, flush=False)
    await _clear_table(run_db, commons_enums.DBTables.PORTFOLIO.value, flush=False)
    await run_db.clear()
    for symbol in exchange_manager.exchange_config.traded_symbol_pairs:
        await _clear_table(
            commons_databases.RunDatabasesProvider.instance().get_symbol_db(
                exchange_manager.bot_id,
                exchange_manager.exchange_name,
                symbol
            ),
            commons_enums.DBTables.CANDLES.value,
            flush=False
        )


async def clear_orders_cache(writer):
    await _clear_table(writer, commons_enums.DBTables.ORDERS.value)
    await writer.clear()


async def clear_trades_cache(writer):
    await _clear_table(writer, commons_enums.DBTables.TRADES.value)
    await writer.clear()


async def clear_transactions_cache(writer):
    await _clear_table(writer, commons_enums.DBTables.TRANSACTIONS.value)
    await writer.clear()


async def clear_all_tables(writer_reader):
    for table in await writer_reader.tables():
        await _clear_table(writer_reader, table)
    await writer_reader.clear()


async def _clear_table(writer, table, flush=True):
    await writer.delete(table, None)
    if flush:
        await writer.flush()


def get_shared_element(key):
    return commons_databases.GlobalSharedMemoryStorage.instance()[key]


def set_shared_element(key, element):
    commons_databases.GlobalSharedMemoryStorage.instance()[key] = element
