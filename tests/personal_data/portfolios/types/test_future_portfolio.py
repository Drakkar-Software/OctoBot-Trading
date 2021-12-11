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
    symbol_position.update(mark_price=mark_price)


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

    # update position mark price
    await _update_position_mark_price(exchange_manager_inst, buy_price, DEFAULT_FUTURE_SYMBOL)

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(900))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").initial_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").wallet_balance == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").order_margin == decimal.Decimal(str(100))

    await fill_market_order(market_buy)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(900))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(900))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").unrealized_pnl == -constants.ONE_HUNDRED
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

    # test cancel buy order
    portfolio_manager.portfolio.update_portfolio_available(market_buy, False)
    # 426 + 1 BTC * 74$ = 500
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(500))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000))
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

    # test cancel buy order
    portfolio_manager.portfolio.update_portfolio_available(market_buy, False)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(9)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(str(10))
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
                      quantity=decimal.Decimal(str(3)),  # real quantity = 3 / 5 = 0.6
                      price=buy_price)

    # update position mark price
    await _update_position_mark_price(exchange_manager_inst, buy_price, DEFAULT_FUTURE_SYMBOL)

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    await fill_market_order(market_buy)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(400.0))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(400.0))

    # Test buy order
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(str(7.5)),
                      quantity=decimal.Decimal(str(30)),
                      price=decimal.Decimal(str(7.5)))

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    await fill_market_order(market_buy)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(355.0))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(355.0))

    # Test reducing LONG position with a sell market order
    market_sell = SellMarketOrder(trader_inst)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=decimal.Decimal(str(54)),
                       quantity=decimal.Decimal(str(20)),
                       price=decimal.Decimal(str(54)))

    # Should restore to first test step asserts
    portfolio_manager.portfolio.update_portfolio_available(market_sell, True)
    await fill_market_order(market_sell)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(10)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(354.568))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(10)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str('570.568'))


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
    if not os.getenv('CYTHON_IGNORE'):
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

    # update position mark price
    await _update_position_mark_price(exchange_manager_inst, sell_price, DEFAULT_FUTURE_SYMBOL)

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
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('714.616')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1191.616')

    # cancel other orders
    portfolio_manager.portfolio.update_portfolio_available(stop_loss, False)
    portfolio_manager.portfolio.update_portfolio_available(limit_sell, False)
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal('10')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('807.616')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal('10')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1191.616')


async def test_update_portfolio_data_from_order_with_huge_loss_on_filled_orders_linear_contract(
        future_trader_simulator_with_default_linear):
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

    # Test buy order
    market_buy = BuyMarketOrder(trader_inst)
    buy_order_price = decimal.Decimal(13)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=buy_order_price,
                      quantity=decimal.Decimal(10),
                      price=buy_order_price)

    portfolio_manager.portfolio.update_portfolio_available(market_sell, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('975.0')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')

    # update position mark price
    await _update_position_mark_price(exchange_manager_inst, sell_order_price, DEFAULT_FUTURE_SYMBOL)

    # Open short position
    await fill_market_order(market_sell)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('974.9')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1024.9')

    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    # => 975 - 250 = 725
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('961.9')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1024.9')

    # update position mark price
    await _update_position_mark_price(exchange_manager_inst, buy_order_price, DEFAULT_FUTURE_SYMBOL)

    # Close short position with loss
    await fill_market_order(market_buy)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('974.9')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1011.9')


async def test_update_portfolio_from_liquidated_position_with_long_position_inverse_contract(
        future_trader_simulator_with_default_inverse):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_inverse
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(10))

    position_inst = LinearPosition(trader_inst, default_contract)
    position_inst.update_from_raw(
        {
            enums.ExchangeConstantsPositionColumns.SYMBOL.value: DEFAULT_FUTURE_SYMBOL
        }
    )
    await position_inst.update(update_size=decimal.Decimal(10), mark_price=decimal.Decimal(100))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal('10')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal('10')

    portfolio_manager.portfolio.update_portfolio_from_liquidated_position(position_inst)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal('9.99')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal('9.99')


async def test_update_portfolio_from_liquidated_position_with_short_position_inverse_contract(
        future_trader_simulator_with_default_inverse):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_inverse
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(50))
    trader_inst.exchange_manager.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, default_contract)

    position_inst = InversePosition(trader_inst, default_contract)
    position_inst.update_from_raw(
        {
            enums.ExchangeConstantsPositionColumns.SYMBOL.value: DEFAULT_FUTURE_SYMBOL
        }
    )
    await position_inst.update(update_size=decimal.Decimal(-10000), mark_price=decimal.Decimal(100))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal('10')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal('10')

    portfolio_manager.portfolio.get_currency_portfolio("BTC").position_margin = decimal.Decimal('100')
    portfolio_manager.portfolio.get_currency_portfolio("BTC").wallet_balance = decimal.Decimal('10000')
    portfolio_manager.portfolio.update_portfolio_from_liquidated_position(position_inst)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").position_margin == constants.ZERO
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").wallet_balance == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal('9900')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal('9998')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").position_margin == decimal.Decimal('98')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").wallet_balance == decimal.Decimal('9998')


async def test_update_portfolio_from_liquidated_position_with_orders_on_short_position_linear_contract(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(50))
    trader_inst.exchange_manager.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, default_contract)

    position_inst = LinearPosition(trader_inst, default_contract)
    position_inst.update_from_raw(
        {
            enums.ExchangeConstantsPositionColumns.SYMBOL.value: DEFAULT_FUTURE_SYMBOL
        }
    )
    await position_inst.update(update_size=decimal.Decimal(-100), mark_price=decimal.Decimal(99))

    # Test sell order
    market_sell = SellMarketOrder(trader_inst)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=decimal.Decimal(99),
                       quantity=decimal.Decimal(5),
                       price=decimal.Decimal(99))

    # test sell order creation
    portfolio_manager.portfolio.update_portfolio_available(market_sell, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('990.1')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal('10')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal('10')

    await fill_market_order(market_sell)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('989.902')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1009.702')
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
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('971.902')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1009.702')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal('10')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal('10')

    await fill_market_order(market_buy)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('989.902')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('991.702')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal('10')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal('10')

    portfolio_manager.portfolio.get_currency_portfolio("BTC").wallet_balance = decimal.Decimal('10')
    portfolio_manager.portfolio.get_currency_portfolio("USDT").wallet_balance = decimal.Decimal('1000')
    await position_inst.update(mark_price=decimal.Decimal(126))
    portfolio_manager.portfolio.update_portfolio_from_liquidated_position(position_inst)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('748')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('694')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal('10')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal('10')


async def test_update_portfolio_from_funding_with_long_position(
        future_trader_simulator_with_default_inverse):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_inverse
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(10))

    position_inst = InversePosition(trader_inst, default_contract)
    await position_inst.update(update_size=decimal.Decimal(10), mark_price=decimal.Decimal(100))
    position_inst.update_from_raw(
        {
            enums.ExchangeConstantsPositionColumns.SYMBOL.value: DEFAULT_FUTURE_SYMBOL
        }
    )
    # long position holders have to pay the short position holders
    portfolio_manager.portfolio.update_portfolio_from_funding(position=position_inst,
                                                              funding_rate=decimal.Decimal(0.0001))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(
        '9.999998999999999999999952078')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(
        '9.999998999999999999999952078')

    position_inst = InversePosition(trader_inst, default_contract)
    await position_inst.update(update_size=decimal.Decimal(10), mark_price=decimal.Decimal(100))
    position_inst.update_from_raw(
        {
            enums.ExchangeConstantsPositionColumns.SYMBOL.value: DEFAULT_FUTURE_SYMBOL
        }
    )
    # short position holders have to pay the long position holders
    portfolio_manager.portfolio.update_portfolio_from_funding(position=position_inst,
                                                              funding_rate=decimal.Decimal(-0.0002))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(
        '10.00000100000000000000004792')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(
        '10.00000100000000000000004792')


async def test_update_portfolio_from_funding_with_short_position(
        future_trader_simulator_with_default_inverse):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_inverse
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(10))

    position_inst = InversePosition(trader_inst, default_contract)
    await position_inst.update(update_size=decimal.Decimal(-10), mark_price=decimal.Decimal(100))
    position_inst.update_from_raw(
        {
            enums.ExchangeConstantsPositionColumns.SYMBOL.value: DEFAULT_FUTURE_SYMBOL
        }
    )
    # long position holders have to pay the short position holders
    portfolio_manager.portfolio.update_portfolio_from_funding(position=position_inst,
                                                              funding_rate=decimal.Decimal(0.0003))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(
        '10.00000299999999999999973719')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(
        '10.00000299999999999999973719')

    position_inst = InversePosition(trader_inst, default_contract)
    await position_inst.update(update_size=decimal.Decimal(-10), mark_price=decimal.Decimal(100))
    position_inst.update_from_raw(
        {
            enums.ExchangeConstantsPositionColumns.SYMBOL.value: DEFAULT_FUTURE_SYMBOL
        }
    )
    # short position holders have to pay the long position holders
    portfolio_manager.portfolio.update_portfolio_from_funding(position=position_inst,
                                                              funding_rate=decimal.Decimal(-0.0004))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(
        '9.999998999999999999999545503')
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(
        '9.999998999999999999999545503')


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

    # update position mark price
    await _update_position_mark_price(exchange_manager_inst, sell_order_price, DEFAULT_FUTURE_SYMBOL)

    if not os.getenv('CYTHON_IGNORE'):
        with mock.patch.object(market_sell, "get_total_fees", mock.Mock(return_value=5)):
            portfolio_manager.portfolio.update_portfolio_available(market_sell, True)
            assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('975.0')
            assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1000')

            # fill order with fees
            await fill_market_order(market_sell)
            assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal('970.0')
            assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal('1020')


async def test_update_portfolio_reduce_size_with_market_sell_long_linear_contract(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(10))

    position_inst = LinearPosition(trader_inst, default_contract)
    await position_inst.update(update_size=decimal.Decimal(10), mark_price=decimal.Decimal(101))
    position_inst.update_from_raw(
        {
            enums.ExchangeConstantsPositionColumns.SYMBOL.value: DEFAULT_FUTURE_SYMBOL
        }
    )

    # Test sell order
    market_sell = SellMarketOrder(trader_inst)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=decimal.Decimal(101),
                       quantity=decimal.Decimal(25),
                       price=decimal.Decimal(101))

    # test sell order creation
    portfolio_manager.portfolio.update_portfolio_available(market_sell, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(747.5))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(str(10))

    # fill order
    await fill_market_order(market_sell)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal("1251.49")
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str("746.49"))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(str(10))


async def test_update_portfolio_reduce_size_with_market_buy_short_linear_contract(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(10))

    position_inst = LinearPosition(trader_inst, default_contract)
    position_inst.update(update_size=decimal.Decimal(-70), mark_price=decimal.Decimal(9))
    position_inst.update_from_raw(
        {
            enums.ExchangeConstantsPositionColumns.SYMBOL.value: DEFAULT_FUTURE_SYMBOL
        }
    )

    # Test buy order
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(9),
                      quantity=decimal.Decimal(10),
                      price=decimal.Decimal(9))

    # test buy order creation
    portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(991))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(str(10))

    # fill order
    await fill_market_order(market_buy)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(991)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(991))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(str(10))


async def test_update_portfolio_from_pnl_with_long_inverse_contract(future_trader_simulator_with_default_inverse):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_inverse
    portfolio_manager = exchange_manager_inst.exchange_personal_data.portfolio_manager
    default_contract.set_current_leverage(decimal.Decimal(10))

    position_inst = InversePosition(trader_inst, default_contract)
    position_inst.update(update_size=decimal.Decimal(-70), mark_price=decimal.Decimal(10))
    position_inst.update_from_raw(
        {
            enums.ExchangeConstantsPositionColumns.SYMBOL.value: DEFAULT_FUTURE_SYMBOL
        }
    )

    position_inst.unrealised_pnl = decimal.Decimal(0.1)
    portfolio_manager.portfolio.update_portfolio_from_pnl(position_inst)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(
        str('10.10000000000000000555111512'))

    position_inst.unrealised_pnl = decimal.Decimal(-0.3)
    portfolio_manager.portfolio.update_portfolio_from_pnl(position_inst)
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").available == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("USDT").total == decimal.Decimal(str(1000))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").available == decimal.Decimal(str(10))
    assert portfolio_manager.portfolio.get_currency_portfolio("BTC").total == decimal.Decimal(
        str('9.700000000000000011102230246'))
