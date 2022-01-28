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
import mock

import octobot_trading.constants as constants
import octobot_trading.errors as errors
import octobot_trading.enums as enums
import octobot_trading.exchange_data.contracts as contracts
from octobot_trading.personal_data import FuturePortfolio, BuyMarketOrder, SellMarketOrder, SellLimitOrder, \
    StopLossOrder, LinearPosition, InversePosition

from tests import event_loop
from tests.exchanges import future_simulated_exchange_manager
from tests.exchanges.traders import future_trader, future_trader_simulator_with_default_linear, DEFAULT_FUTURE_SYMBOL, \
    DEFAULT_FUTURE_SYMBOL_MARGIN_TYPE, DEFAULT_FUTURE_SYMBOL_LEVERAGE, future_trader_simulator_with_default_inverse
from tests.test_utils.order_util import fill_market_order

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def _update_position_mark_price(exchange_manager_inst, mark_price, symbol=DEFAULT_FUTURE_SYMBOL, side=None):
    symbol_position = exchange_manager_inst.exchange_personal_data.positions_manager. \
        get_symbol_position(symbol=symbol, side=side)
    await symbol_position.update(mark_price=mark_price)


async def test_initial_portfolio(future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager

    assert isinstance(portfolio_manager.portfolio, FuturePortfolio)


async def test_update_future_portfolio_from_order(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(2))

    # Test buy order
    market_buy = BuyMarketOrder(trader_inst)
    buy_price = decimal.Decimal(str(100))
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=buy_price,
                      quantity=decimal.Decimal(str(2)),
                      price=buy_price)

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(900))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").initial_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").wallet_balance == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == decimal.Decimal(str(100))

    # create a new position from order
    await fill_market_order(market_buy)

    # update position mark price
    await _update_position_mark_price(exchange_manager_inst, buy_price, DEFAULT_FUTURE_SYMBOL)

    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(900))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == 0
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").initial_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").wallet_balance == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == decimal.Decimal(str(100))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO


async def test_update_portfolio_available_from_order_with_market_buy_long_linear_contract(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(5))

    # Test buy order
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(str(1000)),
                      quantity=decimal.Decimal(str(2.5)),  # real quantity = 2.5 / 5 = 0.5 BTC at 1000$
                      price=decimal.Decimal(str(1000)))

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    # 1000 - 0.5 BTC * 1000$ = 500
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(500))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == decimal.Decimal(500)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == constants.ZERO

    # Test buy order
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(str(74)),
                      quantity=decimal.Decimal(str(5)),  # real quantity = 5 / 5 = 1 BTC at 74$
                      price=decimal.Decimal(str(74)))

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(1000)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == decimal.Decimal(574)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == constants.ZERO
    # 500 - 1 BTC * 74$ = 426
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(426))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == constants.ZERO

    # test cancel buy order
    portfolio_manager.portfolio.update_portfolio_available(market_buy, False)
    # 426 + 1 BTC * 74$ = 500
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(500))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == decimal.Decimal(str(500))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(10)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(str(10))


async def test_update_portfolio_available_from_order_with_market_buy_long_inverse_contract(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    symbol_contract = contracts.FutureContract(
        pair=DEFAULT_FUTURE_SYMBOL,
        margin_type=DEFAULT_FUTURE_SYMBOL_MARGIN_TYPE,
        contract_type=enums.FutureContractType.INVERSE_PERPETUAL,
        current_leverage=DEFAULT_FUTURE_SYMBOL_LEVERAGE)
    trader_inst.exchange_manager.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)

    # Test buy order
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(str(1000)),
                      quantity=decimal.Decimal(str(1000)),  # real quantity = 1000 / 1000 = 1 BTC at 1000$
                      price=decimal.Decimal(str(1000)))

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(str(9))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").position_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").order_margin == constants.ONE
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").unrealized_pnl == constants.ZERO

    # Test buy order
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(str(74)),
                      quantity=decimal.Decimal(str(74 / 3)),  # real quantity = 0.3 BTC at 74$
                      price=decimal.Decimal(str(74)))

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(10)
    # 9 - (74 / 3) / 74 = 8.666666666666666648648648649
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(
        '8.666666666666666648648648649')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").position_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").order_margin == decimal.Decimal(
        str('1.333333333333333351351351351'))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").unrealized_pnl == constants.ZERO

    # test cancel buy order
    portfolio_manager.portfolio.update_portfolio_available(market_buy, False)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(9)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").position_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").order_margin == decimal.Decimal(
        str('0.9999999999999999999999999996'))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").unrealized_pnl == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000))


async def test_update_portfolio_data_from_order_with_market_buy_long_linear_contract(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(5))

    # Test buy order
    market_buy = BuyMarketOrder(trader_inst)
    buy_price = decimal.Decimal(str(1000))
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=buy_price,
                      quantity=decimal.Decimal(3),  # real quantity = 3 / 5 = 0.6
                      price=buy_price)  # real cost = 0.6 * 1000 = 600

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)

    # create position from order
    await fill_market_order(market_buy)

    # update position mark price
    await _update_position_mark_price(exchange_manager_inst, buy_price, DEFAULT_FUTURE_SYMBOL)

    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(400.0))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000.0))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == decimal.Decimal(str(600.0))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == constants.ZERO

    # Test buy order
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=buy_price,
                      quantity=decimal.Decimal(1),  # 0.2
                      price=buy_price)  # 200

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    await fill_market_order(market_buy)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(200.0))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000.0))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == decimal.Decimal(str(800.0))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == constants.ZERO

    # Test reducing LONG position with a sell market order
    market_sell = SellMarketOrder(trader_inst)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=buy_price,
                       quantity=decimal.Decimal(0.5),  # 0.1
                       price=buy_price)  # 100

    # Should restore available
    portfolio_manager.portfolio.update_portfolio_available(market_sell, True)
    await fill_market_order(market_sell)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(10)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(300))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(10)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == decimal.Decimal(str(700.0))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == constants.ZERO

    # Test buy order 2
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=buy_price,
                      quantity=decimal.Decimal(0.5),  # 0.1
                      price=buy_price)  # 100

    # increase position size
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    await fill_market_order(market_buy)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(200))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == decimal.Decimal(str(800.0))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == constants.ZERO

    # Test reducing again LONG position with a sell market order
    market_sell = SellMarketOrder(trader_inst)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=buy_price,
                       quantity=decimal.Decimal(4),  # 0.8
                       price=buy_price)  # 800

    # decrease position size
    portfolio_manager.portfolio.update_portfolio_available(market_sell, True)
    await fill_market_order(market_sell)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(10)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(10)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == constants.ZERO


async def test_update_portfolio_data_from_order_that_triggers_negative_portfolio_linear_contract(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(5))

    # Test buy order
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(str(1000)),
                      quantity=decimal.Decimal(str(100000000)),
                      price=decimal.Decimal(str(1000)))

    # test buy order creation
    # if not os.getenv('CYTHON_IGNORE'):
    with pytest.raises(errors.PortfolioNegativeValueError):
        portfolio_manager.portfolio.update_portfolio_available(market_buy, True)


async def test_update_portfolio_data_from_order_with_cancelled_and_filled_orders_linear_contract(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(5))

    # Test sell order
    market_sell = SellMarketOrder(trader_inst)
    sell_price = decimal.Decimal(str(80))
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=sell_price,
                       quantity=decimal.Decimal(str(12)),
                       price=sell_price)

    # Test sell order
    limit_sell = SellLimitOrder(trader_inst)
    limit_sell.update(order_type=enums.TraderOrderType.SELL_LIMIT,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(str(10)),
                      quantity=decimal.Decimal(str(46.5)),
                      price=decimal.Decimal(str(10)))

    # Test stop loss order
    stop_loss = StopLossOrder(trader_inst)
    stop_loss.update(order_type=enums.TraderOrderType.STOP_LOSS,
                     symbol=DEFAULT_FUTURE_SYMBOL,
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

    await fill_market_order(market_sell)
    await _update_position_mark_price(exchange_manager_inst, sell_price, DEFAULT_FUTURE_SYMBOL)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('714.616')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('999.616')

    # cancel other orders
    portfolio_manager.portfolio.update_portfolio_available(stop_loss, False)
    portfolio_manager.portfolio.update_portfolio_available(limit_sell, False)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal('10')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('807.616')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal('10')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('999.616')


async def test_update_portfolio_data_from_orders_with_max_long_size_linear_contract(
        future_trader_simulator_with_default_linear):
    # TODO same test with fees in orders
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(2))

    # Test buy order
    market_buy = BuyMarketOrder(trader_inst)
    buy_order_price = decimal.Decimal(40)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=buy_order_price,
                      quantity=decimal.Decimal(50),
                      price=buy_order_price)

    # Test sell order
    market_sell = SellMarketOrder(trader_inst)
    sell_order_price = decimal.Decimal(80)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=sell_order_price,
                       quantity=decimal.Decimal(50),
                       price=sell_order_price)

    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == constants.ZERO

    if os.getenv('CYTHON_IGNORE'):
        return

    # Open long position
    # Mock fees because it's not possible to trade with money you don't have (full available + fees)
    # so we need to disable fees for this test
    with mock.patch.object(market_buy, "get_total_fees", mock.Mock(return_value=0)):
        await fill_market_order(market_buy)
    await _update_position_mark_price(exchange_manager_inst, sell_order_price, DEFAULT_FUTURE_SYMBOL)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == constants.ZERO

    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('3000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == decimal.Decimal('2000')

    portfolio_manager.portfolio.update_portfolio_available(market_sell, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('3000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == decimal.Decimal('2000')

    # Close long position with gains
    await fill_market_order(market_sell)
    await _update_position_mark_price(exchange_manager_inst, buy_order_price, DEFAULT_FUTURE_SYMBOL)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('3000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('3000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == constants.ZERO


async def test_update_portfolio_data_from_orders_with_max_short_size_linear_contract(
        future_trader_simulator_with_default_linear):
    # TODO same test with fees in orders
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(2))

    # Test buy order
    market_buy = BuyMarketOrder(trader_inst)
    buy_order_price = decimal.Decimal(50)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=buy_order_price,
                      quantity=decimal.Decimal(50),
                      price=buy_order_price)

    # Test sell order
    market_sell = SellMarketOrder(trader_inst)
    sell_order_price = decimal.Decimal(40)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=sell_order_price,
                       quantity=decimal.Decimal(50),
                       price=sell_order_price)

    portfolio_manager.portfolio.update_portfolio_available(market_sell, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == constants.ZERO

    if os.getenv('CYTHON_IGNORE'):
        return

    # Open long position
    # Mock fees because it's not possible to trade with money you don't have (full available + fees)
    # so we need to disable fees for this test
    with mock.patch.object(market_sell, "get_total_fees", mock.Mock(return_value=0)):
        await fill_market_order(market_sell)
    await _update_position_mark_price(exchange_manager_inst, buy_order_price, DEFAULT_FUTURE_SYMBOL)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('500')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == decimal.Decimal('-500')

    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('500')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == decimal.Decimal('-500')

    # Close long position with gains
    await fill_market_order(market_buy)
    await _update_position_mark_price(exchange_manager_inst, buy_order_price, DEFAULT_FUTURE_SYMBOL)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('500')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('500')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == constants.ZERO


async def test_update_portfolio_data_from_order_with_huge_loss_on_filled_orders_linear_contract(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(2))

    # Test sell order
    market_sell = SellMarketOrder(trader_inst)
    sell_order_price = decimal.Decimal(10)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=sell_order_price,
                       quantity=decimal.Decimal(25),
                       price=sell_order_price)

    # Test buy order
    market_buy = BuyMarketOrder(trader_inst)
    buy_order_price = decimal.Decimal(13)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=buy_order_price,
                      quantity=decimal.Decimal(10),
                      price=buy_order_price)

    closing_market_buy = BuyMarketOrder(trader_inst)
    closing_market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                              symbol=DEFAULT_FUTURE_SYMBOL,
                              current_price=buy_order_price,
                              quantity=decimal.Decimal(15),
                              price=buy_order_price)

    portfolio_manager.portfolio.update_portfolio_available(market_sell, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('875.0')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == decimal.Decimal('125')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == constants.ZERO

    # Open short position
    await fill_market_order(market_sell)
    await _update_position_mark_price(exchange_manager_inst, sell_order_price, DEFAULT_FUTURE_SYMBOL)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('874.9')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('999.9')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == decimal.Decimal('125')

    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('874.9')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('999.9')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == decimal.Decimal('125')

    # Close short position with loss
    await fill_market_order(market_buy)
    await _update_position_mark_price(exchange_manager_inst, buy_order_price, DEFAULT_FUTURE_SYMBOL)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('894.9')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('924.9')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == decimal.Decimal('75')

    # Close short position with loss
    await fill_market_order(closing_market_buy)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('924.9')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('924.9')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == constants.ZERO


async def test_update_portfolio_from_liquidated_position_with_orders_on_short_position_linear_contract(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(50))
    trader_inst.exchange_manager.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, default_contract)

    position_inst = LinearPosition(trader_inst, default_contract)
    await position_inst.initialize()
    position_inst.update_from_raw({enums.ExchangeConstantsPositionColumns.SYMBOL.value: DEFAULT_FUTURE_SYMBOL})
    await position_inst.update(update_size=decimal.Decimal(-100), mark_price=decimal.Decimal(99))
    exchange_manager_inst.exchange_personal_data.positions_manager.upsert_position_instance(position_inst)

    # Test sell order
    market_sell = SellMarketOrder(trader_inst)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=decimal.Decimal(99),
                       quantity=decimal.Decimal(5),
                       price=decimal.Decimal(99))

    # test sell order creation
    portfolio_manager.portfolio.update_portfolio_available(market_sell, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('792.1')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == decimal.Decimal('9.9')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == decimal.Decimal('198')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == constants.ZERO

    await fill_market_order(market_sell)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('791.902')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('999.802')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal('10')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal('10')

    # Test buy order
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(90),
                      quantity=decimal.Decimal(10),
                      price=decimal.Decimal(90))

    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('791.902')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == decimal.Decimal('207.9')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('999.802')

    await fill_market_order(market_buy)  # reducing position with positive PNL
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('901.702')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1944.802')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == decimal.Decimal('188.1')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == decimal.Decimal(str(855))

    portfolio_manager.portfolio.get_currency_portfolio("BTC").wallet_balance = decimal.Decimal('10')
    portfolio_manager.portfolio.get_currency_portfolio("USDT").wallet_balance = decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == decimal.Decimal(str(188.1))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == decimal.Decimal(str(855.0))

    await position_inst.update(mark_price=position_inst.liquidation_price)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('811.9')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('811.9')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal('10')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal('10')


async def test_update_portfolio_from_funding_with_long_position(
        future_trader_simulator_with_default_inverse):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_inverse
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(10))

    position_inst = InversePosition(trader_inst, default_contract)
    await position_inst.initialize()
    position_inst.update_from_raw({enums.ExchangeConstantsPositionColumns.SYMBOL.value: DEFAULT_FUTURE_SYMBOL})
    await position_inst.update(update_size=decimal.Decimal(10), mark_price=decimal.Decimal(100))
    exchange_manager_inst.exchange_personal_data.positions_manager.upsert_position_instance(position_inst)

    # long position holders have to pay the short position holders
    portfolio_manager.portfolio.update_portfolio_from_funding(position=position_inst,
                                                              funding_rate=decimal.Decimal(0.0001))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(
        '9.989989999999999999999520783')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(
        '9.999989999999999999999520783')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").position_margin == decimal.Decimal('0.01')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").unrealized_pnl == constants.ZERO

    position_inst = InversePosition(trader_inst, default_contract)
    await position_inst.initialize()
    position_inst.update_from_raw({enums.ExchangeConstantsPositionColumns.SYMBOL.value: DEFAULT_FUTURE_SYMBOL})
    await position_inst.update(update_size=decimal.Decimal(10), mark_price=decimal.Decimal(100))
    exchange_manager_inst.exchange_personal_data.positions_manager.upsert_position_instance(position_inst)

    # short position holders have to pay the long position holders
    portfolio_manager.portfolio.update_portfolio_from_funding(position=position_inst,
                                                              funding_rate=decimal.Decimal(-0.0002))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(
        '9.98001000000000000000047922')  # = previous available + funding - position increased size
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(
        '10.00001000000000000000047922')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").position_margin == decimal.Decimal('0.02')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").unrealized_pnl == constants.ZERO

    # should raise PortfolioNegativeValueError when funding fee > available
    with pytest.raises(errors.PortfolioNegativeValueError):
        portfolio_manager.portfolio.update_portfolio_from_funding(position=position_inst,
                                                                  funding_rate=decimal.Decimal(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(
        '9.98001000000000000000047922')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(
        '10.00001000000000000000047922')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").position_margin == decimal.Decimal('0.02')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").unrealized_pnl == constants.ZERO


async def test_update_portfolio_from_funding_with_short_position(
        future_trader_simulator_with_default_inverse):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_inverse
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(10))

    position_inst = InversePosition(trader_inst, default_contract)
    await position_inst.initialize()
    position_inst.update_from_raw({enums.ExchangeConstantsPositionColumns.SYMBOL.value: DEFAULT_FUTURE_SYMBOL})
    await position_inst.update(update_size=decimal.Decimal(-10), mark_price=decimal.Decimal(100))
    exchange_manager_inst.exchange_personal_data.positions_manager.upsert_position_instance(position_inst)

    # long position holders have to pay the short position holders
    portfolio_manager.portfolio.update_portfolio_from_funding(position=position_inst,
                                                              funding_rate=decimal.Decimal(0.0003))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(
        '9.99002999999999999999737189')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(
        '10.00002999999999999999737189')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").position_margin == decimal.Decimal(str(0.01))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").unrealized_pnl == constants.ZERO

    position_inst = InversePosition(trader_inst, default_contract)
    await position_inst.initialize()
    position_inst.update_from_raw({enums.ExchangeConstantsPositionColumns.SYMBOL.value: DEFAULT_FUTURE_SYMBOL})
    await position_inst.update(update_size=decimal.Decimal(-10), mark_price=decimal.Decimal(100))
    exchange_manager_inst.exchange_personal_data.positions_manager.upsert_position_instance(position_inst)

    # short position holders have to pay the long position holders
    portfolio_manager.portfolio.update_portfolio_from_funding(position=position_inst,
                                                              funding_rate=decimal.Decimal(-0.0004))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(
        '9.979989999999999999995455021')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(
        '9.999989999999999999995455021')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").position_margin == decimal.Decimal('0.02')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").unrealized_pnl == constants.ZERO

    # should raise PortfolioNegativeValueError when funding fee > available
    with pytest.raises(errors.PortfolioNegativeValueError):
        portfolio_manager.portfolio.update_portfolio_from_funding(position=position_inst,
                                                                  funding_rate=decimal.Decimal(-2378))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(
        '9.979989999999999999995455021')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(
        '9.999989999999999999995455021')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").position_margin == decimal.Decimal('0.02')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").unrealized_pnl == constants.ZERO


async def test_update_portfolio_data_with_fees(future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(10))

    # Test sell order
    market_sell = SellMarketOrder(trader_inst)
    sell_order_price = decimal.Decimal(10)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=sell_order_price,
                       quantity=decimal.Decimal(25),
                       price=sell_order_price)

    if not os.getenv('CYTHON_IGNORE'):
        with mock.patch.object(market_sell, "get_total_fees", mock.Mock(return_value=5)):
            portfolio_manager.portfolio.update_portfolio_available(market_sell, True)
            assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('975.0')
            assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')
            assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == decimal.Decimal('25')
            assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == constants.ZERO
            assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == constants.ZERO

            # fill order with fees
            await fill_market_order(market_sell)
            await _update_position_mark_price(exchange_manager_inst, sell_order_price, DEFAULT_FUTURE_SYMBOL)
            assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('970.0')
            assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('995')
            assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
            assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == decimal.Decimal('25')
            assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == constants.ZERO


async def test_update_portfolio_reduce_size_with_market_sell_long_linear_contract(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(10))

    position_inst = LinearPosition(trader_inst, default_contract)
    await position_inst.initialize()
    position_inst.update_from_raw({enums.ExchangeConstantsPositionColumns.SYMBOL.value: DEFAULT_FUTURE_SYMBOL})
    await position_inst.update(update_size=decimal.Decimal(10), mark_price=decimal.Decimal(101))
    exchange_manager_inst.exchange_personal_data.positions_manager.upsert_position_instance(position_inst)

    # Test sell order
    market_sell = SellMarketOrder(trader_inst)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=decimal.Decimal(101),
                       quantity=decimal.Decimal(25),
                       price=decimal.Decimal(101))

    # test sell order creation
    portfolio_manager.portfolio.update_portfolio_available(market_sell, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(899))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(str(10))

    # fill order
    await fill_market_order(market_sell)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal("1000")
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str("848.5"))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == decimal.Decimal(str(151.5))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(str(10))


async def test_update_portfolio_reduce_size_with_market_buy_short_linear_contract(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(10))

    position_inst = LinearPosition(trader_inst, default_contract)
    await position_inst.initialize()
    position_inst.update_from_raw({enums.ExchangeConstantsPositionColumns.SYMBOL.value: DEFAULT_FUTURE_SYMBOL})
    await position_inst.update(update_size=constants.ZERO, mark_price=decimal.Decimal(10))
    exchange_manager_inst.exchange_personal_data.positions_manager.upsert_position_instance(position_inst)

    # initialize short
    market_sell = SellMarketOrder(trader_inst)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=decimal.Decimal(10),
                       quantity=decimal.Decimal(70),
                       price=decimal.Decimal(10))
    portfolio_manager.portfolio.update_portfolio_available(market_sell, True)
    await fill_market_order(market_sell)

    # Test reducing buy order
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(10),
                      quantity=decimal.Decimal(20),
                      price=decimal.Decimal(10))

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    # 1000 - 70 - fees
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('929.72')
    # 1000 - fees
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('999.72')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == decimal.Decimal('70')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(str(10))

    # fill order
    await fill_market_order(market_buy)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('999.72')
    # 1000 - 70 - fees + 20
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('949.72')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == decimal.Decimal('50')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(str(10))


async def test_update_portfolio_from_pnl_with_long_inverse_contract(future_trader_simulator_with_default_inverse):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_inverse
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(10))

    position_inst = InversePosition(trader_inst, default_contract)
    await position_inst.initialize()
    position_inst.update_from_raw({enums.ExchangeConstantsPositionColumns.SYMBOL.value: DEFAULT_FUTURE_SYMBOL})
    await position_inst.update(update_size=decimal.Decimal(-70), mark_price=decimal.Decimal(10))
    exchange_manager_inst.exchange_personal_data.positions_manager.upsert_position_instance(position_inst)

    position_inst.unrealized_pnl = decimal.Decimal(0.1)
    portfolio_manager.portfolio.update_portfolio_from_pnl(position_inst)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(str(9.3))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(str('10.0'))

    position_inst.unrealized_pnl = decimal.Decimal(-0.3)
    portfolio_manager.portfolio.update_portfolio_from_pnl(position_inst)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(str(9.3))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(str('10'))
