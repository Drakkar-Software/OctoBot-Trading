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
import logging

import ccxt
import octobot_commons.logging as commons_logging

import octobot_trading.exchanges.connectors.abstract_websocket_connector as abstract_websocket_connector


class CCXTWebsocketConnector(abstract_websocket_connector.AbstractWebsocketConnector):
    def __init__(self,
                 config: object,
                 exchange_manager: object,
                 timeout: int = 120,
                 timeout_interval: int = 5):
        super().__init__(config, exchange_manager, timeout, timeout_interval)
        commons_logging.set_logging_level(self.LOGGERS, logging.WARNING)

        self.async_ccxt_client = None
        self.ccxt_client = None
        self.use_testnet = self.exchange_manager.is_sandboxed

    def initialize(self, currencies=None, pairs=None, time_frames=None, channels=None):
        self.async_ccxt_client = self.get_ccxt_async_client()()
        self.ccxt_client = getattr(ccxt, self.get_name())()
        self.ccxt_client.load_markets()
        super().initialize(currencies, pairs, time_frames, channels)

    @classmethod
    def is_handling_spot(cls) -> bool:
        return False

    @classmethod
    def is_handling_margin(cls) -> bool:
        return False

    @classmethod
    def is_handling_future(cls) -> bool:
        return False

    @classmethod
    def get_ccxt_async_client(cls):
        raise NotImplementedError("get_ccxt_async_client is not implemented")

    def get_pair_from_exchange(self, pair):
        try:
            return self.ccxt_client.market(pair)["symbol"]
        except ccxt.errors.BadSymbol:
            try:
                return self.ccxt_client.markets_by_id[pair]["symbol"]
            except KeyError:
                self.logger.error(f"Failed to get market of {pair}")
                return None

    def get_exchange_pair(self, pair):
        if pair in self.ccxt_client.symbols:
            try:
                return self.ccxt_client.market(pair)["id"]
            except KeyError:
                raise KeyError(f'{pair} is not supported on {self.get_name()}')
        else:
            raise ValueError(f'{pair} is not supported on {self.get_name()}')
