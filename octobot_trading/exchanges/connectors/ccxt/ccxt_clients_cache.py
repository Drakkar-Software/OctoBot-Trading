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


# To avoid side effects related to a cache refresh at a fix time of the day every day,
# cache should not be refreshed at the same time every day.
# Use 30h and 18min as a period. It could be anything else as long as it doesn't make it so
# that cache ends up refreshed approximately at the same time of the day
_CACHE_TIME = commons_constants.HOURS_TO_SECONDS * 30 + commons_constants.MINUTE_TO_SECONDS * 18
_MARKETS_BY_EXCHANGE = cachetools.TTLCache(maxsize=50, ttl=_CACHE_TIME)


def get_client_key(client) -> str:
    return f"{client.__class__.__name__}:{json.dumps(client.urls.get('api'))}"


def get_exchange_parsed_markets(client_key: str):
    return _MARKETS_BY_EXCHANGE[client_key]


def set_exchange_parsed_markets(client_key: str, markets):
    _MARKETS_BY_EXCHANGE[client_key] = markets
