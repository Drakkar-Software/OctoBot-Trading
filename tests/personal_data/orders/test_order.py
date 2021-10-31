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
import pytest
import decimal

import octobot_trading.errors as errors
import octobot_trading.enums as enums
import octobot_trading.constants as constants
import octobot_trading.personal_data as personal_data

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

    order_inst.update(order_type=enums.TraderOrderType.STOP_LOSS_LIMIT,
                      symbol="ETH/BTC",
                      quantity=0.1,
                      quantity_filled=5.2,
                      price=0.12,
                      stop_price=0.9)
    assert order_inst.origin_stop_price == 0.9
    assert order_inst.origin_price == 0.12


async def test_simulated_update(trader_simulator):
    config, exchange_manager_inst, trader_inst = trader_simulator
    order_sim_inst = personal_data.Order(trader_inst)

    order_sim_inst.update(order_type=enums.TraderOrderType.SELL_MARKET,
                          symbol="LTC/USDT",
                          quantity=100,
                          price=3.22)
    assert order_sim_inst.status == enums.OrderStatus.OPEN
    assert order_sim_inst.filled_quantity == order_sim_inst.origin_quantity == 100


def test_order_state_creation(trader_simulator):
    config, exchange_manager_inst, trader_inst = trader_simulator
    order_inst = personal_data.Order(trader_inst)
    # errors.InvalidOrderState exception is caught by context manager
    with order_inst.order_state_creation():
        raise errors.InvalidOrderState()


def test_parse_order_type():
    untyped_raw_order = {
        enums.ExchangeConstantsOrderColumns.SIDE.value: enums.TradeOrderSide.BUY.value,
        enums.ExchangeConstantsOrderColumns.TYPE.value: None,
    }
    untyped_raw_with_maker_order = {
        enums.ExchangeConstantsOrderColumns.SIDE.value: enums.TradeOrderSide.BUY.value,
        enums.ExchangeConstantsOrderColumns.TAKERORMAKER.value: enums.ExchangeConstantsOrderColumns.MAKER.value,
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


def test_update_from_raw(trader_simulator):
    config, exchange_manager_inst, trader_inst = trader_simulator
    order_inst = personal_data.Order(trader_inst)
    # Binance example market order
    raw_order = {
        'id': '362550114',
        'clientOrderId': 'x-T9698eeeeeeeeeeeeee792',
        'timestamp': 1637579281.377,
        'datetime': '2021-11-22T11:08:01.377Z',
        'lastTradeTimestamp': None,
        'symbol': 'WIN/USDT',
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
    assert order_inst.side is enums.TradeOrderSide.SELL
    assert order_inst.status is enums.OrderStatus.CLOSED
    assert order_inst.symbol == "WIN/USDT"
    assert order_inst.currency == "WIN"
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
    assert order_inst.fee == {'cost': decimal.Decimal('0.03764836'), 'currency': 'USDT'}

    order_inst = personal_data.Order(trader_inst)
    # Binance example limit order
    raw_order = {
        'id': '362550114',
        'clientOrderId': 'x-T9698eeeeeeeeeeeeee792',
        'timestamp': 1637579281.377,
        'datetime': '2021-11-22T11:08:01.377Z',
        'lastTradeTimestamp': None,
        'symbol': 'WIN/USDT',
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
    assert order_inst.side is enums.TradeOrderSide.BUY
    assert order_inst.status is enums.OrderStatus.CLOSED
    assert order_inst.symbol == "WIN/USDT"
    assert order_inst.currency == "WIN"
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
    assert order_inst.fee == {'cost': decimal.Decimal('0.03764836'), 'currency': 'USDT'}
