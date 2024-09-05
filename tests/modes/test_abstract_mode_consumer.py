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
import mock
import pytest

import octobot_commons.constants as commons_constants
from octobot_backtesting.backtesting import Backtesting
from octobot_commons.tests.test_config import load_test_config
from octobot_trading.modes.channel.abstract_mode_consumer import AbstractTradingModeConsumer
from octobot_trading.enums import EvaluatorStates, TradingModeActivityType
from octobot_trading.constants import TRADING_MODE_ACTIVITY_REASON
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.modes import AbstractTradingMode, AbstractTradingModeProducer, TradingModeActivity
from octobot_trading.exchanges.traders.trader_simulator import TraderSimulator
from tests import event_loop

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def _get_tools():
    symbol = "BTC/USDT"
    config = load_test_config()
    config[commons_constants.CONFIG_SIMULATOR][commons_constants.CONFIG_STARTING_PORTFOLIO]["SUB"] = \
        0.000000000000000000005
    config[commons_constants.CONFIG_SIMULATOR][commons_constants.CONFIG_STARTING_PORTFOLIO]["BNB"] = \
        0.000000000000000000005
    config[commons_constants.CONFIG_SIMULATOR][commons_constants.CONFIG_STARTING_PORTFOLIO]["USDT"] = 2000
    exchange_manager = ExchangeManager(config, "binanceus")

    # use backtesting not to spam exchanges apis
    exchange_manager.is_simulated = True
    exchange_manager.is_backtesting = True
    exchange_manager.use_cached_markets = False
    exchange_manager.backtesting = Backtesting(None, [exchange_manager.id], None, [], False)

    await exchange_manager.initialize(exchange_config_by_exchange=None)

    trader = TraderSimulator(config, exchange_manager)
    await trader.initialize()
    
    mode = AbstractTradingMode(config, exchange_manager)
    consumer = AbstractTradingModeConsumer(mode)

    return exchange_manager, symbol, consumer


async def test_can_create_order():
    _, symbol, consumer = await _get_tools()
    # portfolio: "BTC": 10 "USD": 1000
    not_owned_symbol = "ETH/BTC"
    not_owned_market = "BTC/ETH"
    min_trigger_symbol = "SUB/BTC"
    min_trigger_market = "ADA/BNB"

    # order from neutral state => true
    assert await consumer.can_create_order(symbol, EvaluatorStates.NEUTRAL.value)

    # sell order using a currency with 0 available
    assert not await consumer.can_create_order(not_owned_symbol, EvaluatorStates.SHORT.value)
    assert not await consumer.can_create_order(not_owned_symbol, EvaluatorStates.VERY_SHORT.value)

    # sell order using a currency with < min available
    assert not await consumer.can_create_order(min_trigger_symbol, EvaluatorStates.SHORT.value)
    assert not await consumer.can_create_order(min_trigger_symbol, EvaluatorStates.VERY_SHORT.value)

    # sell order using a currency with > min available
    assert await consumer.can_create_order(not_owned_market, EvaluatorStates.SHORT.value)
    assert await consumer.can_create_order(not_owned_market, EvaluatorStates.VERY_SHORT.value)

    # buy order using a market with 0 available
    assert not await consumer.can_create_order(not_owned_market, EvaluatorStates.LONG.value)
    assert not await consumer.can_create_order(not_owned_market, EvaluatorStates.VERY_LONG.value)

    # buy order using a market with < min available
    assert not await consumer.can_create_order(min_trigger_market, EvaluatorStates.LONG.value)
    assert not await consumer.can_create_order(min_trigger_market, EvaluatorStates.VERY_LONG.value)

    # buy order using a market with > min available
    assert await consumer.can_create_order(not_owned_symbol, EvaluatorStates.LONG.value)
    assert await consumer.can_create_order(not_owned_symbol, EvaluatorStates.VERY_LONG.value)


async def test_can_create_order_unknown_symbols():
    _, _, consumer = await _get_tools()
    unknown_symbol = "VI?/BTC"
    unknown_market = "BTC/*s?"
    unknown_everything = "VI?/*s?"

    # buy order with unknown market
    assert not await consumer.can_create_order(unknown_market, EvaluatorStates.LONG.value)
    assert not await consumer.can_create_order(unknown_market, EvaluatorStates.VERY_LONG.value)
    assert await consumer.can_create_order(unknown_market, EvaluatorStates.SHORT.value)
    assert await consumer.can_create_order(unknown_market, EvaluatorStates.VERY_SHORT.value)

    # sell order with unknown symbol
    assert not await consumer.can_create_order(unknown_symbol, EvaluatorStates.SHORT.value)
    assert not await consumer.can_create_order(unknown_symbol, EvaluatorStates.VERY_SHORT.value)
    assert await consumer.can_create_order(unknown_symbol, EvaluatorStates.LONG.value)
    assert await consumer.can_create_order(unknown_symbol, EvaluatorStates.VERY_LONG.value)

    # neutral state with unknown symbol, market and everything
    assert await consumer.can_create_order(unknown_symbol, EvaluatorStates.NEUTRAL.value)
    assert await consumer.can_create_order(unknown_market, EvaluatorStates.NEUTRAL.value)
    assert await consumer.can_create_order(unknown_everything,  EvaluatorStates.NEUTRAL.value)


async def test_valid_create_new_order():
    _, symbol, consumer = await _get_tools()

    # should raise NotImplementedError Exception
    with pytest.raises(NotImplementedError):
        await consumer.create_new_orders(symbol, -1, EvaluatorStates.NEUTRAL)
    with pytest.raises(NotImplementedError):
        await consumer.create_new_orders(symbol, -1, EvaluatorStates.VERY_SHORT, xyz=1)
    with pytest.raises(NotImplementedError):
        await consumer.create_new_orders(symbol, -1, EvaluatorStates.LONG, xyz=1, aaa="bbb")


async def test_get_number_of_traded_assets():
    exchange_manager, symbol, consumer = await _get_tools()
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio_value_holder.\
        origin_crypto_currencies_values = {
            symbol: 1,
            "xyz": 2,
            "aaa": 3
        }
    assert consumer.get_number_of_traded_assets() == 3


async def test_update_producer_last_activity():
    exchange_manager, symbol, consumer = await _get_tools()
    mode = consumer.trading_mode
    producer = AbstractTradingModeProducer(
        mock.Mock(exchange_manager=exchange_manager), exchange_manager.config, mode, exchange_manager
    )
    mode.producers.append(producer)
    assert producer.last_activity == TradingModeActivity()
    consumer._update_producer_last_activity(TradingModeActivityType.NOTHING_TO_DO, "plop")
    assert producer.last_activity == TradingModeActivity(
        TradingModeActivityType.NOTHING_TO_DO, {TRADING_MODE_ACTIVITY_REASON: "plop"}
    )
    consumer._update_producer_last_activity(TradingModeActivityType.CREATED_ORDERS, "11")
    assert producer.last_activity == TradingModeActivity(
        TradingModeActivityType.CREATED_ORDERS, {TRADING_MODE_ACTIVITY_REASON: "11"}
    )
