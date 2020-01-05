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
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.exchanges.exchanges import Exchanges
from octobot_trading.exchanges.exchange_factory import ExchangeFactory
from octobot_trading.channels.exchange_channel import get_chan, ExchangeChannel


def create_new_exchange(config, exchange_name,
                        is_simulated=False,
                        is_rest_only=False,
                        is_backtesting=False,
                        is_sandboxed=False,
                        is_collecting=False,
                        exchange_only=False,
                        backtesting_files=None) -> ExchangeFactory:
    return ExchangeFactory(config, exchange_name,
                           is_simulated=is_simulated,
                           is_backtesting=is_backtesting,
                           rest_only=is_rest_only,
                           is_sandboxed=is_sandboxed,
                           is_collecting=is_collecting,
                           exchange_only=exchange_only,
                           backtesting_files=backtesting_files)


def get_exchange_manager_from_exchange_name(exchange_name) -> ExchangeManager:
    return Exchanges.instance().get_exchange(exchange_name).exchange_manager


def get_exchange_names() -> list:
    return Exchanges.instance().get_exchange_names()


def get_exchange_channel(chan_name, exchange_name) -> ExchangeChannel:
    return get_chan(chan_name, exchange_name)


def get_exchange_name(exchange_manager) -> str:
    return exchange_manager.get_exchange_name()


def get_trading_pairs(exchange_manager) -> list:
    return exchange_manager.exchange_config.traded_symbol_pairs


def get_watched_timeframes(exchange_manager) -> list:
    return exchange_manager.exchange_config.traded_time_frames


async def force_refresh_orders_and_portfolio(exchange_manager):
    return await exchange_manager.trader.force_refresh_orders_and_portfolio()
