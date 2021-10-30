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
from octobot_trading.enums import TraderOrderType
import octobot_trading.constants as constants
from octobot_trading.personal_data import FuturePortfolio, BuyMarketOrder, SellMarketOrder

from tests.exchanges import backtesting_trader, backtesting_config, backtesting_exchange_manager, fake_backtesting, \
    DEFAULT_EXCHANGE_NAME

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

DEFAULT_SYMBOL = "BTC/USDT"


async def init_symbol_contract(exchange, symbol=DEFAULT_SYMBOL,
                               leverage=constants.ONE,
                               margin_type_isolated=True):
    # create BTC/USDT future contract
    await exchange.load_pair_future_contract(symbol)
    await exchange.set_symbol_leverage(symbol, leverage)
    await exchange.set_symbol_margin_type(symbol, margin_type_isolated)
    return exchange.get_pair_future_contract(symbol)


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
    await init_symbol_contract(exchange_manager.exchange, leverage=decimal.Decimal(5))

    # Test buy order
    market_buy = BuyMarketOrder(trader)
    market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                      symbol="BTC/USDT",
                      current_price=decimal.Decimal(str(1000)),
                      quantity=decimal.Decimal(str(10)),
                      price=decimal.Decimal(str(1000)))

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == decimal.Decimal(str(998))
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
    assert round(portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE), 15) == decimal.Decimal(10)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == decimal.Decimal(str("993.4"))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == decimal.Decimal(str(1000))


@pytest.mark.parametrize("backtesting_exchange_manager", [(None, DEFAULT_EXCHANGE_NAME, False, False, True)],
                         indirect=["backtesting_exchange_manager"])
async def test_update_portfolio_available_from_order_in_inverse_market_with_sell_market(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    await init_symbol_contract(exchange_manager.exchange, leverage=decimal.Decimal(2))

    # Test buy order
    market_buy = BuyMarketOrder(trader)
    market_buy.update(order_type=TraderOrderType.SELL_MARKET,
                      symbol="BTC/USDT",
                      current_price=decimal.Decimal(str(1000)),
                      quantity=decimal.Decimal(str(10)),
                      price=decimal.Decimal(str(1000)))

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == decimal.Decimal(str(995))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == decimal.Decimal(str(1000))


@pytest.mark.parametrize("backtesting_exchange_manager", [(None, DEFAULT_EXCHANGE_NAME, False, False, True)],
                         indirect=["backtesting_exchange_manager"])
async def test_update_portfolio_available_from_order(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    await init_symbol_contract(exchange_manager.exchange, leverage=decimal.Decimal(10))

    # Test buy order
    market_buy = BuyMarketOrder(trader)
    market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                      symbol="BTC/USDT",
                      current_price=decimal.Decimal(str(555)),
                      quantity=decimal.Decimal(str(10)),
                      price=decimal.Decimal(str(555)))

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == decimal.Decimal(10)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == decimal.Decimal(str(999))
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
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == decimal.Decimal(10)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == decimal.Decimal(str("998.7"))
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
