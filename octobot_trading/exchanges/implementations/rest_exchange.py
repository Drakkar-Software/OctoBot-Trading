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
import contextlib
import decimal
import typing

from octobot_commons import enums as common_enums

import octobot_trading.enums as enums
import octobot_trading.errors as errors
import octobot_trading.exchanges.abstract_exchange as abstract_exchange
import octobot_trading.exchanges.types as exchanges_types
import octobot_trading.exchanges.connectors as exchange_connectors
import octobot_trading.personal_data as personal_data
from octobot_trading.enums import ExchangeConstantsOrderColumns as ecoc


class RestExchange(abstract_exchange.AbstractExchange):
    """
    RestExchange is only calling the right exchange connector and should be used for each exchange
    request regardless of the trading type (spot / future / etc)
    """
    DEFAULT_CONNECTOR_CLASS = exchange_connectors.CCXTExchange

    def __init__(self, config, exchange_manager, connector_class=DEFAULT_CONNECTOR_CLASS):
        super().__init__(config, exchange_manager)
        self.connector = connector_class(
            config,
            exchange_manager,
            additional_ccxt_config=self.get_additional_connector_config()  # move to connector
        )
        self.connector.client.options['defaultType'] = self.get_default_type() # move to connector

    async def initialize_impl(self):
        await self.connector.initialize()
        self.symbols = self.connector.symbols
        self.time_frames = self.connector.time_frames

    async def stop(self) -> None:
        await self.connector.stop()
        self.exchange_manager = None