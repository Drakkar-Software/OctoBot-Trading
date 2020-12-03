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
import octobot_commons.logging as logging
import octobot_commons.tentacles_management as tentacles_management

import octobot_tentacles_manager.api as api

import octobot_trading.enums as enums
import octobot_trading.exchanges.types as exchanges_types


def get_margin_exchange_class(exchange_name, tentacles_setup_config):
    return search_exchange_class_from_exchange_name(exchanges_types.MarginExchange, exchange_name,
                                                    tentacles_setup_config)


def get_future_exchange_class(exchange_name, tentacles_setup_config):
    return search_exchange_class_from_exchange_name(exchanges_types.FutureExchange, exchange_name,
                                                    tentacles_setup_config)


def get_spot_exchange_class(exchange_name, tentacles_setup_config):
    return search_exchange_class_from_exchange_name(exchanges_types.SpotExchange, exchange_name,
                                                    tentacles_setup_config)


def search_exchange_class_from_exchange_name(exchange_class, exchange_name,
                                             tentacles_setup_config, enable_default=False):
    for exchange_candidate in tentacles_management.get_all_classes_from_parent(exchange_class):
        try:
            if _is_exchange_candidate_matching(exchange_candidate, exchange_name,
                                               tentacles_setup_config, enable_default=enable_default):
                return exchange_candidate
        except NotImplementedError:
            # A subclass of AbstractExchange will raise a NotImplementedError when calling its get_name() method
            # Here we are returning only a subclass that matches the expected name
            # Only Exchange Tentacles are implementing get_name() to specify the related exchange
            # As we are searching for an exchange_type specific subclass
            # We should ignore classes that raises NotImplementedError
            pass

    if enable_default:
        return None

    logging.get_logger().debug(f"No specific exchange implementation for {exchange_name} found, using a default one.")
    return search_exchange_class_from_exchange_name(exchanges_types.SpotExchange, exchange_name,
                                                    tentacles_setup_config, enable_default=True)


def _is_exchange_candidate_matching(exchange_candidate, exchange_name, tentacles_setup_config, enable_default=False):
    return not exchange_candidate.is_simulated_exchange() and \
           (not exchange_candidate.is_default_exchange() or enable_default) and \
           exchange_candidate.is_supporting_exchange(exchange_name) and \
           (tentacles_setup_config is None or
            api.is_tentacle_activated_in_tentacles_setup_config(tentacles_setup_config,
                                                                exchange_candidate.__name__))


def get_order_side(order_type):
    return enums.TradeOrderSide.BUY.value if order_type in (enums.TraderOrderType.BUY_LIMIT,
                                                            enums.TraderOrderType.BUY_MARKET) \
        else enums.TradeOrderSide.SELL.value
