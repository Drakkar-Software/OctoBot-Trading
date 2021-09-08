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
import decimal

import pytest
import octobot_trading.constants as constants
import octobot_commons.constants as commons_constants
from octobot_trading.enums import FeePropertyColumns, ExchangeConstantsMarketPropertyColumns, TraderOrderType
from octobot_trading.api.exchange import cancel_ccxt_throttle_task

# Import required fixtures
from tests import event_loop
from tests.exchanges import backtesting_trader, backtesting_config, backtesting_config, backtesting_exchange_manager, \
    DEFAULT_BACKTESTING_SYMBOL, DEFAULT_BACKTESTING_TF, DEFAULT_BACKTESTING_SPLIT_SYMBOL, DEFAULT_BACKTESTING_CURRENCY, \
    DEFAULT_BACKTESTING_MARKET, fake_backtesting

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


def _get_start_index_for_timeframe(nb_candles, min_limit, timeframe_multiplier):
    return int(nb_candles - (nb_candles - min_limit) / timeframe_multiplier) - 1


def _assert_fee(fee, currency, price, rate, fee_type):
    assert fee[FeePropertyColumns.CURRENCY.value] == currency
    assert fee[FeePropertyColumns.COST.value] == price
    assert fee[FeePropertyColumns.RATE.value] == rate
    assert fee[FeePropertyColumns.TYPE.value] == fee_type


async def test_is_authenticated(backtesting_trader):
    _, exchange_manager, trader_inst = backtesting_trader
    assert not exchange_manager.exchange.authenticated()


async def test_get_uniform_timestamp(backtesting_trader):
    _, exchange_manager, trader_inst = backtesting_trader
    assert exchange_manager.exchange.get_uniform_timestamp(1e8) == 1e5


async def test_get_max_handled_pair_with_time_frame(backtesting_trader):
    _, exchange_manager, _ = backtesting_trader
    assert exchange_manager.exchange.get_max_handled_pair_with_time_frame() == \
           constants.INFINITE_MAX_HANDLED_PAIRS_WITH_TIMEFRAME


async def test_get_split_pair_from_exchange(backtesting_trader):
    _, exchange_manager, trader_inst = backtesting_trader
    assert exchange_manager.exchange.get_split_pair_from_exchange(DEFAULT_BACKTESTING_SYMBOL) == \
           DEFAULT_BACKTESTING_SPLIT_SYMBOL


async def test_get_pair_cryptocurrency(backtesting_trader):
    _, exchange_manager, trader_inst = backtesting_trader
    return exchange_manager.exchange.get_pair_cryptocurrency(DEFAULT_BACKTESTING_SYMBOL) == DEFAULT_BACKTESTING_CURRENCY


async def test_get_trade_fee(backtesting_trader):
    _, exchange_manager, trader_inst = backtesting_trader

    # force fees
    exchange_manager.config[commons_constants.CONFIG_SIMULATOR][commons_constants.CONFIG_SIMULATOR_FEES] = {
        commons_constants.CONFIG_SIMULATOR_FEES_MAKER: 0.05,
        commons_constants.CONFIG_SIMULATOR_FEES_TAKER: 0.1
    }

    buy_market_fee = exchange_manager.exchange.get_trade_fee(DEFAULT_BACKTESTING_SYMBOL, TraderOrderType.BUY_MARKET, 10,
                                                             100, ExchangeConstantsMarketPropertyColumns.TAKER.value)
    _assert_fee(buy_market_fee, DEFAULT_BACKTESTING_CURRENCY, decimal.Decimal("0.01"), 0.001,
                ExchangeConstantsMarketPropertyColumns.TAKER.value)

    sell_market_fee = exchange_manager.exchange.get_trade_fee(
        DEFAULT_BACKTESTING_SYMBOL, TraderOrderType.SELL_MARKET, 10, 100,
        ExchangeConstantsMarketPropertyColumns.TAKER.value)
    _assert_fee(sell_market_fee, DEFAULT_BACKTESTING_MARKET, constants.ONE, 0.001,
                ExchangeConstantsMarketPropertyColumns.TAKER.value)


async def test_stop(backtesting_trader):
    _, exchange_manager, trader_inst = backtesting_trader
    await exchange_manager.exchange.stop()
    cancel_ccxt_throttle_task()
    assert not exchange_manager.exchange.backtesting
    assert not exchange_manager.exchange.exchange_importers