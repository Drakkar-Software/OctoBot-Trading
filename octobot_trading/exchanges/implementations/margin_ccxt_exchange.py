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
import octobot_trading.exchanges.implementations.ccxt_exchange_commons \
    as ccxt_exchange_commons
import octobot_trading.exchanges.types as exchanges_types


class MarginCCXTExchange(exchanges_types.MarginExchange, 
                         ccxt_exchange_commons.CCXTExchangeCommons):
    def get_default_type(self):
        return 'margin'
