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
from octobot_commons.constants import CONFIG_WILDCARD
from octobot_commons.logging.logging_util import get_logger
from octobot_commons.tentacles_management import create_classes_list

from octobot_trading.api import LOGGER_TAG
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.modes import AbstractTradingMode
from octobot_trading.util.trading_config_util import get_activated_trading_mode as util_get_activated_trading_mode


def init_trading_mode_config(config) -> None:
    create_classes_list(config, AbstractTradingMode)


def get_trading_modes(exchange_manager) -> list:
    return exchange_manager.trading_modes


def get_trading_mode_symbol(trading_mode) -> list:
    return trading_mode.symbol


def get_trading_mode_current_state(trading_mode) -> tuple:
    return trading_mode.get_current_state()


def get_activated_trading_mode(config, tentacles_setup_config) -> AbstractTradingMode.__class__:
    return util_get_activated_trading_mode(config, tentacles_setup_config)


async def create_trading_modes(config: dict, exchange_manager: ExchangeManager, tentacles_setup_config: object) -> list:
    return await _create_trading_modes(trading_mode_class=util_get_activated_trading_mode(config,
                                                                                          tentacles_setup_config),
                                       config=config,
                                       exchange_manager=exchange_manager,
                                       cryptocurrencies=exchange_manager.exchange_config.traded_cryptocurrencies,
                                       symbols=exchange_manager.exchange_config.traded_symbol_pairs,
                                       time_frames=exchange_manager.exchange_config.traded_time_frames)


async def _create_trading_modes(trading_mode_class: AbstractTradingMode.__class__,
                                config: dict,
                                exchange_manager: ExchangeManager,
                                cryptocurrencies: list = None,
                                symbols: list = None,
                                time_frames: list = None) -> list:
    return [
        await create_trading_mode(trading_mode_class=trading_mode_class,
                                  config=config,
                                  exchange_manager=exchange_manager,
                                  cryptocurrency=cryptocurrency,
                                  symbol=symbol,
                                  time_frame=time_frame)
        for cryptocurrency in __get_cryptocurrencies_to_create(trading_mode_class, cryptocurrencies)
        for symbol in __get_symbols_to_create(trading_mode_class, symbols)
        for time_frame in __get_time_frames_to_create(trading_mode_class, time_frames)
    ]


async def create_trading_mode(trading_mode_class: AbstractTradingMode.__class__,
                              config: dict,
                              exchange_manager: ExchangeManager,
                              cryptocurrency: str = None,
                              symbol: str = None,
                              time_frame: object = None) -> AbstractTradingMode:
    try:
        trading_mode: AbstractTradingMode = trading_mode_class(config, exchange_manager)
        trading_mode.cryptocurrency = cryptocurrency
        trading_mode.symbol = symbol
        trading_mode.time_frame = time_frame
        await trading_mode.initialize()
        get_logger(f"{LOGGER_TAG}[{exchange_manager.exchange_name}]") \
            .debug(f"{trading_mode.get_name()} started for "
                   f"[cryptocurrency={cryptocurrency if cryptocurrency else CONFIG_WILDCARD},"
                   f" symbol={symbol if symbol else CONFIG_WILDCARD},"
                   f" time_frame={time_frame if time_frame else CONFIG_WILDCARD}]")
        return trading_mode
    except RuntimeError as e:
        get_logger(LOGGER_TAG).error(e.args[0])
        raise e


def __get_cryptocurrencies_to_create(trading_mode_class: AbstractTradingMode.__class__, cryptocurrencies: list) -> list:
    return cryptocurrencies if cryptocurrencies and not trading_mode_class.get_is_cryptocurrency_wildcard() else [None]


def __get_symbols_to_create(trading_mode_class: AbstractTradingMode.__class__, symbols: list) -> list:
    return symbols if symbols and not trading_mode_class.get_is_symbol_wildcard() else [None]


def __get_time_frames_to_create(trading_mode_class: AbstractTradingMode.__class__, time_frames: list) -> list:
    return time_frames if time_frames and not trading_mode_class.get_is_time_frame_wildcard() else [None]
