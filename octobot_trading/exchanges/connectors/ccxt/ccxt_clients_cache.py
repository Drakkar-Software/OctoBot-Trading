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
import json

import octobot_commons.constants as commons_constants


_MARKETS_BY_EXCHANGE = cachetools.TTLCache(maxsize=50, ttl=commons_constants.DAYS_TO_SECONDS*1)


def get_client_key(client) -> str:
    return f"{client.__class__.__name__}:{json.dumps(client.urls.get('api'))}"


def get_exchange_parsed_markets(client_key: str):
    return _MARKETS_BY_EXCHANGE[client_key]


def set_exchange_parsed_markets(client_key: str, markets):
    _MARKETS_BY_EXCHANGE[client_key] = markets
