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
import uuid

import octobot_trading.constants
import octobot_trading.exchanges.traders.trader as trader
import octobot_trading.util as util


class TraderSimulator(trader.Trader):
    """
    TraderSimulator has a role of exchange response simulator
    - During order creation / filling / canceling process
    """

    NO_HISTORY_MESSAGE = "Starting a fresh new trading simulation session using trader simulator initial portfolio " \
                         "in configuration."

    def __init__(self, config, exchange_manager):
        self.simulate = True
        super().__init__(config, exchange_manager)

        self.trader_type_str = octobot_trading.constants.SIMULATOR_TRADER_STR

    @staticmethod
    def enabled(config):
        return util.is_trader_simulator_enabled(config)

    def parse_order_id(self, order_id):
        return str(uuid.uuid4()) if order_id is None else order_id
