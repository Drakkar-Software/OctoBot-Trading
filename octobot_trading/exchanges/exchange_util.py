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
#  Lesser General License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.

from octobot_trading.exchanges.margin.margin_exchange import MarginExchange
from octobot_trading.exchanges.rest_exchange import RestExchange


def get_margin_exchange_class(exchange_type):
    return _search_exchange_class_from_exchange_type(exchange_type, MarginExchange)


def get_rest_exchange_class(exchange_type):
    exchange_class_candidate: RestExchange = _search_exchange_class_from_exchange_type(exchange_type, RestExchange)
    return exchange_class_candidate if exchange_class_candidate is not None else RestExchange


def _search_exchange_class_from_exchange_type(exchange_type, exchange_class):
    for exchange_candidate in exchange_class.__subclasses__():
        try:
            if exchange_candidate.get_name() == exchange_type.__name__:
                return exchange_candidate
        except NotImplementedError:
            # A subclass of AbstractExchange will raise a NotImplementedError when calling its get_name() method
            # Here we are returning only a subclass that matches the expected name
            # Only Exchange Tentacles are implementing get_name() to specify the related exchange
            # As we are searching for an exchange_type specific subclass
            # We should ignore classes that raises NotImplementedError
            pass

    return None
