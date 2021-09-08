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
from octobot_commons.constants import PORTFOLIO_AVAILABLE, PORTFOLIO_TOTAL

from octobot_trading.enums import TraderOrderType, FutureContractType
from octobot_trading.personal_data import FuturePortfolio, BuyMarketOrder, SellMarketOrder
from octobot_trading.personal_data.positions.contracts.future_contract import FutureContract

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

    # set future contract
    btcusd_future_contract = FutureContract("BTC/USDT")
    btcusd_future_contract.current_leverage = 1
    btcusd_future_contract.contract_type = FutureContractType.INVERSE_PERPETUAL
    exchange_manager.exchange.set_pair_future_contract("BTC/USDT", btcusd_future_contract)

    # Test buy order
    market_buy = BuyMarketOrder(trader)
    market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                      symbol="BTC/USDT",
                      current_price=decimal.Decimal(str(1000)),
                      quantity=decimal.Decimal(str(10)),
                      price=decimal.Decimal(str(1000)))

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == decimal.Decimal(str(9.99))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == decimal.Decimal(str(1000))

    # Test buy order
    market_buy = BuyMarketOrder(trader)
    market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                      symbol="BTC/USDT",
                      current_price=decimal.Decimal(str(74)),
                      quantity=decimal.Decimal(str(23)),
                      price=decimal.Decimal(str(74)))

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert round(portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE), 15) == decimal.Decimal("9.679189189189189")
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == decimal.Decimal(str(1000))


@pytest.mark.parametrize("backtesting_exchange_manager", [(None, DEFAULT_EXCHANGE_NAME, False, False, True)],
                         indirect=["backtesting_exchange_manager"])
async def test_update_portfolio_available_from_order_in_inverse_market_with_leverage(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager

    # set future contract
    btcusd_future_contract = FutureContract("BTC/USDT")
    btcusd_future_contract.current_leverage = 10
    btcusd_future_contract.contract_type = FutureContractType.INVERSE_PERPETUAL
    exchange_manager.exchange.set_pair_future_contract("BTC/USDT", btcusd_future_contract)

    # Test buy order
    market_buy = BuyMarketOrder(trader)
    market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                      symbol="BTC/USDT",
                      current_price=decimal.Decimal(str(1000)),
                      quantity=decimal.Decimal(str(10)),
                      price=decimal.Decimal(str(1000)))

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == decimal.Decimal(str(9.999))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == decimal.Decimal(str(1000))


@pytest.mark.parametrize("backtesting_exchange_manager", [(None, DEFAULT_EXCHANGE_NAME, False, False, True)],
                         indirect=["backtesting_exchange_manager"])
async def test_update_portfolio_available_from_order_with_leverage(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager

    # set future contract
    btcusd_future_contract = FutureContract("BTC/USDT")
    btcusd_future_contract.current_leverage = 2
    btcusd_future_contract.contract_type = FutureContractType.PERPETUAL
    exchange_manager.exchange.set_pair_future_contract("BTC/USDT", btcusd_future_contract)

    # Test buy order
    market_buy = BuyMarketOrder(trader)
    market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                      symbol="BTC/USDT",
                      current_price=decimal.Decimal(str(555)),
                      quantity=decimal.Decimal(str(10)),
                      price=decimal.Decimal(str(555)))

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == decimal.Decimal(str(995))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == decimal.Decimal(str(1000))

    # Test sell order
    market_sell = SellMarketOrder(trader)
    market_sell.update(order_type=TraderOrderType.SELL_MARKET,
                       symbol="BTC/USDT",
                       current_price=decimal.Decimal(str(555)),
                       quantity=decimal.Decimal(str(3)),
                       price=decimal.Decimal(str(555)))

    # test sell order creation
    portfolio_manager.portfolio.update_portfolio_available(market_sell, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == decimal.Decimal(str(993.5))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == decimal.Decimal(str(1000))

    # Test limit order to restore initial portfolio with a is_new=False and a quantity of 10 + 3
    market_buy = BuyMarketOrder(trader)
    market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                      symbol="BTC/USDT",
                      current_price=decimal.Decimal(str(555)),
                      quantity=decimal.Decimal(str(13)),
                      price=decimal.Decimal(str(555)))

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, False)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == decimal.Decimal(str(1000))
