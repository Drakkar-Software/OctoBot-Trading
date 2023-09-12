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

from mock import Mock, AsyncMock
import pytest

import octobot_trading.api as api
import octobot_trading.enums as enums
import octobot_trading.constants as constants
import octobot_trading.personal_data as personal_data

from tests import event_loop
from tests.exchanges import future_simulated_exchange_manager, simulated_exchange_manager, set_future_exchange_fees
from tests.exchanges.traders import future_trader_simulator_with_default_linear, \
    future_trader_simulator_with_default_inverse, DEFAULT_FUTURE_SYMBOL, DEFAULT_FUTURE_FUNDING_RATE, trader_simulator


def test_get_min_max_amounts():
    # normal values
    symbol_market = {
        enums.ExchangeConstantsMarketStatusColumns.LIMITS.value: {
            enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT_MIN.value: 0.5,
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT_MAX.value: 100,
            },
            enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST_MIN.value: None,
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST_MAX.value: None
            },
            enums.ExchangeConstantsMarketStatusColumns.LIMITS_PRICE.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_PRICE_MIN.value: 0.5,
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_PRICE_MAX.value: 50
            },
        }
    }
    min_quantity, max_quantity, min_cost, max_cost, min_price, max_price = personal_data.get_min_max_amounts(
        symbol_market)
    assert min_quantity == 0.5
    assert max_quantity == 100
    assert min_cost is None
    assert max_cost is None
    assert min_price == 0.5
    assert max_price == 50

    # missing all values
    min_quantity, max_quantity, min_cost, max_cost, min_price, max_price = personal_data.get_min_max_amounts({})
    assert min_quantity is None
    assert max_quantity is None
    assert min_cost is None
    assert max_cost is None
    assert min_price is None
    assert max_price is None

    # missing all values: asign default
    min_quantity, max_quantity, min_cost, max_cost, min_price, max_price = personal_data.get_min_max_amounts({}, "xyz")
    assert min_quantity == "xyz"
    assert max_quantity == "xyz"
    assert min_cost == "xyz"
    assert max_cost == "xyz"
    assert min_price == "xyz"
    assert max_price == "xyz"

    # missing values: assign default

    symbol_market = {
        enums.ExchangeConstantsMarketStatusColumns.LIMITS.value: {
            enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT_MIN.value: 0.5,
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT_MAX.value: 100,
            },
            enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST_MIN.value: None,
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST_MAX.value: None
            }
        }
    }
    min_quantity, max_quantity, min_cost, max_cost, min_price, max_price = personal_data.get_min_max_amounts(symbol_market, "xyz")
    assert min_quantity == 0.5
    assert max_quantity == 100
    assert min_cost == "xyz"  # None is not a valid value => assign default
    assert max_cost == "xyz"  # None is not a valid value => assign default
    assert min_price == "xyz"
    assert max_price == "xyz"


def test_get_fees_for_currency():
    fee1 = {
        enums.FeePropertyColumns.CURRENCY.value: "BTC",
        enums.FeePropertyColumns.COST.value: 1
    }
    assert personal_data.get_fees_for_currency(fee1, "BTC") == 1
    assert personal_data.get_fees_for_currency(fee1, "BTC1") == 0

    fee2 = {
        enums.FeePropertyColumns.CURRENCY.value: "BTC",
        enums.FeePropertyColumns.COST.value: 0,
        enums.FeePropertyColumns.IS_FROM_EXCHANGE.value: True
    }
    assert personal_data.get_fees_for_currency(fee2, "BTC") == 0
    assert personal_data.get_fees_for_currency(fee2, "BTC1") == 0

    assert personal_data.get_fees_for_currency({}, "BTC") == 0
    assert personal_data.get_fees_for_currency(None, "BTC") == 0


def test_get_max_order_quantity_for_price_long_linear(future_trader_simulator_with_default_linear):
    # values also tested with bybit fees
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    set_future_exchange_fees(exchange_manager_inst.exchange.connector, default_contract.pair)

    # no need to initialize the position
    default_contract.set_current_leverage(constants.ONE)
    # at price = 37000 and 9961.7672 USDT in stock, if there were no fees,
    # max quantity would be 9961.7672 / 37000 = 0.269236951351,
    # it is actually less to allow fees
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.LinearPosition(trader_inst, default_contract),
        decimal.Decimal("9961.7672"), decimal.Decimal("37000"), enums.PositionSide.LONG, DEFAULT_FUTURE_SYMBOL
    ) == decimal.Decimal('0.2691292996314987518506111069')

    default_contract.set_current_leverage(decimal.Decimal("2"))
    # at price = 37000 and 9961.7672 USDT in stock, if there were no fees,
    # max quantity would be 9961.7672 / 37000 * 2 = 0.538473902703,
    # it is actually less to allow fees
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.LinearPosition(trader_inst, default_contract),
        decimal.Decimal("9961.7672"), decimal.Decimal("37000"), enums.PositionSide.LONG, DEFAULT_FUTURE_SYMBOL
    ) == decimal.Decimal('0.5378285084925116886762911533')

    default_contract.set_current_leverage(decimal.Decimal("10"))
    # at price = 43500 and 9943.9078 USDT in stock, if there were no fees,
    # max quantity would be 9943.9078 / 43500 * 10 = 2.26311218138,
    # it is actually less to allow fees
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.LinearPosition(trader_inst, default_contract),
        decimal.Decimal("9943.9078"), decimal.Decimal("43500"), enums.PositionSide.LONG, DEFAULT_FUTURE_SYMBOL
    ) == decimal.Decimal('2.268713592786774536511021980')

    # example from bybit docs
    # Trader place a long entry of 1BTC at USD8000 with 50x leverage.
    # Order Cost = 160USDT + 6USDT + 5.88USDT = 171.88 USDT
    default_contract.set_current_leverage(decimal.Decimal("50"))
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.LinearPosition(trader_inst, default_contract),
        decimal.Decimal("171.88"), decimal.Decimal("8000"), enums.PositionSide.LONG, DEFAULT_FUTURE_SYMBOL
    ) == decimal.Decimal('1.033330126971912273951519815')
    # Here the max size is a bit higher than 1 since binance fees are a bit higher

    default_contract.set_current_leverage(constants.ONE_HUNDRED)
    # at price = 43500 and 9943.9078 USDT in stock, if there were no fees,
    # max quantity would be 9943.9078 / 43500 * 100 = 22.6311218138,
    # it is actually less to allow fees (which are huge on 100x)
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.LinearPosition(trader_inst, default_contract),
        decimal.Decimal("9943.9078"), decimal.Decimal("43500"), enums.PositionSide.LONG, DEFAULT_FUTURE_SYMBOL
    ) == decimal.Decimal('21.17409981559794389578089799')


def test_get_max_order_quantity_for_price_short_linear(future_trader_simulator_with_default_linear):
    # values also tested with bybit fees
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    set_future_exchange_fees(exchange_manager_inst.exchange.connector, default_contract.pair)

    # no need to initialize the position
    # Differs from long due to the position closing fees at liquidation price which are higher (price is higher)
    # Therefore to open the same position size, more funds are required than for longs
    # (max quantity is lower than for longs)
    default_contract.set_current_leverage(constants.ONE)
    # at price = 37000 and 9961.7672 USDT in stock, if there were no fees,
    # max quantity would be 9961.7672 / 37000 = 0.269236951351,
    # it is actually less to allow fees
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.LinearPosition(trader_inst, default_contract),
        decimal.Decimal("9961.7672"), decimal.Decimal("37000"), enums.PositionSide.SHORT, DEFAULT_FUTURE_SYMBOL
    ) == decimal.Decimal('0.2689142542462558443381455767')

    default_contract.set_current_leverage(decimal.Decimal("2"))
    # at price = 37000 and 9961.7672 USDT in stock, if there were no fees,
    # max quantity would be 9961.7672 / 37000 * 2 = 0.538473902703,
    # it is actually less to allow fees
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.LinearPosition(trader_inst, default_contract),
        decimal.Decimal("9961.7672"), decimal.Decimal("37000"), enums.PositionSide.SHORT, DEFAULT_FUTURE_SYMBOL
    ) == decimal.Decimal('0.5373991044937152721583859308')

    default_contract.set_current_leverage(decimal.Decimal("50"))
    # at price = 44500 and 9943.9078 USDT in stock, if there were no fees,
    # max quantity would be 9943.9078 / 44500 * 50 = 11.1729301124,
    # it is actually less to allow fees
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.LinearPosition(trader_inst, default_contract),
        decimal.Decimal("9943.9078"), decimal.Decimal("44500"), enums.PositionSide.SHORT, DEFAULT_FUTURE_SYMBOL
    ) == decimal.Decimal('10.73907161895381638004397617')

    default_contract.set_current_leverage(constants.ONE_HUNDRED)
    # at price = 37000 and 9961.7672 USDT in stock, if there were no fees,
    # max quantity would be 9961.7672 / 37000 * 100 = 26.9236951351,
    # it is actually less to allow fees (which are huge on 100x)
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.LinearPosition(trader_inst, default_contract),
        decimal.Decimal("9961.7672"), decimal.Decimal("37000"), enums.PositionSide.SHORT, DEFAULT_FUTURE_SYMBOL
    ) == decimal.Decimal('24.92011767413470486406436055')


def test_get_max_order_quantity_for_price_long_inverse(future_trader_simulator_with_default_inverse):
    # values also tested with bybit fees
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_inverse
    set_future_exchange_fees(exchange_manager_inst.exchange.connector, default_contract.pair)

    # no need to initialize the position
    default_contract.set_current_leverage(constants.ONE)
    # at price = 36000 and 1 btc in stock, if there were no fees,
    # max quantity would be 1 * 36000 = 36000,
    # it is actually less to allow fees
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.InversePosition(trader_inst, default_contract),
        constants.ONE, decimal.Decimal("36000"), enums.PositionSide.LONG, DEFAULT_FUTURE_SYMBOL
    ) == decimal.Decimal('35956.85177786656012784658410')

    default_contract.set_current_leverage(decimal.Decimal("2"))
    # at price = 36000 and 1 btc in stock, if there were no fees,
    # max quantity would be 1 * 36000 * 2 = 72000,
    # it is actually less to allow fees
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.InversePosition(trader_inst, default_contract),
        constants.ONE, decimal.Decimal("36000"), enums.PositionSide.LONG, DEFAULT_FUTURE_SYMBOL
    ) == decimal.Decimal('71856.28742514970059880239519')

    default_contract.set_current_leverage(decimal.Decimal("25"))
    # example from bybit docs
    # Trader places a buy limit order of 10,000 BTCUSD contracts at 6,400 USD, using 25x leverage.
    # Order Cost = 0.0625 BTC (Initial margin) + 0.00117188 BTC (fee to open) + 0.00121872 BTC (fee to close) = 0.06489060 BTC
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.InversePosition(trader_inst, default_contract),
        decimal.Decimal("0.06489060"), decimal.Decimal("6400"), enums.PositionSide.LONG, DEFAULT_FUTURE_SYMBOL
    ) == decimal.Decimal('10174.92747941983535868286946')
    # higher than the 10000 from bybit example as binance fees are lower

    default_contract.set_current_leverage(constants.ONE_HUNDRED)
    # at price = 36000 and 1 btc in stock, if there were no fees,
    # max quantity would be 1 * 36000 * 100 = 3600000,
    # it is actually less to allow fees (which are huge on 100x)
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.InversePosition(trader_inst, default_contract),
        constants.ONE, decimal.Decimal("36000"), enums.PositionSide.LONG, DEFAULT_FUTURE_SYMBOL
    ) == decimal.Decimal('3332099.222510181414291003332')


def test_get_max_order_quantity_for_price_short_inverse(future_trader_simulator_with_default_inverse):
    # values also tested with bybit fees
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_inverse
    set_future_exchange_fees(exchange_manager_inst.exchange.connector, default_contract.pair)

    # no need to initialize the position
    # Differs from long due to the position closing fees at liquidation price which are higher (price is higher)
    # Therefore to open the same position size, less funds are required than for longs
    # (max quantity is higher than for longs)
    default_contract.set_current_leverage(constants.ONE)
    # at price = 36000 and 1 btc in stock, if there were no fees,
    # max quantity would be 1 * 36000 = 36000,
    # it is actually less to allow fees
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.InversePosition(trader_inst, default_contract),
        constants.ONE, decimal.Decimal("36000"), enums.PositionSide.SHORT, DEFAULT_FUTURE_SYMBOL
    ) == decimal.Decimal('35985.60575769692123150739704')

    default_contract.set_current_leverage(decimal.Decimal("2"))
    # at price = 36000 and 1 btc in stock, if there were no fees,
    # max quantity would be 1 * 36000 * 2 = 72000,
    # it is actually less to allow fees
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.InversePosition(trader_inst, default_contract),
        constants.ONE, decimal.Decimal("36000"), enums.PositionSide.SHORT, DEFAULT_FUTURE_SYMBOL
    ) == decimal.Decimal('71913.70355573312025569316820')

    default_contract.set_current_leverage(constants.ONE_HUNDRED)
    # at price = 36000 and 1 btc in stock, if there were no fees,
    # max quantity would be 1 * 36000 * 100 = 3600000,
    # it is actually less to allow fees (which are huge on 100x)
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.InversePosition(trader_inst, default_contract),
        constants.ONE, decimal.Decimal("36000"), enums.PositionSide.SHORT, DEFAULT_FUTURE_SYMBOL
    ) == decimal.Decimal('3334568.358651352352723230826')


@pytest.mark.asyncio
async def test_get_futures_max_order_size(future_trader_simulator_with_default_linear):
    # values also tested with bybit fees
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    set_future_exchange_fees(exchange_manager_inst.exchange.connector, default_contract.pair)

    symbol = default_contract.pair
    api.force_set_mark_price(exchange_manager_inst, symbol, 37000)
    compare_accuracy = decimal.Decimal("1.000000")

    default_contract.set_current_leverage(constants.ONE)
    l1_current_symbol_holding, _, l1_market_quantity, _, _ = \
        await personal_data.get_pre_order_data(exchange_manager_inst, symbol=symbol)
    assert personal_data.get_futures_max_order_size(
        exchange_manager_inst, symbol, enums.TradeOrderSide.BUY,
        decimal.Decimal("37000"), False, l1_current_symbol_holding, l1_market_quantity
    ) == (decimal.Decimal('0.02701622053881150242605660439'), True)

    # take leverage into account
    default_contract.set_current_leverage(decimal.Decimal(5))
    l2_current_symbol_holding, _, l2_market_quantity, _, _ = \
        await personal_data.get_pre_order_data(exchange_manager_inst, symbol=symbol)
    assert l2_current_symbol_holding.quantize(compare_accuracy) == \
           (l1_current_symbol_holding * default_contract.current_leverage).quantize(compare_accuracy)
    assert l2_market_quantity.quantize(compare_accuracy) == \
           (l1_market_quantity * default_contract.current_leverage).quantize(compare_accuracy)
    assert personal_data.get_futures_max_order_size(
        exchange_manager_inst, symbol, enums.TradeOrderSide.BUY,
        decimal.Decimal("37000"), False, l2_current_symbol_holding, l2_market_quantity
    ) == (decimal.Decimal('0.1346503937177512307045985802'), True)

    # with short position
    assert personal_data.get_futures_max_order_size(
        exchange_manager_inst, symbol, enums.TradeOrderSide.SELL,
        decimal.Decimal("37000"), False, l2_current_symbol_holding, l2_market_quantity
    ) == (decimal.Decimal('0.1345431452958334678764786291'), True)


@pytest.mark.asyncio
async def test_create_as_chained_order_regular_order(trader_simulator):
    config, exchange_manager_inst, trader_inst = trader_simulator

    base_order = personal_data.BuyLimitOrder(trader_inst)
    base_order.update(order_type=enums.TraderOrderType.BUY_LIMIT,
                      symbol="BTC/USDT",
                      current_price=decimal.Decimal("70"),
                      quantity=decimal.Decimal("10"),
                      price=decimal.Decimal("70"))
    base_order.is_waiting_for_chained_trigger = True
    # base_order.state is None since no state has been associated to it (not initiliazed)
    assert base_order.state is None
    assert base_order.is_initialized is False

    await personal_data.create_as_chained_order(base_order)
    assert base_order.is_waiting_for_chained_trigger is False
    assert base_order.is_created() is True
    assert base_order.is_initialized is True
    assert isinstance(base_order.state, personal_data.OpenOrderState)


@pytest.mark.asyncio
async def test_create_as_chained_order_bundled_order_no_open_order(trader_simulator):
    config, exchange_manager_inst, trader_inst = trader_simulator

    base_order = personal_data.BuyLimitOrder(trader_inst)
    base_order.update(order_type=enums.TraderOrderType.BUY_LIMIT,
                      symbol="BTC/USDT",
                      current_price=decimal.Decimal("70"),
                      quantity=decimal.Decimal("10"),
                      price=decimal.Decimal("70"))
    base_order.has_been_bundled = True
    # base_order.state is None since no state has been associated to it (not initiliazed)
    assert base_order.state is None
    assert base_order.is_initialized is False

    #no order in order_manager, register as pending order
    assert not exchange_manager_inst.exchange_personal_data.orders_manager.orders
    assert not exchange_manager_inst.exchange_personal_data.orders_manager.pending_creation_orders

    # simulate real trader
    trader_inst.simulate = False
    await personal_data.create_as_chained_order(base_order)
    # did not add it to orders
    assert not exchange_manager_inst.exchange_personal_data.orders_manager.orders
    assert exchange_manager_inst.exchange_personal_data.orders_manager.pending_creation_orders == [base_order]

    assert base_order.is_waiting_for_chained_trigger is False
    # still not initialized
    assert base_order.is_initialized is False


@pytest.mark.asyncio
async def test_create_as_chained_order_bundled_order_no_open_order(trader_simulator):
    config, exchange_manager_inst, trader_inst = trader_simulator

    open_order_1 = personal_data.SellLimitOrder(trader_inst)
    open_order_2 = personal_data.BuyLimitOrder(trader_inst)
    open_order_1.update(order_type=enums.TraderOrderType.SELL_LIMIT,
                        order_id="open_order_1_id",
                        symbol="BTC/USDT",
                        current_price=decimal.Decimal("70"),
                        quantity=decimal.Decimal("10"),
                        price=decimal.Decimal("70"))
    open_order_2.update(order_type=enums.TraderOrderType.BUY_LIMIT,
                        order_id="open_order_2_id",
                        symbol="BTC/USDT",
                        current_price=decimal.Decimal("70"),
                        quantity=decimal.Decimal("10"),
                        price=decimal.Decimal("70"),
                        reduce_only=True)
    await exchange_manager_inst.exchange_personal_data.orders_manager.upsert_order_instance(open_order_1)
    await exchange_manager_inst.exchange_personal_data.orders_manager.upsert_order_instance(open_order_2)
    assert not exchange_manager_inst.exchange_personal_data.orders_manager.pending_creation_orders
    assert exchange_manager_inst.exchange_personal_data.orders_manager.get_all_orders() == [
        open_order_1, open_order_2
    ]

    base_order = personal_data.BuyLimitOrder(trader_inst)
    base_order.update(order_type=enums.TraderOrderType.BUY_LIMIT,
                      order_id="base_order_id",
                      symbol="BTC/USDT",
                      current_price=decimal.Decimal("55"),
                      quantity=decimal.Decimal("10"),
                      price=decimal.Decimal("70"),
                      reduce_only=False)
    base_order.has_been_bundled = True

    # simulate real trader
    trader_inst.simulate = False
    await personal_data.create_as_chained_order(base_order)
    registered_orders = exchange_manager_inst.exchange_personal_data.orders_manager.get_all_orders()
    assert len(registered_orders) == 2
    assert registered_orders[0] is open_order_1
    inserted_pending_order = exchange_manager_inst.exchange_personal_data.orders_manager.get_all_orders()[1]
    assert inserted_pending_order is base_order
    assert inserted_pending_order.reduce_only is True  # inserted_pending_order got preserved and updated
    # did not add it to orders
    assert not exchange_manager_inst.exchange_personal_data.orders_manager.pending_creation_orders

    assert base_order.is_waiting_for_chained_trigger is False
    # still not initialized
    assert base_order.is_initialized is False
    # open_order_2 got cleared
    assert open_order_2.exchange_manager is None


@pytest.mark.asyncio
async def test_ensure_orders_relevancy_without_positions(trader_simulator):
    config, exchange_manager_inst, trader_inst = trader_simulator
    order_mock = Mock(exchange_manager=exchange_manager_inst, symbol="BTC/USD")
    exchange_manager_inst.exchange_personal_data.positions_manager.positions = {}
    # without positions: doing nothing
    async with personal_data.ensure_orders_relevancy(order=order_mock):
        pass
    # nothing happened


@pytest.mark.asyncio
async def test_ensure_orders_relevancy_with_positions(future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    position = personal_data.LinearPosition(trader_inst, default_contract)
    position.symbol = DEFAULT_FUTURE_SYMBOL
    order_mock = Mock(exchange_manager=exchange_manager_inst, symbol=DEFAULT_FUTURE_SYMBOL)
    trader_mock = Mock(cancel_order=AsyncMock())
    group_mock = Mock(on_cancel=AsyncMock())
    to_cancel_order_mock = Mock(trader=trader_mock, order_group=group_mock, status=enums.OrderStatus.OPEN,
                                     is_open=Mock(return_value=True), reduce_only=True,
                                     symbol=DEFAULT_FUTURE_SYMBOL)
    # with positions
    exchange_manager_inst.exchange_personal_data.positions_manager.positions = {"BTC/USDT": position}
    exchange_manager_inst.exchange_personal_data.orders_manager.orders = {"id": to_cancel_order_mock}
    async with personal_data.ensure_orders_relevancy(order=order_mock):
        # no change
        pass
    trader_mock.cancel_order.assert_not_called()
    # with order parameter
    async with personal_data.ensure_orders_relevancy(order=order_mock):
        # changing side
        position.side = "other_side"
    trader_mock.cancel_order.assert_not_called()
    # don't canceled order as position was idle (same situation as open a short from a 0 quantity position,
    # which is considered as long)
    async with personal_data.ensure_orders_relevancy(position=position):
        # changing side
        position.side = "other_other_side"
    trader_mock.cancel_order.assert_not_called()
    # with a non-0 quantity position
    position.quantity = decimal.Decimal("2")
    # with position parameter
    async with personal_data.ensure_orders_relevancy(position=position):
        # changing side
        position.side = "other_side"
    # canceled order
    trader_mock.cancel_order.assert_called_once_with(to_cancel_order_mock)


@pytest.mark.asyncio
async def test_get_order_size_portfolio_percent(trader_simulator):
    config, exchange_manager_inst, trader_inst = trader_simulator
    api.force_set_mark_price(exchange_manager_inst, "BTC/UDST", 1000)
    # no USDT in portfolio
    assert await personal_data.get_order_size_portfolio_percent(
        exchange_manager_inst, decimal.Decimal("0.1"), enums.TradeOrderSide.BUY, "BTC/UDST"
    ) == constants.ZERO
    # 10 BTC in portfolio
    assert await personal_data.get_order_size_portfolio_percent(
        exchange_manager_inst, decimal.Decimal("1"), enums.TradeOrderSide.SELL, "BTC/UDST"
    ) == decimal.Decimal("10")
    assert await personal_data.get_order_size_portfolio_percent(
        exchange_manager_inst, decimal.Decimal("10"), enums.TradeOrderSide.SELL, "BTC/UDST"
    ) == decimal.Decimal("100")
    assert await personal_data.get_order_size_portfolio_percent(
        exchange_manager_inst, decimal.Decimal("11"), enums.TradeOrderSide.SELL, "BTC/UDST"
    ) == decimal.Decimal("100")
    assert await personal_data.get_order_size_portfolio_percent(
        exchange_manager_inst, decimal.Decimal("6.6666"), enums.TradeOrderSide.SELL, "BTC/UDST"
    ) == decimal.Decimal("66.666")

    # 100 USDT in portfolio
    exchange_manager_inst.exchange_personal_data.portfolio_manager.portfolio.portfolio['UDST'].available \
        = decimal.Decimal("100")
    exchange_manager_inst.exchange_personal_data.portfolio_manager.portfolio.portfolio['UDST'].total \
        = decimal.Decimal("100")
    assert await personal_data.get_order_size_portfolio_percent(
        exchange_manager_inst, decimal.Decimal("0.1"), enums.TradeOrderSide.BUY, "BTC/UDST"
    ) == decimal.Decimal("100")
    assert await personal_data.get_order_size_portfolio_percent(
        exchange_manager_inst, decimal.Decimal("0.01"), enums.TradeOrderSide.BUY, "BTC/UDST"
    ) == decimal.Decimal("10")


def test_get_split_orders_count_and_increment():
    # example SOL/BTC values from 12/09/2023
    symbol_market = {
        enums.ExchangeConstantsMarketStatusColumns.LIMITS.value: {
            enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT_MIN.value: 0.01,
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT_MAX.value: 90000000.0,
            },
            enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST_MIN.value: 0.0001,
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST_MAX.value: 9000000.0
            },
            enums.ExchangeConstantsMarketStatusColumns.LIMITS_PRICE.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_PRICE_MIN.value: 1e-07,
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_PRICE_MAX.value: 1000.0
            },
        },
        enums.ExchangeConstantsMarketStatusColumns.PRECISION.value: {
            enums.ExchangeConstantsMarketStatusColumns.PRECISION_PRICE.value: 7,
            enums.ExchangeConstantsMarketStatusColumns.PRECISION_AMOUNT.value: 2
        }
    }
    # all valid values
    assert personal_data.get_split_orders_count_and_increment(
        decimal.Decimal("0.0006858"),
        decimal.Decimal("0.0006958"),
        decimal.Decimal("1"),
        4,
        symbol_market,
        True
    ) == (4, decimal.Decimal('0.0000025'))

    # too small amount for cost: adapt to 3 orders
    assert personal_data.get_split_orders_count_and_increment(
        decimal.Decimal("0.0006858"),
        decimal.Decimal("0.0006958"),
        decimal.Decimal("0.5"),
        4,
        symbol_market,
        True
    ) == (3, decimal.Decimal('0.000003333333333333333333333333333'))

    # too small amount for cost: adapt to 0 orders
    assert personal_data.get_split_orders_count_and_increment(
        decimal.Decimal("0.0006858"),
        decimal.Decimal("0.0006958"),
        decimal.Decimal("0.1"),
        4,
        symbol_market,
        True
    ) == (0, decimal.Decimal('0'))

    # too small amount for cost (because of the lowest price order amount that gets truncated because of
    # exchange precision rules): adapt to 0 orders
    assert personal_data.get_split_orders_count_and_increment(
        decimal.Decimal("0.0006963"),
        decimal.Decimal("0.0006958"),
        decimal.Decimal("0.14985"),
        4,
        symbol_market,
        False
    ) == (0, decimal.Decimal('0'))
