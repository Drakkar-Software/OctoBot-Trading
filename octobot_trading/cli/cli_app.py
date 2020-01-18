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
from threading import Thread

import click
from click_shell import shell

from octobot_trading.api.exchange import create_exchange_builder
from octobot_trading.api.orders import get_open_orders, create_order as api_create_order
from octobot_trading.cli import exchanges, get_config, set_should_display_callbacks_logs, add_exchange, get_exchange
from octobot_trading.cli.cli_tools import start_cli_exchange
from octobot_trading.enums import TraderOrderType


@shell(prompt='OctoBot-Trading > ', intro='Starting...')
def app():
    exchange_name = "binance"
    exchange_builder = create_exchange_builder(get_config(), exchange_name) \
        .is_simulated() \
        .is_rest_only()

    add_exchange(exchange_name, {
        "exchange_builder": exchange_builder,
        "exchange_thread": Thread(target=start_cli_exchange, args=(exchange_builder,))
    })

    get_exchange(exchange_name)["exchange_thread"].start()


@app.command()
def show():
    set_should_display_callbacks_logs(True)


@app.command()
def hide():
    set_should_display_callbacks_logs(False)


#  create_order --exchange_name binance --symbol BTC/USDT --price 11000 --quantity 1 --order_type buy_limit
@app.command()
@click.option("--exchange_name", prompt="Exchange name", help="The name of the exchange to use.", type=str)
@click.option("--symbol", prompt="Order symbol", help="The order symbol.", type=str)
@click.option("--price", prompt="Order price", help="The order price.", type=float)
@click.option("--quantity", prompt="Order quantity", help="The order quantity.", type=float)
@click.option("--order_type", prompt="Order type", help="The order type.",
              type=click.Choice([t.value for t in TraderOrderType]))
def create_order(exchange_name, symbol, price, quantity, order_type):
    asyncio.get_event_loop().run_until_complete(
        api_create_order(exchanges[exchange_name]["exchange_factory"].exchange_manager,
                         order_type=TraderOrderType(order_type),
                         symbol=symbol,
                         current_price=price,
                         quantity=quantity,
                         price=price))


#  orders --exchange_name binance --symbol BTC/USDT
@app.command()
@click.option("--exchange_name", prompt="Exchange name", help="The name of the exchange to use.", type=str)
@click.option("--symbol", prompt="Order symbol", help="The order symbol.", type=str)
def orders(exchange_name, symbol):
    exchange_manager = exchanges[exchange_name]["exchange_factory"].exchange_manager
    click.echo(get_open_orders(exchange_manager))


@app.command()
@click.option("--exchange_name", prompt="Exchange name", help="The name of the exchange to use.")
# @click.option("--api_key", prompt="API key", help="The api key of the exchange to use.")
# @click.option("--api_secret", prompt="API secret", help="The api secret of the exchange to use.")
def connect(exchange_name):
    if exchange_name not in exchanges:
        exchange_builder = create_exchange_builder(get_config(), exchange_name)

        exchanges[exchange_name] = {
            "exchange_builder": exchange_builder,
            "exchange_thread": Thread(target=start_cli_exchange, args=(exchange_builder,))
        }

        exchanges[exchange_name]["exchange_thread"].start()
    else:
        click.echo("Already connected to this exchange", err=True)
        return
    click.echo(f"Connected to {exchange_name}")
