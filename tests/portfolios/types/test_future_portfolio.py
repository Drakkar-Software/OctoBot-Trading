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
from octobot_commons.constants import PORTFOLIO_AVAILABLE, PORTFOLIO_TOTAL

from octobot_trading.enums import TraderOrderType
from octobot_trading.orders.types.limit.sell_limit_order import SellLimitOrder
from octobot_trading.orders.types.market.buy_market_order import BuyMarketOrder
from octobot_trading.portfolios.types.future_portfolio import FuturePortfolio

from tests.exchanges import backtesting_trader, backtesting_config, backtesting_exchange_manager, fake_backtesting, \
    DEFAULT_EXCHANGE_NAME

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("backtesting_exchange_manager", [(None, DEFAULT_EXCHANGE_NAME, False, False, True)],
                         indirect=["backtesting_exchange_manager"])
async def test_initial_portfolio(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager

    assert isinstance(portfolio_manager.portfolio, FuturePortfolio)


@pytest.mark.parametrize("backtesting_exchange_manager", [(None, DEFAULT_EXCHANGE_NAME, False, False, True)],
                         indirect=["backtesting_exchange_manager"])
async def test_update_portfolio_available_from_order_in_inverse_market(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager

    # Test buy order
    market_buy = BuyMarketOrder(trader)
    market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                      symbol="BTC/USDT",
                      current_price=1000,
                      quantity=10,
                      price=1000)

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 9.99
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 1000
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 10
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 1000


@pytest.mark.parametrize("backtesting_exchange_manager", [(None, DEFAULT_EXCHANGE_NAME, False, False, True)],
                         indirect=["backtesting_exchange_manager"])
async def test_update_portfolio_available_from_order_in_inverse_market_with_leverage(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager

    # set leverage
    exchange_manager.leverage_by_symbol["BTC/USDT"] = 10

    # Test buy order
    market_buy = BuyMarketOrder(trader)
    market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                      symbol="BTC/USDT",
                      current_price=1000,
                      quantity=10,
                      price=1000)

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 9.99
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 1000
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 10
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 1000
