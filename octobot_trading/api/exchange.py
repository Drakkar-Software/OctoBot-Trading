# pylint: disable=protected-access
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
import trading_backend

import octobot_trading.constants
import octobot_trading.enums
import octobot_trading.exchanges as exchanges
import octobot_trading.exchange_data as exchange_data

import octobot_backtesting.api as backtesting_api


def create_exchange_builder(config, exchange_name: str) -> exchanges.ExchangeBuilder:
    return exchanges.create_exchange_builder_instance(config, exchange_name)


async def stop_exchange(exchange_manager) -> None:
    await exchange_manager.stop()


def get_exchange_configurations_from_exchange_name(exchange_name: str) -> dict:
    return exchanges.Exchanges.instance().get_exchanges(exchange_name)


def get_exchange_manager_from_exchange_name_and_id(exchange_name: str, exchange_id: str) -> object:
    return exchanges.Exchanges.instance().get_exchange(exchange_name, exchange_id).exchange_manager


async def get_exchange_available_time_frames(
        exchange_name: str,
        exchange_lib: octobot_trading.enums.ExchangeWrapperLibs = octobot_trading.enums.ExchangeWrapperLibs.CCXT
) -> list:
    """
    When using CCXT, prefer using the sync lib since no request is required to get time frames
    :param exchange_name: name of the exchange
    :param exchange_lib: octobot_trading.enums.ExchangeWrapperLibs to use
    :return: the list of time frames
    """
    try:
        # first try in available exchanges
        for exchange_configuration in get_exchange_configurations_from_exchange_name(exchange_name).values():
            return exchange_configuration.exchange_manager.client_time_frames
    except KeyError:
        async with exchanges.temporary_exchange_wrapper(exchange_name, exchange_lib) as wrapper:
            return list(await wrapper.get_available_time_frames())


def get_exchange_available_required_time_frames(exchange_name: str, exchange_id: str) -> list:
    return exchanges.Exchanges.instance().get_exchange(exchange_name, exchange_id).available_required_time_frames


# prefer get_exchange_configurations_from_exchange_name when possible
def get_exchange_configuration_from_exchange_id(exchange_id: str) -> exchanges.ExchangeConfiguration:
    for exchange_configs in exchanges.Exchanges.instance().exchanges.values():
        for exchange_config in exchange_configs.values():
            if exchange_config.exchange_manager.id == exchange_id:
                return exchange_config
    raise KeyError(f"No exchange configuration with id: {exchange_id}")


# prefer get_exchange_manager_from_exchange_name_and_id when possible
def get_exchange_manager_from_exchange_id(exchange_id: str) -> object:
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


def get_exchange_manager_is_sandboxed(exchange_manager) -> bool:
    return exchange_manager.is_sandboxed


def get_exchange_current_time(exchange_manager) -> float:
    return exchange_manager.exchange.get_exchange_current_time()


def get_exchange_allowed_time_lag(exchange_manager) -> float:
    return exchange_manager.exchange.allowed_time_lag


def get_exchange_id_from_matrix_id(exchange_name: str, matrix_id: str) -> str:
    for exchange_configuration in get_exchange_configurations_from_exchange_name(exchange_name).values():
        if exchange_configuration.matrix_id == matrix_id:
            return get_exchange_manager_id(exchange_configuration.exchange_manager)
    return None


def get_matrix_id_from_exchange_id(exchange_name: str, exchange_id: str) -> str:
    for exchange_configuration in get_exchange_configurations_from_exchange_name(exchange_name).values():
        if exchange_configuration.id == exchange_id:
            return exchange_configuration.matrix_id
    return None


def get_all_exchange_ids_from_matrix_id(matrix_id) -> list:
    return [
        exchange_configuration.id
        for exchange_configuration in exchanges.Exchanges.instance().get_all_exchanges()
        if exchange_configuration.matrix_id == matrix_id
    ]


def get_exchange_configuration_from_exchange(exchange_name: str, exchange_id: str) -> exchanges.ExchangeConfiguration:
    return exchanges.Exchanges.instance().get_exchange(exchange_name, exchange_id)


def get_all_exchange_ids_with_same_matrix_id(exchange_name: str, exchange_id: str) -> list:
    """
    Used to get all the exchange ids for the same octobot instance represented by the matrix_id
    :param exchange_name: the exchange name
    :param exchange_id: the exchange id
    :return: the exchange ids for the same matrix id
    """
    return get_all_exchange_ids_from_matrix_id(
        get_exchange_configuration_from_exchange(exchange_name, exchange_id).matrix_id)


def get_exchange_names() -> list:
    return exchanges.Exchanges.instance().get_exchange_names()


def get_exchange_ids() -> list:
    return exchanges.Exchanges.instance().get_exchange_ids()


def get_exchange_name(exchange_manager) -> str:
    return exchange_manager.get_exchange_name()


def has_only_ohlcv(exchange_importers):
    return exchanges.ExchangeSimulator.get_real_available_data(exchange_importers) == \
           set(exchange_data.SIMULATOR_PRODUCERS_TO_POSSIBLE_DATA_TYPE[octobot_trading.constants.OHLCV_CHANNEL])


def get_is_backtesting(exchange_manager) -> bool:
    return exchange_manager.is_backtesting


def get_backtesting_data_files(exchange_manager) -> list:
    if not get_is_backtesting(exchange_manager):
        raise RuntimeError("Require a backtesting exchange manager")
    return exchange_manager.exchange.get_backtesting_data_files()


def get_backtesting_data_file(exchange_manager, symbol, time_frame) -> str:
    if not get_is_backtesting(exchange_manager):
        raise RuntimeError("Require a backtesting exchange manager")
    return backtesting_api.get_data_file_from_importers(
        exchange_manager.exchange.connector.exchange_importers, symbol, time_frame
    )


def get_has_websocket(exchange_manager) -> bool:
    return exchange_manager.has_websocket


def supports_websockets(exchange_name: str, tentacles_setup_config) -> bool:
    return exchanges.supports_websocket(exchange_name, tentacles_setup_config)


def get_trading_pairs(exchange_manager) -> list:
    return exchange_manager.exchange_config.traded_symbol_pairs


def get_watched_timeframes(exchange_manager) -> list:
    return exchange_manager.exchange_config.traded_time_frames


def get_base_currency(exchange_manager, pair) -> str:
    return exchange_manager.exchange.get_pair_cryptocurrency(pair)


def get_fees(exchange_manager, symbol) -> dict:
    return exchange_manager.exchange.get_fees(symbol)


def get_max_handled_pair_with_time_frame(exchange_manager) -> int:
    return exchange_manager.exchange.get_max_handled_pair_with_time_frame()


def get_currently_handled_pair_with_time_frame(exchange_manager) -> int:
    return exchange_manager.get_currently_handled_pair_with_time_frame()


def get_required_historical_candles_count(exchange_manager) -> int:
    return exchange_manager.exchange_config.required_historical_candles_count \
        if exchange_manager.exchange_config.required_historical_candles_count > \
        octobot_trading.constants.DEFAULT_CANDLE_HISTORY_SIZE else octobot_trading.constants.DEFAULT_CANDLE_HISTORY_SIZE


def is_overloaded(exchange_manager) -> bool:
    return exchange_manager.get_is_overloaded()


async def is_compatible_account(exchange_name: str, exchange_config: dict, tentacles_setup_config) -> (bool, str):
    return await exchanges.is_compatible_account(exchange_name, exchange_config, tentacles_setup_config)


def is_sponsoring(exchange_name: str) -> bool:
    return trading_backend.is_sponsoring(exchange_name)


def is_valid_account(exchange_manager) -> bool:
    return exchange_manager.is_valid_account


def get_historical_ohlcv(exchange_manager, symbol, time_frame, start_time, end_time):
    return exchanges.get_historical_ohlcv(exchange_manager, symbol, time_frame, start_time, end_time)


def get_bot_id(exchange_manager):
    return exchange_manager.bot_id


def cancel_ccxt_throttle_task():
    for task in asyncio.all_tasks():
        # manually cancel ccxt async throttle task since it apparently can't be cancelled otherwise
        if str(task._coro).startswith("<coroutine object Throttler.looper at"):
            task.cancel()
