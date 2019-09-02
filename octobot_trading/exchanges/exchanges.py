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
from octobot_commons.singleton.singleton_class import Singleton


class ExchangeConfiguration:
    def __init__(self, exchange_manager):
        self.exchange_manager = exchange_manager
        self.exchange_name = exchange_manager.exchange.name
        self.symbols = exchange_manager.traded_pairs
        self.time_frames = exchange_manager.time_frames


class Exchanges(Singleton):
    def __init__(self):
        self.exchanges = {}

    def add_exchange(self, exchange_manager) -> None:
        self.exchanges[exchange_manager.exchange.name] = ExchangeConfiguration(exchange_manager)

    def get_exchange(self, exchange_name) -> ExchangeConfiguration:
        return self.exchanges[exchange_name]
