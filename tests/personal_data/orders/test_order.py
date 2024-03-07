#  Drakkar-Software OctoBot
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
import decimal

import octobot_trading.errors as errors
import octobot_trading.enums as enums
import octobot_trading.constants as constants
import octobot_trading.personal_data as personal_data
import octobot_trading.personal_data.orders.order_util as order_util
import octobot_trading.storage.orders_storage as orders_storage

from tests import event_loop
from tests.exchanges import exchange_manager, simulated_exchange_manager
from tests.exchanges.traders import trader_simulator
from tests.exchanges.traders import trader
from tests.test_utils.random_numbers import random_price

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_get_profitability(trader_simulator):
    config, exchange_manager_inst, trader_inst = trader_simulator

    # Test filled_price > create_last_price
    # test side SELL
    order_filled_sup_side_sell_inst = personal_data.Order(trader_inst)
    order_filled_sup_side_sell_inst.side = enums.TradeOrderSide.SELL
    order_filled_sup_side_sell_inst.filled_price = 10
    order_filled_sup_side_sell_inst.created_last_price = 9
    assert order_filled_sup_side_sell_inst.get_profitability() == (-(1 - 10 / 9))

    # test side BUY
    order_filled_sup_side_sell_inst = personal_data.Order(trader_inst)
    order_filled_sup_side_sell_inst.side = enums.TradeOrderSide.BUY
    order_filled_sup_side_sell_inst.filled_price = 15.114778
    order_filled_sup_side_sell_inst.created_last_price = 7.265
    assert order_filled_sup_side_sell_inst.get_profitability() == (1 - 15.114778 / 7.265)

    # Test filled_price < create_last_price
    # test side SELL
    order_filled_sup_side_sell_inst = personal_data.Order(trader_inst)
    order_filled_sup_side_sell_inst.side = enums.TradeOrderSide.SELL
    order_filled_sup_side_sell_inst.filled_price = 11.556877
    order_filled_sup_side_sell_inst.created_last_price = 20
    assert order_filled_sup_side_sell_inst.get_profitability() == (1 - 20 / 11.556877)

    # test side BUY
    order_filled_sup_side_sell_inst = personal_data.Order(trader_inst)
    order_filled_sup_side_sell_inst.side = enums.TradeOrderSide.BUY
    order_filled_sup_side_sell_inst.filled_price = 8
    order_filled_sup_side_sell_inst.created_last_price = 14.35
    assert order_filled_sup_side_sell_inst.get_profitability() == (-(1 - 14.35 / 8))

    # Test filled_price == create_last_price
    # test side SELL
    order_filled_sup_side_sell_inst = personal_data.Order(trader_inst)
    order_filled_sup_side_sell_inst.side = enums.TradeOrderSide.SELL
    order_filled_sup_side_sell_inst.filled_price = 1517374.4567
    order_filled_sup_side_sell_inst.created_last_price = 1517374.4567
    assert order_filled_sup_side_sell_inst.get_profitability() == 0

    # test side BUY
    order_filled_sup_side_sell_inst = personal_data.Order(trader_inst)
    order_filled_sup_side_sell_inst.side = enums.TradeOrderSide.BUY
    order_filled_sup_side_sell_inst.filled_price = 0.4275587387858527
    order_filled_sup_side_sell_inst.created_last_price = 0.4275587387858527
    assert order_filled_sup_side_sell_inst.get_profitability() == 0


async def test_update(trader):
    config, exchange_manager_inst, trader_inst = trader

    # with real trader
    order_inst = personal_data.Order(trader_inst)
    order_inst.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol="BTC/USDT",
                      current_price=10000,
                      quantity=1)

    assert order_inst.order_type == enums.TraderOrderType.BUY_MARKET
    assert order_inst.symbol == "BTC/USDT"
    assert order_inst.created_last_price == 10000
    assert order_inst.origin_quantity == 1
    assert order_inst.creation_time != 0
    assert order_inst.side is None
    assert order_inst.status == enums.OrderStatus.OPEN
    assert order_inst.filled_quantity != order_inst.origin_quantity
    assert order_inst.tag is None

    order_inst.update(order_type=enums.TraderOrderType.STOP_LOSS_LIMIT,
                      symbol="ETH/BTC",
                      quantity=0.1,
                      quantity_filled=5.2,
                      price=0.12,
                      stop_price=0.9,
                      tag="tag")
    assert order_inst.origin_stop_price == 0.9
    assert order_inst.origin_price == 0.12
    assert order_inst.tag == "tag"


async def test_simulated_update(trader_simulator):
    config, exchange_manager_inst, trader_inst = trader_simulator
    order_sim_inst = personal_data.Order(trader_inst)

    order_sim_inst.update(order_type=enums.TraderOrderType.SELL_MARKET,
                          symbol="LTC/USDT",
                          quantity=100,
                          price=3.22)
    assert order_sim_inst.status == enums.OrderStatus.OPEN
    assert order_sim_inst.filled_quantity == order_sim_inst.origin_quantity == 100


async def test_order_state_creation(trader_simulator):
    config, exchange_manager_inst, trader_inst = trader_simulator
    order_inst = personal_data.Order(trader_inst)
    # errors.InvalidOrderState exception is caught by context manager
    with order_inst.order_state_creation():
        raise errors.InvalidOrderState()


async def test_parse_order_type():
    untyped_raw_order = {
        enums.ExchangeConstantsOrderColumns.SIDE.value: enums.TradeOrderSide.BUY.value,
        enums.ExchangeConstantsOrderColumns.TYPE.value: None,
    }
    untyped_raw_with_maker_order = {
        enums.ExchangeConstantsOrderColumns.SIDE.value: enums.TradeOrderSide.BUY.value,
        enums.ExchangeConstantsOrderColumns.TAKER_OR_MAKER.value: enums.ExchangeConstantsOrderColumns.MAKER.value,
        enums.ExchangeConstantsOrderColumns.TYPE.value: None,
    }
    typed_raw_order = {
        enums.ExchangeConstantsOrderColumns.SIDE.value: enums.TradeOrderSide.SELL.value,
        enums.ExchangeConstantsOrderColumns.TYPE.value: enums.TradeOrderType.MARKET,
    }
    assert personal_data.parse_order_type({}) == \
           (None, None)
    assert personal_data.parse_order_type(untyped_raw_order) == \
           (enums.TradeOrderSide.BUY, enums.TraderOrderType.UNKNOWN)
    assert personal_data.parse_order_type(untyped_raw_with_maker_order) == \
           (enums.TradeOrderSide.BUY, enums.TraderOrderType.BUY_LIMIT)
    untyped_raw_with_maker_order[enums.ExchangeConstantsOrderColumns.SIDE.value] = enums.TradeOrderSide.SELL.value
    assert personal_data.parse_order_type(untyped_raw_with_maker_order) == \
           (enums.TradeOrderSide.SELL, enums.TraderOrderType.SELL_LIMIT)
    assert personal_data.parse_order_type(typed_raw_order) == \
           (enums.TradeOrderSide.SELL, enums.TraderOrderType.SELL_MARKET)
    typed_raw_order[enums.ExchangeConstantsOrderColumns.TYPE.value] = enums.TradeOrderType.LIMIT
    assert personal_data.parse_order_type(typed_raw_order) == \
           (enums.TradeOrderSide.SELL, enums.TraderOrderType.SELL_LIMIT)


async def test_update_from_raw(trader_simulator):
    config, exchange_manager_inst, trader_inst = trader_simulator
    order_inst = personal_data.Order(trader_inst)
    # binance example market order
    raw_order = {
        'id': '362550114',
        'exchange_id': '123',
        'clientOrderId': 'x-T9698eeeeeeeeeeeeee792',
        'timestamp': 1637579281.377,
        'datetime': '2021-11-22T11:08:01.377Z',
        'lastTradeTimestamp': None,
        'symbol': 'UNI/USDT',
        'type': 'market',
        'timeInForce': 'GTC',
        'postOnly': False,
        'side': 'sell',
        'price': None,
        'stopPrice': None,
        'amount': 44964.0,
        'cost': None,
        'average': None,
        'filled': 44964.0,
        'remaining': 0.0,
        'status': 'closed',
        'fee': {'cost': 0.03764836, 'currency': 'USDT'},
        'trades': [],
        'fees': []
    }
    assert order_inst.update_from_raw(raw_order) is True
    assert order_inst.order_type is enums.TraderOrderType.SELL_MARKET
    assert order_inst.order_id == "362550114"
    assert order_inst.exchange_order_id == "123"
    assert order_inst.side is enums.TradeOrderSide.SELL
    assert order_inst.status is enums.OrderStatus.CLOSED
    assert order_inst.symbol == "UNI/USDT"
    assert order_inst.currency == "UNI"
    assert order_inst.market == "USDT"
    assert order_inst.taker_or_maker is enums.ExchangeConstantsMarketPropertyColumns.TAKER.value
    assert order_inst.origin_price == constants.ZERO
    assert order_inst.origin_stop_price == constants.ZERO
    assert order_inst.origin_quantity == decimal.Decimal("44964.0")
    assert order_inst.filled_quantity == decimal.Decimal("44964.0")
    assert order_inst.filled_price == constants.ZERO
    assert order_inst.total_cost == constants.ZERO
    assert order_inst.created_last_price == constants.ZERO
    assert order_inst.timestamp == 1637579281.377
    assert order_inst.canceled_time == 0
    assert order_inst.executed_time == 1637579281.377
    assert order_inst.fee == {
        enums.FeePropertyColumns.COST.value: decimal.Decimal('0.03764836'),
        enums.FeePropertyColumns.CURRENCY.value: 'USDT',
        enums.FeePropertyColumns.IS_FROM_EXCHANGE.value: True,
    }

    order_inst = personal_data.Order(trader_inst)
    # binance example limit order
    raw_order = {
        'id': '362550114',
        'exchange_id': '123a',
        'clientOrderId': 'x-T9698eeeeeeeeeeeeee792',
        'timestamp': 1637579281.377,
        'datetime': '2021-11-22T11:08:01.377Z',
        'lastTradeTimestamp': None,
        'symbol': 'UNI/USDT',
        'type': 'limit',
        'timeInForce': 'GTC',
        'postOnly': False,
        'side': 'buy',
        'price': 12.664,
        'stopPrice': None,
        'amount': 44964.0,
        'cost': 123.6667,
        'average': 13,
        'filled': 44964.0,
        'remaining': 0.0,
        'status': 'closed',
        'fee': {'cost': 0.03764836, 'currency': 'USDT'},
        'trades': [],
        'fees': []
    }
    assert order_inst.update_from_raw(raw_order) is True
    assert order_inst.order_type is enums.TraderOrderType.BUY_LIMIT
    assert order_inst.order_id == "362550114"
    assert order_inst.exchange_order_id == "123a"
    assert order_inst.side is enums.TradeOrderSide.BUY
    assert order_inst.status is enums.OrderStatus.CLOSED
    assert order_inst.symbol == "UNI/USDT"
    assert order_inst.currency == "UNI"
    assert order_inst.market == "USDT"
    assert order_inst.taker_or_maker is enums.ExchangeConstantsMarketPropertyColumns.MAKER.value
    assert order_inst.origin_price == decimal.Decimal("12.664")
    assert order_inst.origin_stop_price == constants.ZERO
    assert order_inst.origin_quantity == decimal.Decimal("44964.0")
    assert order_inst.filled_quantity == decimal.Decimal("44964.0")
    assert order_inst.filled_price == decimal.Decimal("13")
    assert order_inst.total_cost == decimal.Decimal("123.6667")
    assert order_inst.created_last_price == decimal.Decimal("12.664")
    assert order_inst.timestamp == 1637579281.377
    assert order_inst.canceled_time == 0
    assert order_inst.executed_time == 1637579281.377
    assert order_inst.fee == {
        enums.FeePropertyColumns.COST.value: decimal.Decimal('0.03764836'),
        enums.FeePropertyColumns.CURRENCY.value: 'USDT',
        enums.FeePropertyColumns.IS_FROM_EXCHANGE.value: True,
    }


async def test_set_as_chained_order(trader_simulator):
    config, exchange_manager_inst, trader_inst = trader_simulator

    base_order = personal_data.Order(trader_inst)

    with pytest.raises(errors.ConflictingOrdersError):
        await base_order.set_as_chained_order(base_order, True, {}, True)
    assert base_order.triggered_by is None
    assert base_order.has_been_bundled is False
    assert base_order.update_with_triggering_order_fees is False
    assert base_order.status is enums.OrderStatus.OPEN
    assert base_order.state is None

    chained_order = personal_data.Order(trader_inst)
    await chained_order.set_as_chained_order(base_order, True, {}, True)
    assert chained_order.triggered_by is base_order
    assert chained_order.has_been_bundled is True
    assert base_order.update_with_triggering_order_fees is False
    assert chained_order.update_with_triggering_order_fees is True
    assert chained_order.status is enums.OrderStatus.PENDING_CREATION
    assert isinstance(chained_order.state, personal_data.PendingCreationOrderState)


async def test_trigger_chained_orders(trader_simulator):
    config, exchange_manager_inst, trader_inst = trader_simulator

    base_order = personal_data.Order(trader_inst)
    # does nothing
    await base_order.on_filled(True)

    # with chained orders
    order_mock_1 = mock.Mock(
        update_price_if_outdated=mock.AsyncMock(),
        update_quantity_with_order_fees=mock.AsyncMock(return_value=True),
        should_be_created=mock.Mock(return_value=True)
    )
    order_mock_2 = mock.Mock(
        update_price_if_outdated=mock.AsyncMock(),
        update_quantity_with_order_fees=mock.AsyncMock(return_value=True),
        should_be_created=mock.Mock(return_value=False)
    )
    with mock.patch.object(order_util, "create_as_chained_order", mock.AsyncMock()) as create_as_chained_order_mock:

        base_order.add_chained_order(order_mock_1)
        base_order.add_chained_order(order_mock_2)

        # does not triggers chained orders
        await base_order.on_filled(False)
        order_mock_1.should_be_created.assert_not_called()
        order_mock_2.should_be_created.assert_not_called()
        order_mock_1.update_price_if_outdated.assert_not_called()
        order_mock_2.update_price_if_outdated.assert_not_called()
        order_mock_1.update_quantity_with_order_fees.assert_not_called()
        order_mock_2.update_quantity_with_order_fees.assert_not_called()
        create_as_chained_order_mock.assert_not_called()

        # triggers chained orders
        await base_order.on_filled(True)
        order_mock_1.should_be_created.assert_called_once()
        order_mock_2.should_be_created.assert_called_once()
        order_mock_1.update_price_if_outdated.assert_called_once()
        order_mock_2.update_price_if_outdated.assert_called_once()
        order_mock_1.update_quantity_with_order_fees.assert_called_once()
        order_mock_2.update_quantity_with_order_fees.assert_called_once()
        create_as_chained_order_mock.assert_called_once_with(order_mock_1)


async def test_update_from_order(trader_simulator):
    config, exchange_manager_inst, trader_inst = trader_simulator

    base_order_1 = personal_data.Order(trader_inst)
    base_order_1.order_id = "1"
    base_order_1.exchange_order_id = "1a"
    base_order_1.status = enums.OrderStatus.OPEN
    base_order_1.filled_price = decimal.Decimal("2")

    base_order_2 = personal_data.Order(trader_inst)
    base_order_2.order_id = "2"
    base_order_2.exchange_order_id = "2a"
    base_order_2.status = enums.OrderStatus.CLOSED
    base_order_2.filled_price = decimal.Decimal("3")

    # no state
    await base_order_1.update_from_order(base_order_2)
    assert base_order_1.order_id == "2"
    assert base_order_1.exchange_order_id == "2a"
    assert base_order_1.status == enums.OrderStatus.CLOSED
    assert base_order_1.filled_price == decimal.Decimal("3")

    # with state
    state_1 = personal_data.OpenOrderState(base_order_1, False)
    state_2 = personal_data.OpenOrderState(base_order_2, False)
    base_order_1.state = state_1
    base_order_2.state = state_2
    base_order_2.order_id = "3"
    base_order_2.exchange_order_id = "3AAAAA"
    base_order_2.status = enums.OrderStatus.CANCELED
    base_order_2.filled_price = decimal.Decimal("4")
    await base_order_1.update_from_order(base_order_2)
    assert base_order_1.order_id == "3"
    assert base_order_1.exchange_order_id == "3AAAAA"
    assert base_order_1.status == enums.OrderStatus.CANCELED
    assert base_order_1.filled_price == decimal.Decimal("4")
    assert base_order_1.state is state_2
    assert base_order_1.state.order is base_order_1


async def test_update_from_order_storage(trader_simulator):
    config, exchange_manager_inst, trader_inst = trader_simulator

    order = personal_data.BuyLimitOrder(trader_inst)
    order.update(order_type=enums.TraderOrderType.BUY_LIMIT,
                 symbol="BTC/USDT",
                 current_price=decimal.Decimal("70"),
                 quantity=decimal.Decimal("10"),
                 price=decimal.Decimal("70"),
                 exchange_order_id="PLOP")
    origin_tag = order.tag
    origin_trader_creation_kwargs = order.trader_creation_kwargs
    origin_exchange_creation_params = order.exchange_creation_params
    origin_order_id = order.order_id
    origin_exchange_order_id = order.exchange_order_id
    origin_has_been_bundled = order.has_been_bundled
    origin_associated_entry_ids = order.associated_entry_ids
    origin_update_with_triggering_order_fees = order.update_with_triggering_order_fees

    # wrong format
    order.update_from_storage_order_details({"hello": "hi there"})
    assert order.tag is origin_tag
    assert order.trader_creation_kwargs is origin_trader_creation_kwargs
    assert order.exchange_creation_params is origin_exchange_creation_params
    assert order.order_id is origin_order_id
    assert order.exchange_order_id is origin_exchange_order_id
    assert order.has_been_bundled is origin_has_been_bundled
    assert order.associated_entry_ids is origin_associated_entry_ids
    assert order.broker_applied is False
    assert order.update_with_triggering_order_fees is origin_update_with_triggering_order_fees

    # partial update
    order.update_from_storage_order_details({
        enums.StoredOrdersAttr.TRADER_CREATION_KWARGS.value: {"plop": 1}
    })
    assert order.tag is origin_tag
    assert order.trader_creation_kwargs == {"plop": 1} != origin_trader_creation_kwargs
    assert order.exchange_creation_params is origin_exchange_creation_params
    assert order.order_id is origin_order_id
    assert order.exchange_order_id is origin_exchange_order_id
    assert order.has_been_bundled is origin_has_been_bundled
    assert order.associated_entry_ids is origin_associated_entry_ids
    assert order.update_with_triggering_order_fees is origin_update_with_triggering_order_fees

    # full update
    order.update_from_storage_order_details({
        constants.STORAGE_ORIGIN_VALUE: {
            enums.ExchangeConstantsOrderColumns.TAG.value: "t1",
            enums.ExchangeConstantsOrderColumns.ID.value: "11a",
            enums.ExchangeConstantsOrderColumns.EXCHANGE_ID.value: "eee1",
            enums.ExchangeConstantsOrderColumns.BROKER_APPLIED.value: True,
        },
        enums.StoredOrdersAttr.TRADER_CREATION_KWARGS.value: {"plop2": 1},
        enums.StoredOrdersAttr.EXCHANGE_CREATION_PARAMS.value: {"ex": 2, "gg": "yesyes"},
        enums.StoredOrdersAttr.HAS_BEEN_BUNDLED.value: True,
        enums.StoredOrdersAttr.ENTRIES.value: ["ABC", "2"],
        enums.StoredOrdersAttr.UPDATE_WITH_TRIGGERING_ORDER_FEES.value: True,
    })
    assert order.tag == "t1" != origin_tag
    assert order.trader_creation_kwargs == {"plop2": 1} != origin_trader_creation_kwargs
    assert order.exchange_creation_params == {"ex": 2, "gg": "yesyes"} != origin_exchange_creation_params
    assert order.order_id == "11a" != origin_order_id
    assert order.broker_applied is True
    assert order.exchange_order_id == "eee1" != origin_exchange_order_id
    assert order.has_been_bundled is True is not origin_has_been_bundled
    assert order.associated_entry_ids == ["ABC", "2"] != origin_associated_entry_ids
    assert order.has_been_bundled is True is not origin_has_been_bundled
    assert order.update_with_triggering_order_fees is True is not origin_update_with_triggering_order_fees
