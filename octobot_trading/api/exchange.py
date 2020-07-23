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
import asyncio

from octobot_trading.constants import OHLCV_CHANNEL
from octobot_trading.exchanges.exchange_builder import ExchangeBuilder
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.exchanges.exchange_simulator import ExchangeSimulator
from octobot_trading.exchanges.exchanges import Exchanges, ExchangeConfiguration
from octobot_trading.producers.simulator import SIMULATOR_PRODUCERS_TO_POSSIBLE_DATA_TYPE


def create_exchange_builder(config, exchange_name) -> ExchangeBuilder:
    return ExchangeBuilder(config, exchange_name)


async def stop_exchange(exchange_manager) -> None:
    await exchange_manager.stop()


def get_exchange_configurations_from_exchange_name(exchange_name) -> dict:
    return Exchanges.instance().get_exchanges(exchange_name)


def get_exchange_manager_from_exchange_name_and_id(exchange_name, exchange_id) -> ExchangeManager:
    return Exchanges.instance().get_exchange(exchange_name, exchange_id).exchange_manager


def get_exchange_time_frames_without_real_time(exchange_name, exchange_id) -> list:
    return Exchanges.instance().get_exchange(exchange_name, exchange_id).time_frames_without_real_time


# prefer get_exchange_configurations_from_exchange_name when possible
def get_exchange_configuration_from_exchange_id(exchange_id) -> ExchangeConfiguration:
    for exchange_configs in Exchanges.instance().exchanges.values():
        for exchange_config in exchange_configs.values():
            if exchange_config.exchange_manager.id == exchange_id:
                return exchange_config
    raise KeyError(f"No exchange configuration with id: {exchange_id}")


# prefer get_exchange_manager_from_exchange_name_and_id when possible
def get_exchange_manager_from_exchange_id(exchange_id) -> ExchangeManager:
    try:
        return get_exchange_configuration_from_exchange_id(exchange_id).exchange_manager
    except KeyError:
        raise KeyError(f"No exchange manager with id: {exchange_id}")


def get_exchange_managers_from_exchange_ids(exchange_ids) -> list:
    return [get_exchange_manager_from_exchange_id(manager_id) for manager_id in exchange_ids]


def get_trading_exchanges(exchange_managers) -> list:
    return [exchange_manager for exchange_manager in exchange_managers
            if exchange_manager.is_trading]


def is_exchange_trading(exchange_manager) -> bool:
    return exchange_manager.is_trading


def get_exchange_manager_id(exchange_manager) -> str:
    return exchange_manager.id


def get_exchange_current_time(exchange_manager) -> float:
    return exchange_manager.exchange.get_exchange_current_time()


def get_exchange_allowed_time_lag(exchange_manager) -> float:
    return exchange_manager.exchange.allowed_time_lag


def get_exchange_id_from_matrix_id(exchange_name, matrix_id) -> str:
    for exchange_configuration in get_exchange_configurations_from_exchange_name(exchange_name).values():
        if exchange_configuration.matrix_id == matrix_id:
            return get_exchange_manager_id(exchange_configuration.exchange_manager)
    return None


def get_matrix_id_from_exchange_id(exchange_name, exchange_id) -> str:
    for exchange_configuration in get_exchange_configurations_from_exchange_name(exchange_name).values():
        if exchange_configuration.id == exchange_id:
            return exchange_configuration.matrix_id
    return None


def get_all_exchange_ids_from_matrix_id(matrix_id) -> list:
    return [
        exchange_configuration.id
        for exchange_configuration in Exchanges.instance().get_all_exchanges()
        if exchange_configuration.matrix_id == matrix_id
    ]


def get_exchange_configuration_from_exchange(exchange_name, exchange_id) -> ExchangeConfiguration:
    return Exchanges.instance().get_exchange(exchange_name, exchange_id)


def get_all_exchange_ids_with_same_matrix_id(exchange_name, exchange_id) -> list:
    """
    Used to get all the exchange ids for the same octobot instance represented by the matrix_id
    :param exchange_name: the exchange name
    :param exchange_id: the exchange id
    :return: the exchange ids for the same matrix id
    """
    return get_all_exchange_ids_from_matrix_id(
        get_exchange_configuration_from_exchange(exchange_name, exchange_id).matrix_id)


def get_exchange_names() -> list:
    return Exchanges.instance().get_exchange_names()


def get_exchange_ids() -> list:
    return Exchanges.instance().get_exchange_ids()


def get_exchange_name(exchange_manager) -> str:
    return exchange_manager.get_exchange_name()


def has_only_ohlcv(exchange_importers):
    return ExchangeSimulator.get_real_available_data(exchange_importers) == \
           set(SIMULATOR_PRODUCERS_TO_POSSIBLE_DATA_TYPE[OHLCV_CHANNEL])


def get_is_backtesting(exchange_manager) -> bool:
    return exchange_manager.is_backtesting


def get_trading_pairs(exchange_manager) -> list:
    return exchange_manager.exchange_config.traded_symbol_pairs


def get_watched_timeframes(exchange_manager) -> list:
    return exchange_manager.exchange_config.traded_time_frames


def get_base_currency(exchange_manager, pair) -> str:
    return exchange_manager.exchange.get_pair_cryptocurrency(pair)


def get_fees(exchange_manager, symbol) -> dict:
    return exchange_manager.exchange.get_fees(symbol)


def cancel_ccxt_throttle_task():
    for task in asyncio.all_tasks():
        # manually cancel ccxt async throttle task since it apparently can't be cancelled otherwise
        if str(task._coro).startswith("<coroutine object throttle.<locals>.run at"):
            task.cancel()
