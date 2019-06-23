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
import os
from logging.config import fileConfig

from octobot_commons.constants import CONFIG_ENABLED_OPTION, CONFIG_TIME_FRAME
from octobot_commons.enums import TimeFrames

from octobot_trading.channels import TICKER_CHANNEL, RECENT_TRADES_CHANNEL, ORDER_BOOK_CHANNEL, OHLCV_CHANNEL, \
    KLINE_CHANNEL, BALANCE_CHANNEL, TRADES_CHANNEL, POSITIONS_CHANNEL, ORDERS_CHANNEL
from octobot_trading.channels.exchange_channel import ExchangeChannels
from octobot_trading.constants import CONFIG_SIMULATOR, CONFIG_TRADER, CONFIG_TRADING
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.traders.trader import Trader

config = {
    "crypto-currencies": {
        "Bitcoin": {
            "pairs": [
                "BTC/USD",
                "BTC/USDT"
            ]
        },
        "Litecoin": {
            "pairs": [
                "LTCM19"
            ]
        }
    },
    "exchanges": {
        "bitmex": {
            "api-key": os.getenv('BITMEX-API-KEY'),
            "api-secret": os.getenv('BITMEX-API-SECRET')
        },
        "binance": {
            "api-key": os.getenv('BINANCE-API-KEY'),
            "api-secret": os.getenv('BINANCE-API-SECRET')
        },
        "coinbasepro": {
            "api-key": os.getenv('COINBASE-API-KEY'),
            "api-secret": os.getenv('COINBASE-API-SECRET'),
            "api-password": os.getenv('COINBASE-PASSWORD')
        }
    },
    CONFIG_TRADER: {
        CONFIG_ENABLED_OPTION: True
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


async def ticker_callback(exchange, symbol, ticker):
    logging.info(f"TICKER : EXCHANGE = {exchange} || SYMBOL = {symbol} || TICKER = {ticker}")


async def order_book_callback(exchange, symbol, asks, bids):
    logging.info(f"ORDERBOOK : EXCHANGE = {exchange} || SYMBOL = {symbol} || ASKS = {asks} || BIDS = {bids}")


async def ohlcv_callback(exchange, symbol, time_frame, candle):
    logging.info(f"OHLCV : EXCHANGE = {exchange} || SYMBOL = {symbol} || TIME FRAME = {time_frame} || CANDLE = {candle}")


async def recent_trades_callback(exchange, symbol, recent_trades):
    logging.info(f"RECENT TRADE : EXCHANGE = {exchange} || SYMBOL = {symbol} || RECENT TRADE = {recent_trades}")


async def kline_callback(exchange, symbol, time_frame, kline):
    logging.info(f"KLINE : EXCHANGE = {exchange} || SYMBOL = {symbol} || TIME FRAME = {time_frame} || KLINE = {kline}")


async def balance_callback(exchange, balance):
    logging.info(f"BALANCE : EXCHANGE = {exchange} || BALANCE = {balance}")


async def trades_callback(exchange, symbol, trade):
    logging.info(f"TRADES : EXCHANGE = {exchange} || SYMBOL = {symbol} || TRADE = {trade}")


async def orders_callback(exchange, symbol, order, is_closed, is_updated, is_from_bot):
    logging.info(f"ORDERS : EXCHANGE = {exchange} || SYMBOL = {symbol} || ORDER = {order} "
                 f"|| CLOSED = {is_closed} || UPDATED = {is_updated} || FROM_BOT = {is_from_bot}")


async def positions_callback(exchange, symbol, position, is_closed, is_updated, is_from_bot):
    logging.info(f"POSITIONS : EXCHANGE = {exchange} || SYMBOL = {symbol} || POSITIONS = {position}"
                 f"|| CLOSED = {is_closed} || UPDATED = {is_updated} || FROM_BOT = {is_from_bot}")


async def handle_new_exchange(exchange_name, sandboxed=False):
    exchange = ExchangeManager(config, exchange_name, rest_only=True)  # TODO rest_only=False
    await exchange.initialize()

    # print(dir(ccxt.bitmex()))

    trader = Trader(config, exchange)
    await trader.initialize()

    # set sandbox mode
    exchange.exchange.client.setSandboxMode(sandboxed)

    # consumers
    ExchangeChannels.get_chan(TICKER_CHANNEL, exchange_name).new_consumer(ticker_callback)
    ExchangeChannels.get_chan(RECENT_TRADES_CHANNEL, exchange_name).new_consumer(recent_trades_callback)
    ExchangeChannels.get_chan(ORDER_BOOK_CHANNEL, exchange_name).new_consumer(order_book_callback)
    ExchangeChannels.get_chan(KLINE_CHANNEL, exchange_name).new_consumer(kline_callback)
    ExchangeChannels.get_chan(OHLCV_CHANNEL, exchange_name).new_consumer(ohlcv_callback)

    ExchangeChannels.get_chan(BALANCE_CHANNEL, exchange_name).new_consumer(balance_callback)
    ExchangeChannels.get_chan(TRADES_CHANNEL, exchange_name).new_consumer(trades_callback)
    ExchangeChannels.get_chan(POSITIONS_CHANNEL, exchange_name).new_consumer(positions_callback)
    ExchangeChannels.get_chan(ORDERS_CHANNEL, exchange_name).new_consumer(orders_callback)


async def main():
    fileConfig("logs/logging_config.ini")
    logging.info("starting...")

    await handle_new_exchange("bitmex", sandboxed=True)
    # await handle_new_exchange("binance")
    # await handle_new_exchange("coinbasepro")

    await asyncio.sleep(10000)


if __name__ == '__main__':
    asyncio.new_event_loop()
    asyncio.get_event_loop().run_until_complete(main())
