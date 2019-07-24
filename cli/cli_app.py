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

from cli import exchanges, get_config, set_should_display_callbacks_logs, get_exchanges, add_exchange, get_exchange
from cli.cli_tools import create_new_exchange, start_cli_exchange
from octobot_trading.enums import TraderOrderType


@shell(prompt='OctoBot-Trading > ', intro='Starting...')
def app():
    exchange_name = "binance"
    exchange_factory = create_new_exchange(get_config(), exchange_name,
                                           is_simulated=True,
                                           is_rest_only=True,
                                           is_backtesting=False,
                                           is_sandboxed=False)

    add_exchange(exchange_name, {
        "exchange_factory": exchange_factory,
        "exchange_thread": Thread(target=start_cli_exchange, args=(exchange_factory,))
    })

    get_exchange(exchange_name)["exchange_thread"].start()


@app.command()
def show():
    set_should_display_callbacks_logs(True)


@app.command()
def hide():
    set_should_display_callbacks_logs(False)


#  create-order --exchange_name binance --symbol BTC/USDT --price 10000 --quantity 1 --order_type buy_limit
@app.command()
@click.option("--exchange_name", prompt="Exchange name", help="The name of the exchange to use.", type=str)
@click.option("--symbol", prompt="Order symbol", help="The order symbol.", type=str)
@click.option("--price", prompt="Order price", help="The order price.", type=float)
@click.option("--quantity", prompt="Order quantity", help="The order quantity.", type=float)
@click.option("--order_type", prompt="Order type", help="The order type.",
              type=click.Choice([t.value for t in TraderOrderType]))
def create_order(exchange_name, symbol, price, quantity, order_type):
    exchange_manager = exchanges[exchange_name]["exchange_factory"].exchange_manager

    created_order = exchange_manager.trader.create_order_instance(order_type=TraderOrderType(order_type),
                                                                  symbol=symbol,
                                                                  current_price=price,
                                                                  quantity=quantity,
                                                                  price=price)
    asyncio.get_event_loop().run_until_complete(exchange_manager.trader.create_order(created_order))


#  orders --exchange_name binance --symbol BTC/USDT
@app.command()
@click.option("--exchange_name", prompt="Exchange name", help="The name of the exchange to use.", type=str)
@click.option("--symbol", prompt="Order symbol", help="The order symbol.", type=str)
def orders(exchange_name, symbol):
    exchange_manager = exchanges[exchange_name]["exchange_factory"].exchange_manager
    click.echo(exchange_manager.exchange_personal_data.orders_manager.get_open_orders(symbol))


@app.command()
@click.option("--exchange_name", prompt="Exchange name", help="The name of the exchange to use.")
# @click.option("--api_key", prompt="API key", help="The api key of the exchange to use.")
# @click.option("--api_secret", prompt="API secret", help="The api secret of the exchange to use.")
def connect(exchange_name):
    if exchange_name not in exchanges:
        exchange_factory = create_new_exchange(get_config(), exchange_name,
                                               is_simulated=False,
                                               is_backtesting=False,
                                               is_sandboxed=False)

        exchanges[exchange_name] = {
            "exchange_factory": exchange_factory,
            "exchange_thread": Thread(target=start_cli_exchange, args=(exchange_factory,))
        }

        exchanges[exchange_name]["exchange_thread"].start()
    else:
        click.echo("Already connected to this exchange", err=True)
        return
    click.echo(f"Connected to {exchange_name}")
