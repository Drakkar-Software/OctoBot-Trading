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
import asyncio
import logging

import async_channel.channels as channel

import octobot_commons.channels_name as channels_name
import octobot_commons.pretty_printer as pretty_printer

import octobot_trading.exchange_channel as exchanges_channel
import octobot_trading.cli as cli


async def ticker_callback(exchange: str, exchange_id: str, cryptocurrency: str, symbol: str,  ticker):
    if cli.get_should_display_callbacks_logs():
        logging.info(f"TICKER : EXCHANGE = {exchange} || SYMBOL = {symbol} || TICKER = {ticker}")


async def order_book_callback(exchange: str, exchange_id: str, cryptocurrency: str, symbol: str,  asks, bids):
    if cli.get_should_display_callbacks_logs():
        logging.info(f"ORDERBOOK : EXCHANGE = {exchange} || SYMBOL = {symbol} || ASKS = {asks} || BIDS = {bids}")


async def ohlcv_callback(exchange: str, exchange_id: str, cryptocurrency: str, symbol: str,  time_frame, candle):
    if cli.get_should_display_callbacks_logs():
        logging.info(
            f"OHLCV : EXCHANGE = {exchange} || CRYPTOCURRENCY = {cryptocurrency} || SYMBOL = {symbol} "
            f"|| TIME FRAME = {time_frame} || CANDLE = {candle}")


async def recent_trades_callback(exchange: str, exchange_id: str, cryptocurrency: str, symbol: str,  recent_trades):
    if cli.get_should_display_callbacks_logs():
        logging.info(f"RECENT TRADE : EXCHANGE = {exchange} || SYMBOL = {symbol} || RECENT TRADE = {recent_trades}")


async def kline_callback(exchange: str, exchange_id: str, cryptocurrency: str, symbol: str, time_frame, kline):
    if cli.get_should_display_callbacks_logs():
        logging.info(
            f"KLINE : EXCHANGE = {exchange} || SYMBOL = {symbol} || TIME FRAME = {time_frame} || KLINE = {kline}")


async def balance_callback(exchange: str, exchange_id: str, balance):
    if cli.get_should_display_callbacks_logs():
        logging.info(f"BALANCE : EXCHANGE = {exchange} || BALANCE = {balance}")


async def balance_profitability_callback(exchange: str, exchange_id: str, profitability, profitability_percent,
                                         market_profitability_percent, initial_portfolio_current_profitability):
    if cli.get_should_display_callbacks_logs():
        logging.info(f"BALANCE PROFITABILITY : EXCHANGE = {exchange} || PROFITABILITY = "
                     f"{pretty_printer.portfolio_profitability_pretty_print(profitability, profitability_percent, 'USDT')}")


async def trades_callback(exchange: str, exchange_id: str, cryptocurrency: str, symbol: str, trade: dict, old_trade: bool):
    if cli.get_should_display_callbacks_logs():
        logging.info(f"TRADES : EXCHANGE = {exchange} || SYMBOL = {symbol} || TRADE = {trade} "
                     f"|| OLD_TRADE = {old_trade}")


async def orders_callback(exchange: str, exchange_id: str, cryptocurrency: str, symbol: str,  order: dict, is_new: bool, is_from_bot: bool):
    if cli.get_should_display_callbacks_logs():
        order_string = f"ORDERS : EXCHANGE = {exchange} || SYMBOL = {symbol} ||"
        order_string += pretty_printer.open_order_pretty_printer(exchange, order)
        order_string += f"|| CREATED = {is_new} || FROM_BOT = {is_from_bot}"
        logging.info(order_string)


async def positions_callback(exchange: str, exchange_id: str, cryptocurrency: str, symbol: str,  position, is_closed, is_updated, is_liquidated: bool, is_from_bot):
    if cli.get_should_display_callbacks_logs():
        logging.info(f"POSITIONS : EXCHANGE = {exchange} || SYMBOL = {symbol} || POSITIONS = {position}"
                     f"|| CLOSED = {is_closed} || UPDATED = {is_updated} || FROM_BOT = {is_from_bot}")


async def time_callback(timestamp):
    if cli.get_should_display_callbacks_logs():
        logging.info(f"TIME : TIMESTAMP = {timestamp}")


def start_cli_exchange(exchange_builder):
    current_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(current_loop)
    current_loop.run_until_complete(start_exchange(exchange_builder))

    try:
        current_loop.run_until_complete(wait_exchange_tasks())
    except asyncio.CancelledError:
        logging.error(f"An error occurred when cancelling task")


async def start_exchange(exchange_builder):
    exchange_manager = await exchange_builder.build()

    # consumers
    exchange_id = exchange_manager.id
    await exchanges_channel.get_chan(channels_name.OctoBotTradingChannelsName.TICKER_CHANNEL.value, exchange_id)\
        .new_consumer(ticker_callback)
    await exchanges_channel.get_chan(channels_name.OctoBotTradingChannelsName.RECENT_TRADES_CHANNEL.value, exchange_id)\
        .new_consumer(
        recent_trades_callback)
    await exchanges_channel.get_chan(channels_name.OctoBotTradingChannelsName.ORDER_BOOK_CHANNEL.value, exchange_id)\
        .new_consumer(order_book_callback)
    await exchanges_channel.get_chan(channels_name.OctoBotTradingChannelsName.KLINE_CHANNEL.value, exchange_id)\
        .new_consumer(kline_callback)
    await exchanges_channel.get_chan(channels_name.OctoBotTradingChannelsName.OHLCV_CHANNEL.value, exchange_id)\
        .new_consumer(ohlcv_callback)

    await exchanges_channel.get_chan(channels_name.OctoBotTradingChannelsName.BALANCE_CHANNEL.value, exchange_id)\
        .new_consumer(balance_callback)
    await exchanges_channel.get_chan(channels_name.OctoBotTradingChannelsName.BALANCE_PROFITABILITY_CHANNEL.value,
                                     exchange_id).new_consumer(
        balance_profitability_callback)
    await exchanges_channel.get_chan(channels_name.OctoBotTradingChannelsName.TRADES_CHANNEL.value, exchange_id)\
        .new_consumer(trades_callback)
    await exchanges_channel.get_chan(channels_name.OctoBotTradingChannelsName.POSITIONS_CHANNEL.value, exchange_id)\
        .new_consumer(positions_callback)
    await exchanges_channel.get_chan(channels_name.OctoBotTradingChannelsName.ORDERS_CHANNEL.value, exchange_id)\
        .new_consumer(orders_callback)

    try:
        await channel.get_chan(channels_name.OctoBotBacktestingChannelsName.TIME_CHANNEL.value)\
            .new_consumer(time_callback)
    except KeyError:
        pass


async def wait_exchange_tasks():
    await asyncio.gather(*asyncio.all_tasks(asyncio.get_event_loop()))
