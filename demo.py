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
#  Lesser General License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
import asyncio
import logging
from logging.config import fileConfig

from octobot_commons.constants import CONFIG_ENABLED_OPTION, CONFIG_TIME_FRAME
from octobot_commons.enums import TimeFrames

from octobot_trading.channels import TICKER_CHANNEL, RECENT_TRADES_CHANNEL, ORDER_BOOK_CHANNEL, OHLCV_CHANNEL
from octobot_trading.channels.exchange_channel import ExchangeChannels
from octobot_trading.constants import CONFIG_SIMULATOR, CONFIG_TRADER, CONFIG_TRADING
from octobot_trading.exchanges.exchange_manager import ExchangeManager

config = {
    "crypto-currencies": {
        "Bitcoin": {
            "pairs": [
                "BTC/USD",
                "BTC/USDT"
            ]
        },
    },
    "exchanges": {
        "bitmex": {},
        "binance": {}
    },
    CONFIG_TRADER: {
        CONFIG_ENABLED_OPTION: False
    },
    CONFIG_SIMULATOR: {
        CONFIG_ENABLED_OPTION: True,
        "fees": {
            "maker": 0.1,
            "taker": 0.1
        },
        "starting-portfolio": {
            "BTC": 10,
            "ETH": 50,
            "NEO": 100,
            "USDT": 1000
        }
    },
    CONFIG_TRADING: {
        "multi-session-profitability": False,
        "reference-market": "BTC",
        "risk": 0.5
    },
    CONFIG_TIME_FRAME: {
        TimeFrames.ONE_MINUTE,
        TimeFrames.ONE_HOUR
    }
}


async def ticker_callback(symbol, ticker):
    logging.info(f"TICKER : SYMBOL = {symbol} || TICKER = {ticker}")


async def order_book_callback(symbol, asks, bids):
    logging.info(f"ORDERBOOK : SYMBOL = {symbol} || ASKS = {asks} || BIDS = {bids}")


async def ohlcv_callback(symbol, time_frame, candle):
    logging.info(f"OHLCV : SYMBOL = {symbol} || TIME FRAME = {time_frame} || CANDLE = {candle}")


async def recent_trades_callback(symbol, recent_trades):
    logging.info(f"RECENT TRADE : SYMBOL = {symbol} || RECENT TRADE = {recent_trades}")


async def handle_new_exchange(exchange_name):
    exchange = ExchangeManager(config, exchange_name, ignore_config=True)
    await exchange.initialize()

    # consumers
    ExchangeChannels.get_chan(TICKER_CHANNEL, exchange_name).new_consumer(ticker_callback)
    ExchangeChannels.get_chan(RECENT_TRADES_CHANNEL, exchange_name).new_consumer(recent_trades_callback)
    ExchangeChannels.get_chan(ORDER_BOOK_CHANNEL, exchange_name).new_consumer(order_book_callback)
    ExchangeChannels.get_chan(OHLCV_CHANNEL, exchange_name).new_consumer(ohlcv_callback,
                                                                         time_frame=TimeFrames.ONE_MINUTE)


async def main():
    fileConfig("logs/logging_config.ini")
    logging.info("starting...")

    await handle_new_exchange("bitmex")
    await handle_new_exchange("binance")

    await asyncio.sleep(1000)


if __name__ == '__main__':
    asyncio.new_event_loop()
    asyncio.get_event_loop().run_until_complete(main())
