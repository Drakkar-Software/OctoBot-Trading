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
import os

import pytest

import octobot_trading.constants as constants
import octobot_trading.errors as errors
import octobot_trading.enums as enums
import octobot_trading.exchange_data.contracts as contracts
from octobot_trading.personal_data import FuturePortfolio, BuyMarketOrder, SellMarketOrder, SellLimitOrder, \
    StopLossOrder

from tests.exchanges import backtesting_trader, backtesting_config, backtesting_exchange_manager, fake_backtesting, \
    DEFAULT_EXCHANGE_NAME

# All test coroutines will be treated as marked.
from tests.exchanges.traders import DEFAULT_FUTURE_SYMBOL, DEFAULT_FUTURE_SYMBOL_MARGIN_TYPE, \
    DEFAULT_FUTURE_SYMBOL_LEVERAGE

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
async def test_update_portfolio_available_from_order_with_market_buy_long_linear_contract(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    await init_symbol_contract(exchange_manager.exchange, leverage=decimal.Decimal(5))

    # Test buy order
    market_buy = BuyMarketOrder(trader)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol="BTC/USDT",
                      current_price=decimal.Decimal(str(1000)),
                      quantity=decimal.Decimal(str(2.5)),  # real quantity = 2.5 / 5 = 0.5 BTC at 1000$
                      price=decimal.Decimal(str(1000)))

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    # 1000 - 0.5 BTC * 1000$ = 500
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(500))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000))

    # Test buy order
    market_buy = BuyMarketOrder(trader)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol="BTC/USDT",
                      current_price=decimal.Decimal(str(74)),
                      quantity=decimal.Decimal(str(5)),  # real quantity = 5 / 5 = 1 BTC at 74$
                      price=decimal.Decimal(str(74)))

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(1000)
    # 500 - 1 BTC * 74$ = 426
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(426))

    # test cancel buy order
    portfolio_manager.portfolio.update_portfolio_available(market_buy, False)
    # 426 + 1 BTC * 74$ = 500
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(500))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(10)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(str(10))


@pytest.mark.parametrize("backtesting_exchange_manager", [(None, DEFAULT_EXCHANGE_NAME, False, False, True)],
                         indirect=["backtesting_exchange_manager"])
async def test_update_portfolio_available_from_order_with_market_buy_long_inverse_contract(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    symbol_contract = contracts.FutureContract(
        pair=DEFAULT_FUTURE_SYMBOL,
        margin_type=DEFAULT_FUTURE_SYMBOL_MARGIN_TYPE,
        contract_type=enums.FutureContractType.INVERSE_PERPETUAL,
        current_leverage=DEFAULT_FUTURE_SYMBOL_LEVERAGE)
    trader.exchange_manager.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)

    # Test buy order
    market_buy = BuyMarketOrder(trader)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol="BTC/USDT",
                      current_price=decimal.Decimal(str(1000)),
                      quantity=decimal.Decimal(str(1000)),  # real quantity = 1000 / 1000 = 1 BTC at 1000$
                      price=decimal.Decimal(str(1000)))

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(str(9))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(str(10))

    # Test buy order
    market_buy = BuyMarketOrder(trader)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol="BTC/USDT",
                      current_price=decimal.Decimal(str(74)),
                      quantity=decimal.Decimal(str(74/3)),  # real quantity = 0.3 BTC at 74$
                      price=decimal.Decimal(str(74)))

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(10)
    # 9 - (74 / 3) / 74 = 8.666666666666666648648648649
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal('8.666666666666666648648648649')

    # test cancel buy order
    portfolio_manager.portfolio.update_portfolio_available(market_buy, False)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(9)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000))


@pytest.mark.parametrize("backtesting_exchange_manager", [(None, DEFAULT_EXCHANGE_NAME, False, False, True)],
                         indirect=["backtesting_exchange_manager"])
async def test_update_portfolio_data_from_order_with_market_buy_long_linear_contract(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    await init_symbol_contract(exchange_manager.exchange, leverage=decimal.Decimal(5))

    # Test buy order
    market_buy = BuyMarketOrder(trader)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol="BTC/USDT",
                      current_price=decimal.Decimal(str(1000)),
                      quantity=decimal.Decimal(str(3)),  # real quantity = 3 / 5 = 0.6
                      price=decimal.Decimal(str(1000)))

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    portfolio_manager.portfolio.update_portfolio_data_from_order(market_buy)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(1600.0))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1600.0))

    # Test buy order
    market_buy = BuyMarketOrder(trader)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol="BTC/USDT",
                      current_price=decimal.Decimal(str(7.5)),
                      quantity=decimal.Decimal(str(30)),
                      price=decimal.Decimal(str(7.5)))

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    portfolio_manager.portfolio.update_portfolio_data_from_order(market_buy)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(1645.0))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1645.0))

    # Test reducing LONG position with a sell market order
    market_sell = SellMarketOrder(trader)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol="BTC/USDT",
                       current_price=decimal.Decimal(str(54)),
                       quantity=decimal.Decimal(str(20)),
                       price=decimal.Decimal(str(54)))

    # Should restore to first test step asserts
    portfolio_manager.portfolio.update_portfolio_available(market_sell, True)
    portfolio_manager.portfolio.update_portfolio_data_from_order(market_sell)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(10)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(1861))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(10)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1861))


@pytest.mark.parametrize("backtesting_exchange_manager", [(None, DEFAULT_EXCHANGE_NAME, False, False, True)],
                         indirect=["backtesting_exchange_manager"])
async def test_update_portfolio_data_from_order_that_triggers_negative_portfolio_linear_contract(
        backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    await init_symbol_contract(exchange_manager.exchange, leverage=decimal.Decimal(5))

    # Test buy order
    market_buy = BuyMarketOrder(trader)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol="BTC/USDT",
                      current_price=decimal.Decimal(str(1000)),
                      quantity=decimal.Decimal(str(100000000)),
                      price=decimal.Decimal(str(1000)))

    # test buy order creation
    if not os.getenv('CYTHON_IGNORE'):
        with pytest.raises(errors.PortfolioNegativeValueError):
            portfolio_manager.portfolio.update_portfolio_available(market_buy, True)


@pytest.mark.parametrize("backtesting_exchange_manager", [(None, DEFAULT_EXCHANGE_NAME, False, False, True)],
                         indirect=["backtesting_exchange_manager"])
async def test_update_portfolio_data_from_order_with_cancelled_and_filled_orders_linear_contract(
        backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    await init_symbol_contract(exchange_manager.exchange, leverage=decimal.Decimal(5))

    # Test sell order
    market_sell = SellMarketOrder(trader)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol="BTC/USDT",
                       current_price=decimal.Decimal(str(80)),
                       quantity=decimal.Decimal(str(12)),
                       price=decimal.Decimal(str(80)))

    # Test sell order
    limit_sell = SellLimitOrder(trader)
    limit_sell.update(order_type=enums.TraderOrderType.SELL_LIMIT,
                      symbol="BTC/USDT",
                      current_price=decimal.Decimal(str(10)),
                      quantity=decimal.Decimal(str(46.5)),
                      price=decimal.Decimal(str(10)))

    # Test stop loss order
    stop_loss = StopLossOrder(trader)
    stop_loss.update(order_type=enums.TraderOrderType.STOP_LOSS,
                     symbol="BTC/USDT",
                     current_price=decimal.Decimal(str(80)),
                     quantity=decimal.Decimal(str(46.5)),
                     price=decimal.Decimal(str(80)))

    portfolio_manager.portfolio.update_portfolio_available(stop_loss, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')

    portfolio_manager.portfolio.update_portfolio_available(limit_sell, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('907.0')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')

    portfolio_manager.portfolio.update_portfolio_available(market_sell, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('715.0')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')

    portfolio_manager.portfolio.update_portfolio_data_from_order(market_sell)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('1099.0')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1192.0')

    # cancel other orders
    portfolio_manager.portfolio.update_portfolio_available(stop_loss, False)
    portfolio_manager.portfolio.update_portfolio_available(limit_sell, False)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal('10')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('1192.0')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal('10')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1192.0')


@pytest.mark.parametrize("backtesting_exchange_manager", [(None, DEFAULT_EXCHANGE_NAME, False, False, True)],
                         indirect=["backtesting_exchange_manager"])
async def test_update_portfolio_data_from_order_with_huge_loss_on_filled_orders_linear_contract(
        backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    await init_symbol_contract(exchange_manager.exchange, leverage=decimal.Decimal(10))

    # Test sell order
    market_sell = SellMarketOrder(trader)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol="BTC/USDT",
                       current_price=decimal.Decimal(str(100)),
                       quantity=decimal.Decimal(str(25)),
                       price=decimal.Decimal(str(100)))

    # Test buy order
    market_buy = BuyMarketOrder(trader)
    market_buy.update(order_type=enums.TraderOrderType.SELL_MARKET,
                      symbol="BTC/USDT",
                      current_price=decimal.Decimal(str(120)),
                      quantity=decimal.Decimal(str(25)),
                      price=decimal.Decimal(str(120)))

    portfolio_manager.portfolio.update_portfolio_available(market_sell, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('750.0')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')

    # Open short position
    portfolio_manager.portfolio.update_portfolio_data_from_order(market_sell)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('1250.0')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1250.0')

    portfolio_manager.portfolio.update_portfolio_available(market_sell, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1250')

    # Close short position with loss
    portfolio_manager.portfolio.update_portfolio_data_from_order(market_sell)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('1500.0')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1500.0')
