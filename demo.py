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
import logging
import os
from logging.config import fileConfig

from octobot_commons.constants import CONFIG_ENABLED_OPTION, CONFIG_TIME_FRAME, CONFIG_CRYPTO_CURRENCIES
from octobot_commons.enums import TimeFrames
from octobot_trading import cli
from octobot_trading.api.exchange import create_new_exchange
from octobot_trading.cli import add_exchange
from octobot_trading.cli.cli_tools import start_cli_exchange
from octobot_trading.constants import CONFIG_SIMULATOR, CONFIG_TRADER, CONFIG_TRADING, CONFIG_EXCHANGES


config = {
    CONFIG_CRYPTO_CURRENCIES: {
        "Bitcoin": {
            "pairs": [
                "BTC/USDT",
                "BTC/USD"
            ]
        },
        "Ethereum": {
            "pairs": [
                "ETH/USDT",
                "ETH/USD"
            ]
        }
    },
    CONFIG_EXCHANGES: {
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

if __name__ == '__main__':
    fileConfig("logs/logging_config.ini")
    logging.info("starting...")

    print("** Welcome to OctoBot-Trading command line interface **")
    cli.set_config(config)
    cli.set_should_display_callbacks_logs(True)

    exchange_name = "binance"
    exchange_factory = create_new_exchange(config, exchange_name,
                                           is_simulated=True, is_rest_only=True, is_backtesting=False,
                                           backtesting_files=[os.getenv('BACKTESTING_FILE')])

    add_exchange(exchange_name, {
        "exchange_factory": exchange_factory,
        "exchange_thread": None
    })

    start_cli_exchange(exchange_factory)
