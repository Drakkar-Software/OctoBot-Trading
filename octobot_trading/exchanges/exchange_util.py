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
from octobot_commons.tentacles_management.class_inspector import get_all_classes_from_parent
from octobot_tentacles_manager.api.configurator import is_tentacle_activated_in_tentacles_setup_config
from octobot_trading.exchanges.types.future_exchange import FutureExchange
from octobot_trading.exchanges.types.margin_exchange import MarginExchange
from octobot_trading.exchanges.types.spot_exchange import SpotExchange
from octobot_trading.exchanges.rest_exchange import RestExchange


def get_margin_exchange_class(exchange_type, tentacles_setup_config):
    return _search_exchange_class_from_exchange_type(exchange_type, MarginExchange, tentacles_setup_config)


def get_future_exchange_class(exchange_type, tentacles_setup_config):
    return _search_exchange_class_from_exchange_type(exchange_type, FutureExchange, tentacles_setup_config)


def get_spot_exchange_class(exchange_type, tentacles_setup_config):
    return _search_exchange_class_from_exchange_type(exchange_type, SpotExchange, tentacles_setup_config)


def get_rest_exchange_class(exchange_type, tentacles_setup_config):
    exchange_class_candidate: RestExchange = _search_exchange_class_from_exchange_type(exchange_type,
                                                                                       RestExchange,
                                                                                       tentacles_setup_config)
    return exchange_class_candidate if exchange_class_candidate is not None else RestExchange


def _search_exchange_class_from_exchange_type(exchange_type, exchange_class, tentacles_setup_config):
    for exchange_candidate in get_all_classes_from_parent(exchange_class):
        try:
            if exchange_candidate.get_name() == exchange_type.__name__ and \
                    tentacles_setup_config is not None and \
                    is_tentacle_activated_in_tentacles_setup_config(tentacles_setup_config,
                                                                    exchange_candidate.__name__):
                return exchange_candidate
        except NotImplementedError:
            # A subclass of AbstractExchange will raise a NotImplementedError when calling its get_name() method
            # Here we are returning only a subclass that matches the expected name
            # Only Exchange Tentacles are implementing get_name() to specify the related exchange
            # As we are searching for an exchange_type specific subclass
            # We should ignore classes that raises NotImplementedError
            pass

    return None
