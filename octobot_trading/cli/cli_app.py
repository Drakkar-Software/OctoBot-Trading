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
import threading
import click
import click_shell

import octobot_trading.api as api
import octobot_trading.cli as cli
import octobot_trading.exchanges as exchanges
import octobot_trading.cli.cli_tools as cli_tools
import octobot_trading.enums as enums


@click_shell.shell(prompt='OctoBot-Trading > ', intro='Starting...')
def app():
    exchange_name = "binance"
    exchange_builder = exchanges.create_exchange_builder_instance(cli.get_config(), exchange_name) \
        .is_simulated() \
        .is_rest_only()

    cli.add_exchange(exchange_name, {
        "exchange_builder": exchange_builder,
        "exchange_thread": threading.Thread(target=cli_tools.start_cli_exchange, args=(exchange_builder,))
    })

    cli.get_exchange(exchange_name)["exchange_thread"].start()


@app.command()
def show():
    cli.set_should_display_callbacks_logs(True)


@app.command()
def hide():
    cli.set_should_display_callbacks_logs(False)


#  create_order --exchange_name binance --symbol BTC/USDT --price 11000 --quantity 1 --order_type buy_limit
@app.command()
@click.option("--exchange_name", prompt="Exchange name", help="The name of the exchange to use.", type=str)
@click.option("--symbol", prompt="Order symbol", help="The order symbol.", type=str)
@click.option("--price", prompt="Order price", help="The order price.", type=float)
@click.option("--quantity", prompt="Order quantity", help="The order quantity.", type=float)
@click.option("--order_type", prompt="Order type", help="The order type.",
              type=click.Choice([t.value for t in enums.TraderOrderType]))
def create_order(exchange_name, symbol, price, quantity, order_type):
    asyncio.get_event_loop().run_until_complete(
        api.create_order(cli.exchanges[exchange_name]["exchange_factory"].exchange_manager,
                         order_type=enums.TraderOrderType(order_type),
                         symbol=symbol,
                         current_price=price,
                         quantity=quantity,
                         price=price))


#  orders --exchange_name binance --symbol BTC/USDT
@app.command()
@click.option("--exchange_name", prompt="Exchange name", help="The name of the exchange to use.", type=str)
@click.option("--symbol", prompt="Order symbol", help="The order symbol.", type=str)
def orders(exchange_name, symbol):
    exchange_manager = cli.exchanges[exchange_name]["exchange_factory"].exchange_manager
    click.echo(api.get_open_orders(exchange_manager))


@app.command()
@click.option("--exchange_name", prompt="Exchange name", help="The name of the exchange to use.")
# @click.option("--api_key", prompt="API key", help="The api key of the exchange to use.")
# @click.option("--api_secret", prompt="API secret", help="The api secret of the exchange to use.")
def connect(exchange_name):
    if exchange_name not in cli.exchanges:
        exchange_builder = api.create_exchange_builder(cli.get_config(), exchange_name)

        cli.exchanges[exchange_name] = {
            "exchange_builder": exchange_builder,
            "exchange_thread": threading.Thread(target=cli_tools.start_cli_exchange, args=(exchange_builder,))
        }

        cli.exchanges[exchange_name]["exchange_thread"].start()
    else:
        click.echo("Already connected to this exchange", err=True)
        return
    click.echo(f"Connected to {exchange_name}")
