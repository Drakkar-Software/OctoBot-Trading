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
import pytest

from octobot_commons.constants import PORTFOLIO_TOTAL
from octobot_commons.tests.test_config import load_test_config
from octobot_trading.constants import CONFIG_SIMULATOR, CONFIG_STARTING_PORTFOLIO
from octobot_trading.consumers.abstract_mode_consumer import AbstractTradingModeConsumer
from octobot_trading.enums import EvaluatorStates
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.modes import AbstractTradingMode
from octobot_trading.traders.trader_simulator import TraderSimulator


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def _get_tools():
    symbol = "BTC/USDT"
    config = load_test_config()
    config[CONFIG_SIMULATOR][CONFIG_STARTING_PORTFOLIO]["SUB"] = 0.000000000000000000005
    config[CONFIG_SIMULATOR][CONFIG_STARTING_PORTFOLIO]["BNB"] = 0.000000000000000000005
    config[CONFIG_SIMULATOR][CONFIG_STARTING_PORTFOLIO]["USDT"] = 2000
    exchange_manager = ExchangeManager(config, "binance")

    # use backtesting not to spam exchanges apis
    exchange_manager.is_simulated = True
    exchange_manager.is_backtesting = True

    # no backtesting file provided, except ValueError from initialize
    with pytest.raises(ValueError):
        await exchange_manager.initialize()

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

    # order from neutral state => false
    assert not await consumer.can_create_order(symbol, EvaluatorStates.NEUTRAL)

    # sell order using a currency with 0 available
    assert not await consumer.can_create_order(not_owned_symbol, EvaluatorStates.SHORT)
    assert not await consumer.can_create_order(not_owned_symbol, EvaluatorStates.VERY_SHORT)

    # sell order using a currency with < min available
    assert not await consumer.can_create_order(min_trigger_symbol, EvaluatorStates.SHORT)
    assert not await consumer.can_create_order(min_trigger_symbol, EvaluatorStates.VERY_SHORT)

    # sell order using a currency with > min available
    assert await consumer.can_create_order(not_owned_market, EvaluatorStates.SHORT)
    assert await consumer.can_create_order(not_owned_market, EvaluatorStates.VERY_SHORT)

    # buy order using a market with 0 available
    assert not await consumer.can_create_order(not_owned_market, EvaluatorStates.LONG)
    assert not await consumer.can_create_order(not_owned_market, EvaluatorStates.VERY_LONG)

    # buy order using a market with < min available
    assert not await consumer.can_create_order(min_trigger_market, EvaluatorStates.LONG)
    assert not await consumer.can_create_order(min_trigger_market, EvaluatorStates.VERY_LONG)

    # buy order using a market with > min available
    assert await consumer.can_create_order(not_owned_symbol, EvaluatorStates.LONG)
    assert await consumer.can_create_order(not_owned_symbol, EvaluatorStates.VERY_LONG)


async def test_can_create_order_unknown_symbols():
    _, _, consumer = await _get_tools()
    unknown_symbol = "VI?/BTC"
    unknown_market = "BTC/*s?"
    unknown_everything = "VI?/*s?"

    # buy order with unknown market
    assert not await consumer.can_create_order(unknown_market, EvaluatorStates.LONG)
    assert not await consumer.can_create_order(unknown_market, EvaluatorStates.VERY_LONG)
    assert await consumer.can_create_order(unknown_market, EvaluatorStates.SHORT)
    assert await consumer.can_create_order(unknown_market, EvaluatorStates.VERY_SHORT)

    # sell order with unknown symbol
    assert not await consumer.can_create_order(unknown_symbol, EvaluatorStates.SHORT)
    assert not await consumer.can_create_order(unknown_symbol, EvaluatorStates.VERY_SHORT)
    assert await consumer.can_create_order(unknown_symbol, EvaluatorStates.LONG)
    assert await consumer.can_create_order(unknown_symbol, EvaluatorStates.VERY_LONG)

    # neutral state with unknown symbol, market and everything
    assert not await consumer.can_create_order(unknown_symbol, EvaluatorStates.NEUTRAL)
    assert not await consumer.can_create_order(unknown_market, EvaluatorStates.NEUTRAL)
    assert not await consumer.can_create_order(unknown_everything,  EvaluatorStates.NEUTRAL)


async def test_valid_create_new_order():
    _, symbol, consumer = await _get_tools()

    # should raise NotImplementedError Exception
    with pytest.raises(NotImplementedError):
        await consumer.create_new_orders(symbol, -1, EvaluatorStates.NEUTRAL)
    with pytest.raises(NotImplementedError):
        await consumer.create_new_orders(symbol, -1, EvaluatorStates.VERY_SHORT, xyz=1)
    with pytest.raises(NotImplementedError):
        await consumer.create_new_orders(symbol, -1, EvaluatorStates.LONG, xyz=1, aaa="bbb")


async def test_get_holdings_ratio():
    exchange_manager, symbol, consumer = await _get_tools()
    exchange_manager.client_symbols = [symbol]
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio_profitability.currencies_last_prices[symbol] = \
        1000
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio_profitability.portfolio_current_value = 11
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio.portfolio = {
        "BTC": {
            PORTFOLIO_TOTAL: 10
        },
        "USDT": {
            PORTFOLIO_TOTAL: 1000
        }
    }
    ratio = await consumer.get_holdings_ratio("BTC")
    assert round(ratio, 8) == 0.90909091
    ratio = await consumer.get_holdings_ratio("USDT")
    assert round(ratio, 8) == 0.09090909

    exchange_manager.exchange_personal_data.portfolio_manager.portfolio.portfolio.pop("USDT")
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio_profitability.portfolio_current_value = 10
    ratio = await consumer.get_holdings_ratio("BTC")
    assert round(ratio, 8) == 1
    ratio = await consumer.get_holdings_ratio("USDT")
    assert round(ratio, 8) == 0
    ratio = await consumer.get_holdings_ratio("XYZ")
    assert round(ratio, 8) == 0


async def test_get_number_of_traded_assets():
    exchange_manager, symbol, consumer = await _get_tools()
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio_profitability.\
        origin_crypto_currencies_values = {
            symbol: 1,
            "xyz": 2,
            "aaa": 3
        }
    assert consumer.get_number_of_traded_assets() == 3
