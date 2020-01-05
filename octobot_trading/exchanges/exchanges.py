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
from octobot_commons.logging.logging_util import get_logger

from octobot_commons.singleton.singleton_class import Singleton


class ExchangeConfiguration:
    def __init__(self, exchange_manager):
        self.exchange_manager = exchange_manager
        self.exchange_name = exchange_manager.exchange.name
        self.id = exchange_manager.id
        self.cryptocurrencies = list(exchange_manager.exchange_config.traded_cryptocurrencies.keys())
        self.symbols = exchange_manager.exchange_config.traded_symbol_pairs
        self.time_frames = exchange_manager.exchange_config.traded_time_frames


class Exchanges(Singleton):
    def __init__(self):
        self.exchanges = {}

    def add_exchange(self, exchange_manager) -> None:
        if exchange_manager.exchange.name not in self.exchanges:
            self.exchanges[exchange_manager.exchange.name] = {}

        self.exchanges[exchange_manager.exchange.name][exchange_manager.id] = ExchangeConfiguration(exchange_manager)

    def get_exchange(self, exchange_name, exchange_manager_id) -> ExchangeConfiguration:
        return self.exchanges[exchange_name][exchange_manager_id]

    def get_all_exchanges(self):
        exchanges_list: list = []
        for exchange_name in self.exchanges.keys():
            exchanges_list += self.get_exchanges_list(exchange_name)
        return exchanges_list

    def get_exchanges(self, exchange_name) -> dict:
        return self.exchanges[exchange_name]

    def get_exchanges_list(self, exchange_name) -> list:
        return list(self.exchanges[exchange_name].values())

    def del_exchange(self, exchange_name, exchange_manager_id) -> None:
        try:
            self.exchanges[exchange_name].pop(exchange_manager_id, None)

            if not self.exchanges[exchange_name]:
                self.exchanges.pop(exchange_name, None)
        except KeyError:
            get_logger(self.__class__.__name__).warning(f"Can't del exchange {exchange_name} "
                                                        f"with id {exchange_manager_id}")
