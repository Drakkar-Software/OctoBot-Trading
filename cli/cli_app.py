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

from cli import exchanges, get_config, set_should_display_callbacks_logs
from cli.cli_tools import create_cli_exchange


@shell(prompt='OctoBot-Trading > ', intro='Starting...')
def app():
    pass


@app.command()
def show():
    set_should_display_callbacks_logs(True)


@app.command()
def hide():
    set_should_display_callbacks_logs(False)


@app.command()
@click.option("--exchange_name", prompt="Exchange name", help="The name of the exchange to use.")
# @click.option("--api_key", prompt="API key", help="The api key of the exchange to use.")
# @click.option("--api_secret", prompt="API secret", help="The api secret of the exchange to use.")
def connect(exchange_name):
    if exchange_name not in exchanges:
        exchanges[exchange_name] = Thread(target=create_cli_exchange, args=(get_config(), exchange_name))
        exchanges[exchange_name].start()
    else:
        click.echo("Already connected to this exchange", err=True)
        return
    click.echo(f"Connected to {exchange_name}")
