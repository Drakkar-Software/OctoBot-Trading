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
import octobot_commons.logging as logging

from octobot_trading.exchange_data.exchange_symbol_data import ExchangeSymbolData


class ExchangeSymbolsData:
    def __init__(self, exchange_manager):
        self.logger = logging.get_logger(self.__class__.__name__)
        self.exchange_manager = exchange_manager
        self.exchange = exchange_manager.exchange
        self.config = exchange_manager.config
        self.exchange_symbol_data = {}

    async def stop(self):
        self.exchange_manager = None
        self.exchange = None
        for exchange_symbol_data in self.exchange_symbol_data.values():
            exchange_symbol_data.stop()
        self.exchange_symbol_data = {}

    def get_exchange_symbol_data(self, symbol, allow_creation=True) -> ExchangeSymbolData:
        try:
            return self.exchange_symbol_data[symbol]
        except KeyError as e:
            if allow_creation:
                # warning: should only be called in the async loop thread
                self.exchange_symbol_data[symbol] = ExchangeSymbolData(self.exchange_manager, symbol)
                return self.exchange_symbol_data[symbol]
            raise e
