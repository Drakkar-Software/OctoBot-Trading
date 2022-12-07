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
import cryptofeed.defines as cryptofeed_constants
from octobot_trading.enums import (
    ExchangeConstantsMarketPropertyColumns,
    ExchangeConstantsOrderColumns,
    OrderStatus,
    TradeOrderSide,
    TradeOrderType,
    TraderOrderType,
)
import octobot_trading.exchanges.parser as parser
from .parser_tests_util import (
    mock_abstract_exchange,
)

pytestmark = pytest.mark.asyncio


def active_parser_class():
    return parser.OrdersParser(exchange=mock_abstract_exchange())


def active_parser(raw_records):
    _parser = active_parser_class()
    return _parser.parse_orders(raw_records)


def get_raw_canceled_orders():
    return [
        {
            "info": {
                "order_id": "da13fb16-daa0-4520-bc01-52a4103c50ca",
                "last_exec_price": "0",
                "cum_exec_qty": "0",
                "cum_exec_value": "0",
                "cum_exec_fee": "0",
                "symbol": "BTCUSDT",
                "side": "Sell",
                "order_type": "Limit",
                "time_in_force": "GoodTillCancel",
                "order_status": "Cancelled",
                "tp_trigger_by": "UNKNOWN",
                "sl_trigger_by": "UNKNOWN",
                "price": "17349",
                "qty": "0.004",
                "order_link_id": "",
                "reduce_only": True,
                "close_on_trigger": True,
                "take_profit": "0",
                "stop_loss": "0",
                "created_time": "2022-11-22T22:31:52Z",
                "updated_time": "2022-11-22T22:45:34Z",
            },
            "id": "da13fb16-daa0-4520-bc01-52a4103c50ca",
            "clientOrderId": None,
            "timestamp": 1669156312000,
            "datetime": "2022-11-22T22:31:52.000Z",
            "lastTradeTimestamp": 1669157134000,
            "symbol": "BTC/USDT",
            "type": "limit",
            "timeInForce": "GTC",
            "postOnly": False,
            "side": "sell",
            "price": 17349.0,
            "stopPrice": None,
            "amount": 0.004,
            "cost": 0.0,
            "average": None,
            "filled": 0.0,
            "remaining": 0.004,
            "status": "canceled",
            "fee": {"cost": 0.0, "currency": "USDT"},
            "trades": [],
            "fees": [{"cost": 0.0, "currency": "USDT"}],
        }
    ]


def get_raw_open_market_orders():
    return [
        {
            "info": {
                "order_id": "16b1bf6c-b3eb-4145-9a31-c24e68562d8a",
                "symbol": "BTCUSDT",
                "side": "Buy",
                "order_type": "Market",
                "price": "17964.5",
                "qty": "0.006",
                "time_in_force": "ImmediateOrCancel",
                "order_status": "Created",
                "last_exec_price": "0",
                "cum_exec_qty": "0",
                "cum_exec_value": "0",
                "cum_exec_fee": "0",
                "reduce_only": False,
                "close_on_trigger": False,
                "order_link_id": "",
                "created_time": "2022-12-01T14:44:54Z",
                "updated_time": "2022-12-01T14:44:54Z",
                "take_profit": "0",
                "stop_loss": "16938",
                "tp_trigger_by": "UNKNOWN",
                "sl_trigger_by": "LastPrice",
                "position_idx": "0",
            },
            "id": "16b1bf6c-b3eb-4145-9a31-c24e68562d8a",
            "clientOrderId": None,
            "timestamp": 1669905894000,
            "datetime": "2022-12-01T14:44:54.000Z",
            "lastTradeTimestamp": 1669905894000,
            "symbol": "BTC/USDT",
            "type": "market",
            "timeInForce": "IOC",
            "postOnly": False,
            "side": "buy",
            "price": 17964.5,
            "stopPrice": None,
            "amount": 0.006,
            "cost": 0.0,
            "average": None,
            "filled": 0.0,
            "remaining": 0.006,
            "status": "open",
            "fee": {"cost": 0.0, "currency": "USDT"},
            "trades": [],
            "fees": [{"cost": 0.0, "currency": "USDT"}],
        },
    ]


def get_raw_open_long_limit_tp_orders():
    return [
        {
            "info": {
                "order_id": "f9bcf5e1-004f-44d3-9487-901b982d4c62",
                "symbol": "BTCUSDT",
                "side": "Sell",
                "order_type": "Limit",
                "price": "18394",
                "qty": "0.006",
                "time_in_force": "GoodTillCancel",
                "order_status": "Created",
                "last_exec_price": "0",
                "cum_exec_qty": "0",
                "cum_exec_value": "0",
                "cum_exec_fee": "0",
                "reduce_only": True,
                "close_on_trigger": True,
                "order_link_id": "",
                "created_time": "2022-12-01T15:03:09Z",
                "updated_time": "2022-12-01T15:03:09Z",
                "take_profit": "0",
                "stop_loss": "16938",
                "tp_trigger_by": "UNKNOWN",
                "sl_trigger_by": "UNKNOWN",
                "position_idx": "0",
            },
            "id": "f9bcf5e1-004f-44d3-9487-901b982d4c62",
            "clientOrderId": None,
            "timestamp": 1669906989000,
            "datetime": "2022-12-01T15:03:09.000Z",
            "lastTradeTimestamp": 1669906989000,
            "symbol": "BTC/USDT",
            "type": "limit",
            "timeInForce": "GTC",
            "postOnly": False,
            "side": "sell",
            "price": 18394.0,
            "stopPrice": None,
            "amount": 0.006,
            "cost": 0.0,
            "average": None,
            "filled": 0.0,
            "remaining": 0.006,
            "status": "open",
            "fee": {"cost": 0.0, "currency": "USDT"},
            "trades": [],
            "fees": [{"cost": 0.0, "currency": "USDT"}],
        },
    ]


def get_raw_open_short_limit_tp_orders():
    return [
        {
            "info": {
                "order_id": "de11a287-24cd-421a-ade8-8888f336779a",
                "last_exec_price": "0",
                "cum_exec_qty": "0",
                "cum_exec_value": "0",
                "cum_exec_fee": "0",
                "symbol": "BTCUSDT",
                "side": "Buy",
                "order_type": "Limit",
                "time_in_force": "GoodTillCancel",
                "order_status": "New",
                "tp_trigger_by": "UNKNOWN",
                "sl_trigger_by": "UNKNOWN",
                "price": "15785.5",
                "qty": "0.006",
                "order_link_id": "",
                "reduce_only": True,
                "close_on_trigger": True,
                "take_profit": "0",
                "stop_loss": "0",
                "created_time": "2022-12-01T15:03:09Z",
                "updated_time": "2022-12-01T15:03:09Z",
            },
            "id": "de11a287-24cd-421a-ade8-8888f336779a",
            "clientOrderId": None,
            "timestamp": 1669909167000,
            "datetime": "2022-12-01T15:39:27.000Z",
            "lastTradeTimestamp": 1669909167000,
            "symbol": "BTC/USDT",
            "type": "limit",
            "timeInForce": "GTC",
            "postOnly": False,
            "side": "buy",
            "price": 15785.5,
            "stopPrice": None,
            "amount": 0.006,
            "cost": 0.0,
            "average": None,
            "filled": 0.0,
            "remaining": 0.006,
            "status": "open",
            "fee": {"cost": 0.0, "currency": "USDT"},
            "trades": [],
            "fees": [{"cost": 0.0, "currency": "USDT"}],
        },
    ]


def get_raw_open_long_sl_orders():
    return [
        {
            "info": {
                "stop_order_id": "71830ad6-5f0d-410c-a0fc-82deb1b7b989",
                "trigger_price": "16938",
                "base_price": "0.00",
                "trigger_by": "LastPrice",
                "symbol": "BTCUSDT",
                "side": "Sell",
                "order_type": "Market",
                "time_in_force": "ImmediateOrCancel",
                "order_status": "Untriggered",
                "tp_trigger_by": "UNKNOWN",
                "sl_trigger_by": "UNKNOWN",
                "price": "0",
                "qty": "0.006",
                "order_link_id": "",
                "reduce_only": True,
                "close_on_trigger": True,
                "take_profit": "0",
                "stop_loss": "0",
                "created_time": "2022-12-01T14:44:54.000Z",
                "updated_time": "2022-12-01T14:44:54.000Z",
            },
            "id": "71830ad6-5f0d-410c-a0fc-82deb1b7b989",
            "clientOrderId": None,
            "timestamp": 1669905894000,
            "datetime": "2022-12-01T14:44:54.000Z",
            "lastTradeTimestamp": 1669905894000,
            "symbol": "BTC/USDT",
            "type": "market",
            "timeInForce": "IOC",
            "postOnly": False,
            "side": "sell",
            "price": None,
            "stopPrice": "16938",
            "amount": 0.006,
            "cost": None,
            "average": None,
            "filled": None,
            "remaining": None,
            "status": "open",
            "fee": None,
            "trades": [],
            "fees": [],
        },
    ]


def get_raw_open_short_sl_orders():
    return [
        {
            "info": {
                "stop_order_id": "71830ad6-5f0d-410c-a0fc-82deb1b7b989",
                "trigger_price": "17170",
                "base_price": "0.00",
                "trigger_by": "LastPrice",
                "symbol": "BTCUSDT",
                "side": "Buy",
                "order_type": "Market",
                "time_in_force": "ImmediateOrCancel",
                "order_status": "Untriggered",
                "tp_trigger_by": "UNKNOWN",
                "sl_trigger_by": "UNKNOWN",
                "price": "0",
                "qty": "0.006",
                "order_link_id": "",
                "reduce_only": True,
                "close_on_trigger": True,
                "take_profit": "0",
                "stop_loss": "0",
                "created_time": "2022-12-01T14:44:54.000Z",
                "updated_time": "2022-12-01T14:44:54.000Z",
            },
            "id": "71830ad6-5f0d-410c-a0fc-82deb1b7b989",
            "clientOrderId": None,
            "timestamp": 1669905894000,
            "datetime": "2022-12-01T15:39:15.000Z",
            "lastTradeTimestamp": 1669905894000,
            "symbol": "BTC/USDT",
            "type": "market",
            "timeInForce": "IOC",
            "postOnly": False,
            "side": "buy",
            "price": None,
            "stopPrice": "17170",
            "amount": 0.006,
            "cost": None,
            "average": None,
            "filled": None,
            "remaining": None,
            "status": "open",
            "fee": None,
            "trades": [],
            "fees": [],
        },
    ]


def get_parsed_canceled_orders():
    return [
        {
            ExchangeConstantsOrderColumns.ID.value: "da13fb16-daa0-4520-bc01-52a4103c50ca",
            ExchangeConstantsOrderColumns.STATUS.value: OrderStatus.CANCELED.value,
            ExchangeConstantsOrderColumns.TIMESTAMP.value: 1669156312,
            ExchangeConstantsOrderColumns.SYMBOL.value: "BTC/USDT",
            ExchangeConstantsOrderColumns.SIDE.value: TradeOrderSide.SELL.value,
            ExchangeConstantsOrderColumns.TYPE.value: TradeOrderType.LIMIT.value,
            ExchangeConstantsOrderColumns.OCTOBOT_ORDER_TYPE.value: TraderOrderType.SELL_LIMIT.value,
            ExchangeConstantsOrderColumns.TAKER_OR_MAKER.value: ExchangeConstantsMarketPropertyColumns.MAKER.value,
            ExchangeConstantsOrderColumns.PRICE.value: decimal.Decimal("17349.0"),
            ExchangeConstantsOrderColumns.FILLED_PRICE.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.AVERAGE.value: decimal.Decimal("17349.0"),
            ExchangeConstantsOrderColumns.AMOUNT.value: decimal.Decimal("0.004"),
            ExchangeConstantsOrderColumns.REMAINING.value: decimal.Decimal("0.004"),
            ExchangeConstantsOrderColumns.FILLED_AMOUNT.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.COST.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.REDUCE_ONLY.value: True,
            ExchangeConstantsOrderColumns.FEE.value: None,
        },
    ]


def get_parsed_open_market_orders():
    return [
        {
            ExchangeConstantsOrderColumns.ID.value: "16b1bf6c-b3eb-4145-9a31-c24e68562d8a",
            ExchangeConstantsOrderColumns.STATUS.value: OrderStatus.OPEN.value,
            ExchangeConstantsOrderColumns.TIMESTAMP.value: 1669905894,
            ExchangeConstantsOrderColumns.SYMBOL.value: "BTC/USDT",
            ExchangeConstantsOrderColumns.SIDE.value: TradeOrderSide.BUY.value,
            ExchangeConstantsOrderColumns.TYPE.value: TradeOrderType.MARKET.value,
            ExchangeConstantsOrderColumns.OCTOBOT_ORDER_TYPE.value: TraderOrderType.BUY_MARKET.value,
            ExchangeConstantsOrderColumns.TAKER_OR_MAKER.value: ExchangeConstantsMarketPropertyColumns.TAKER.value,
            ExchangeConstantsOrderColumns.PRICE.value: decimal.Decimal("17964.5"),
            ExchangeConstantsOrderColumns.FILLED_PRICE.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.AVERAGE.value: decimal.Decimal("17964.5"),
            ExchangeConstantsOrderColumns.AMOUNT.value: decimal.Decimal("0.006"),
            ExchangeConstantsOrderColumns.REMAINING.value: decimal.Decimal("0.006"),
            ExchangeConstantsOrderColumns.FILLED_AMOUNT.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.COST.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.REDUCE_ONLY.value: False,
            ExchangeConstantsOrderColumns.FEE.value: None,
        }
    ]


def get_parsed_open_long_limit_tp_orders():
    return [
        {
            ExchangeConstantsOrderColumns.ID.value: "f9bcf5e1-004f-44d3-9487-901b982d4c62",
            ExchangeConstantsOrderColumns.STATUS.value: OrderStatus.OPEN.value,
            ExchangeConstantsOrderColumns.TIMESTAMP.value: 1669906989,
            ExchangeConstantsOrderColumns.SYMBOL.value: "BTC/USDT",
            ExchangeConstantsOrderColumns.SIDE.value: TradeOrderSide.SELL.value,
            ExchangeConstantsOrderColumns.TYPE.value: TradeOrderType.LIMIT.value,
            ExchangeConstantsOrderColumns.OCTOBOT_ORDER_TYPE.value: TraderOrderType.SELL_LIMIT.value,
            ExchangeConstantsOrderColumns.TAKER_OR_MAKER.value: ExchangeConstantsMarketPropertyColumns.MAKER.value,
            ExchangeConstantsOrderColumns.PRICE.value: decimal.Decimal("18394.0"),
            ExchangeConstantsOrderColumns.FILLED_PRICE.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.AVERAGE.value: decimal.Decimal("18394.0"),
            ExchangeConstantsOrderColumns.AMOUNT.value: decimal.Decimal("0.006"),
            ExchangeConstantsOrderColumns.REMAINING.value: decimal.Decimal("0.006"),
            ExchangeConstantsOrderColumns.FILLED_AMOUNT.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.COST.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.REDUCE_ONLY.value: True,
            ExchangeConstantsOrderColumns.FEE.value: None,
        }
    ]


def get_parsed_open_short_limit_tp_orders():
    return [
        {
            ExchangeConstantsOrderColumns.ID.value: "de11a287-24cd-421a-ade8-8888f336779a",
            ExchangeConstantsOrderColumns.STATUS.value: OrderStatus.OPEN.value,
            ExchangeConstantsOrderColumns.TIMESTAMP.value: 1669909167,
            ExchangeConstantsOrderColumns.SYMBOL.value: "BTC/USDT",
            ExchangeConstantsOrderColumns.SIDE.value: TradeOrderSide.BUY.value,
            ExchangeConstantsOrderColumns.TYPE.value: TradeOrderType.LIMIT.value,
            ExchangeConstantsOrderColumns.OCTOBOT_ORDER_TYPE.value: TraderOrderType.BUY_LIMIT.value,
            ExchangeConstantsOrderColumns.TAKER_OR_MAKER.value: ExchangeConstantsMarketPropertyColumns.MAKER.value,
            ExchangeConstantsOrderColumns.PRICE.value: decimal.Decimal("15785.5"),
            ExchangeConstantsOrderColumns.FILLED_PRICE.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.AVERAGE.value: decimal.Decimal("15785.5"),
            ExchangeConstantsOrderColumns.AMOUNT.value: decimal.Decimal("0.006"),
            ExchangeConstantsOrderColumns.REMAINING.value: decimal.Decimal("0.006"),
            ExchangeConstantsOrderColumns.FILLED_AMOUNT.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.COST.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.REDUCE_ONLY.value: True,
            ExchangeConstantsOrderColumns.FEE.value: None,
        },
    ]


def get_parsed_open_short_sl_orders():
    return [
        {
            ExchangeConstantsOrderColumns.ID.value: "71830ad6-5f0d-410c-a0fc-82deb1b7b989",
            ExchangeConstantsOrderColumns.STATUS.value: OrderStatus.OPEN.value,
            ExchangeConstantsOrderColumns.TIMESTAMP.value: 1669905894,
            ExchangeConstantsOrderColumns.SYMBOL.value: "BTC/USDT",
            ExchangeConstantsOrderColumns.SIDE.value: TradeOrderSide.BUY.value,
            ExchangeConstantsOrderColumns.TYPE.value: TradeOrderType.STOP_LOSS.value,
            ExchangeConstantsOrderColumns.OCTOBOT_ORDER_TYPE.value: TraderOrderType.STOP_LOSS.value,
            ExchangeConstantsOrderColumns.TAKER_OR_MAKER.value: ExchangeConstantsMarketPropertyColumns.TAKER.value,
            ExchangeConstantsOrderColumns.PRICE.value: decimal.Decimal("17170"),
            ExchangeConstantsOrderColumns.FILLED_PRICE.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.AVERAGE.value: decimal.Decimal("17170"),
            ExchangeConstantsOrderColumns.AMOUNT.value: decimal.Decimal("0.006"),
            ExchangeConstantsOrderColumns.REMAINING.value: decimal.Decimal("0.006"),
            ExchangeConstantsOrderColumns.FILLED_AMOUNT.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.COST.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.REDUCE_ONLY.value: True,
            ExchangeConstantsOrderColumns.FEE.value: None,
        },
    ]


def get_parsed_open_long_sl_orders():
    return [
        {
            ExchangeConstantsOrderColumns.ID.value: "71830ad6-5f0d-410c-a0fc-82deb1b7b989",
            ExchangeConstantsOrderColumns.STATUS.value: OrderStatus.OPEN.value,
            ExchangeConstantsOrderColumns.TIMESTAMP.value: 1669905894,
            ExchangeConstantsOrderColumns.SYMBOL.value: "BTC/USDT",
            ExchangeConstantsOrderColumns.SIDE.value: TradeOrderSide.SELL.value,
            ExchangeConstantsOrderColumns.TYPE.value: TradeOrderType.STOP_LOSS.value,
            ExchangeConstantsOrderColumns.OCTOBOT_ORDER_TYPE.value: TraderOrderType.STOP_LOSS.value,
            ExchangeConstantsOrderColumns.TAKER_OR_MAKER.value: ExchangeConstantsMarketPropertyColumns.TAKER.value,
            ExchangeConstantsOrderColumns.PRICE.value: decimal.Decimal("16938"),
            ExchangeConstantsOrderColumns.FILLED_PRICE.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.AVERAGE.value: decimal.Decimal("16938"),
            ExchangeConstantsOrderColumns.AMOUNT.value: decimal.Decimal("0.006"),
            ExchangeConstantsOrderColumns.REMAINING.value: decimal.Decimal("0.006"),
            ExchangeConstantsOrderColumns.FILLED_AMOUNT.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.COST.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.REDUCE_ONLY.value: True,
            ExchangeConstantsOrderColumns.FEE.value: None,
        }
    ]


async def test_parse_default_canceled_orders(
    raw_canceled_orders=get_raw_canceled_orders(),
):
    just_parsed_orders = await active_parser(raw_canceled_orders)
    assert get_parsed_canceled_orders() == just_parsed_orders


async def test_parse_default_open_market_orders(
    raw_open_market_orders=get_raw_open_market_orders(),
):
    just_parsed_orders = await active_parser(raw_open_market_orders)
    assert get_parsed_open_market_orders() == just_parsed_orders


async def test_parse_default_open_long_limit_tp_orders(
    raw_open_long_limit_tp_orders=get_raw_open_long_limit_tp_orders(),
):
    just_parsed_orders = await active_parser(raw_open_long_limit_tp_orders)
    assert get_parsed_open_long_limit_tp_orders() == just_parsed_orders


async def test_parse_default_open_short_limit_tp_orders(
    raw_open_short_limit_tp_orders=get_raw_open_short_limit_tp_orders(),
):
    just_parsed_orders = await active_parser(raw_open_short_limit_tp_orders)
    assert get_parsed_open_short_limit_tp_orders() == just_parsed_orders


async def test_parse_default_open_long_sl_orders(
    raw_open_long_sl_orders=get_raw_open_long_sl_orders(),
):
    just_parsed_orders = await active_parser(raw_open_long_sl_orders)
    assert get_parsed_open_long_sl_orders() == just_parsed_orders


async def test_parse_default_open_short_sl_orders(
    raw_open_short_sl_orders=get_raw_open_short_sl_orders(),
):
    just_parsed_orders = await active_parser(raw_open_short_sl_orders)
    assert get_parsed_open_short_sl_orders() == just_parsed_orders


def test_cryptofeed_constants_change():
    # update orders parser if it fails
    assert cryptofeed_constants.OPEN == 'open'
    assert cryptofeed_constants.PENDING == 'pending'
    assert cryptofeed_constants.FILLED == 'filled'
    assert cryptofeed_constants.PARTIAL == 'partial'
    assert cryptofeed_constants.CANCELLED == 'cancelled'
    assert cryptofeed_constants.UNFILLED == 'unfilled'
    assert cryptofeed_constants.EXPIRED == 'expired'
    assert cryptofeed_constants.SUSPENDED == 'suspended'
    assert cryptofeed_constants.FAILED == 'failed'
    assert cryptofeed_constants.SUBMITTING == 'submitting'
    assert cryptofeed_constants.CANCELLING == 'cancelling'
    assert cryptofeed_constants.CLOSED == 'closed'
    
    
def test_cryptofeed_order_types_constants_change():
    # update orders parser if it fails
    assert cryptofeed_constants.LIMIT == 'limit'
    assert cryptofeed_constants.MARKET == 'market'
    assert cryptofeed_constants.STOP_LIMIT == 'stop-limit'
    assert cryptofeed_constants.STOP_MARKET == 'stop-market'
    assert cryptofeed_constants.MAKER_OR_CANCEL == 'maker-or-cancel'
    assert cryptofeed_constants.FILL_OR_KILL == 'fill-or-kill'
    assert cryptofeed_constants.IMMEDIATE_OR_CANCEL == 'immediate-or-cancel'
    assert cryptofeed_constants.GOOD_TIL_CANCELED == 'good-til-canceled'
    assert cryptofeed_constants.TRIGGER_LIMIT == 'trigger-limit'
    assert cryptofeed_constants.TRIGGER_MARKET == 'trigger-market'
    assert cryptofeed_constants.MARGIN_LIMIT == 'margin-limit'
    assert cryptofeed_constants.MARGIN_MARKET == 'margin-market'
    