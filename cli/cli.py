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

import click
from click_shell import shell
from octobot_commons.constants import CONFIG_TIME_FRAME, CONFIG_ENABLED_OPTION
from octobot_commons.enums import TimeFrames

from octobot_trading.constants import CONFIG_TRADING, CONFIG_TRADER, CONFIG_SIMULATOR
from octobot_trading.exchanges.exchange_manager import ExchangeManager

exchanges = {}
config = {
    "crypto-currencies": {
        "Bitcoin": {
            "pairs": [
                "BTC/USDT"
            ]
        },
    },
    "exchanges": {
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
        TimeFrames.ONE_HOUR
    }
}


@shell(prompt='OctoBot-Trading > ', intro='Starting...')
def app():
    pass


@app.command()
@click.option("--exchange_name", prompt="Exchange name", help="The name of the exchange to use.")
# @click.option("--api_key", prompt="API key", help="The api key of the exchange to use.")
# @click.option("--api_secret", prompt="API secret", help="The api secret of the exchange to use.")
def connect(exchange_name):
    if exchange_name not in exchanges:
        exchanges[exchange_name] = ExchangeManager(config, exchange_name)
    else:
        click.echo("Already connected to this exchange", err=True)
        return
    asyncio.get_event_loop().run_until_complete(exchanges[exchange_name].initialize())
    click.echo(f"Connected to {exchange_name}")


if __name__ == '__main__':
    print("** Welcome to OctoBot-Trading command line interface **")
    asyncio.new_event_loop()
    app()
