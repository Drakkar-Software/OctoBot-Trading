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

from octobot_channels.channels.channel import get_chan

from octobot_commons.channels_name import OctoBotBacktestingChannelsName
from octobot_commons.pretty_printer import PrettyPrinter

from octobot_trading.constants import TICKER_CHANNEL, RECENT_TRADES_CHANNEL, ORDER_BOOK_CHANNEL, KLINE_CHANNEL, \
    OHLCV_CHANNEL, BALANCE_CHANNEL, TRADES_CHANNEL, POSITIONS_CHANNEL, ORDERS_CHANNEL, BALANCE_PROFITABILITY_CHANNEL
from octobot_trading.channels.exchange_channel import get_chan as get_trading_chan
from octobot_trading.cli import get_should_display_callbacks_logs


async def ticker_callback(exchange: str, exchange_id: str, symbol: str,  ticker):
    if get_should_display_callbacks_logs():
        logging.info(f"TICKER : EXCHANGE = {exchange} || SYMBOL = {symbol} || TICKER = {ticker}")


async def order_book_callback(exchange: str, exchange_id: str, symbol: str,  asks, bids):
    if get_should_display_callbacks_logs():
        logging.info(f"ORDERBOOK : EXCHANGE = {exchange} || SYMBOL = {symbol} || ASKS = {asks} || BIDS = {bids}")


async def ohlcv_callback(exchange: str, exchange_id: str, symbol: str,  time_frame, candle):
    if get_should_display_callbacks_logs():
        logging.info(
            f"OHLCV : EXCHANGE = {exchange} || SYMBOL = {symbol} || TIME FRAME = {time_frame} || CANDLE = {candle}")


async def recent_trades_callback(exchange: str, exchange_id: str, symbol: str,  recent_trades):
    if get_should_display_callbacks_logs():
        logging.info(f"RECENT TRADE : EXCHANGE = {exchange} || SYMBOL = {symbol} || RECENT TRADE = {recent_trades}")


async def kline_callback(exchange: str, exchange_id: str, symbol: str, time_frame, kline):
    if get_should_display_callbacks_logs():
        logging.info(
            f"KLINE : EXCHANGE = {exchange} || SYMBOL = {symbol} || TIME FRAME = {time_frame} || KLINE = {kline}")


async def balance_callback(exchange: str, exchange_id: str, balance):
    if get_should_display_callbacks_logs():
        logging.info(f"BALANCE : EXCHANGE = {exchange} || BALANCE = {balance}")


async def balance_profitability_callback(exchange: str, exchange_id: str, profitability, profitability_percent,
                                         market_profitability_percent, initial_portfolio_current_profitability):
    if get_should_display_callbacks_logs():
        logging.info(f"BALANCE PROFITABILITY : EXCHANGE = {exchange} || PROFITABILITY = "
                     f"{PrettyPrinter.portfolio_profitability_pretty_print(profitability, profitability_percent, 'USDT')}")


async def trades_callback(exchange: str, exchange_id: str, symbol: str, trade: dict, old_trade: bool):
    if get_should_display_callbacks_logs():
        logging.info(f"TRADES : EXCHANGE = {exchange} || SYMBOL = {symbol} || TRADE = {trade} "
                     f"|| OLD_TRADE = {old_trade}")


async def orders_callback(exchange: str, exchange_id: str, symbol: str,  order: dict, is_new, is_from_bot):
    if get_should_display_callbacks_logs():
        order_string = f"ORDERS : EXCHANGE = {exchange} || SYMBOL = {symbol} ||"
        order_string += PrettyPrinter.open_order_pretty_printer(exchange, order)
        order_string += f"|| CREATED = {is_new} || FROM_BOT = {is_from_bot}"
        logging.info(order_string)


async def positions_callback(exchange: str, exchange_id: str, symbol: str,  position, is_closed, is_updated, is_from_bot):
    if get_should_display_callbacks_logs():
        logging.info(f"POSITIONS : EXCHANGE = {exchange} || SYMBOL = {symbol} || POSITIONS = {position}"
                     f"|| CLOSED = {is_closed} || UPDATED = {is_updated} || FROM_BOT = {is_from_bot}")


async def time_callback(timestamp):
    if get_should_display_callbacks_logs():
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
    await get_trading_chan(TICKER_CHANNEL, exchange_id).new_consumer(ticker_callback)
    await get_trading_chan(RECENT_TRADES_CHANNEL, exchange_id).new_consumer(
        recent_trades_callback)
    await get_trading_chan(ORDER_BOOK_CHANNEL, exchange_id).new_consumer(order_book_callback)
    await get_trading_chan(KLINE_CHANNEL, exchange_id).new_consumer(kline_callback)
    await get_trading_chan(OHLCV_CHANNEL, exchange_id).new_consumer(ohlcv_callback)

    await get_trading_chan(BALANCE_CHANNEL, exchange_id).new_consumer(balance_callback)
    await get_trading_chan(BALANCE_PROFITABILITY_CHANNEL, exchange_id).new_consumer(
        balance_profitability_callback)
    await get_trading_chan(TRADES_CHANNEL, exchange_id).new_consumer(trades_callback)
    await get_trading_chan(POSITIONS_CHANNEL, exchange_id).new_consumer(positions_callback)
    await get_trading_chan(ORDERS_CHANNEL, exchange_id).new_consumer(orders_callback)

    try:
        await get_chan(OctoBotBacktestingChannelsName.TIME_CHANNEL.value).new_consumer(time_callback)
    except KeyError:
        pass


async def wait_exchange_tasks():
    await asyncio.gather(*asyncio.all_tasks(asyncio.get_event_loop()))
