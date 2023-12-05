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
import cachetools

import octobot_commons.constants as commons_constants


_MARKETS_BY_EXCHANGE = cachetools.TTLCache(maxsize=50, ttl=commons_constants.DAYS_TO_SECONDS*7)


def get_client_key(client) -> str:
    return client.__class__.__name__


def get_exchange_parsed_markets(exchange: str):
    return _MARKETS_BY_EXCHANGE[exchange]


def set_exchange_parsed_markets(exchange: str, markets):
    _MARKETS_BY_EXCHANGE[exchange] = markets
