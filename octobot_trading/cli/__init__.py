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

exchanges = {}
config = {}
should_display_callbacks_logs = False


def set_should_display_callbacks_logs(display_callbacks_logs):
    global should_display_callbacks_logs
    should_display_callbacks_logs = display_callbacks_logs


def get_should_display_callbacks_logs():
    return should_display_callbacks_logs


def set_config(cli_config):
    global config
    config = cli_config


def get_config():
    return config


def get_exchanges():
    return exchanges


def get_exchange(exchange_name):
    return exchanges[exchange_name]


def add_exchange(exchange_name, exchange):
    global exchanges
    exchanges[exchange_name] = exchange
