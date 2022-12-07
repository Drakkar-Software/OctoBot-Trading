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
from octobot_trading.enums import (
    ExchangeConstantsFeesColumns,
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
    return parser.TradesParser(exchange=mock_abstract_exchange())


def active_parser(raw_records):
    _parser = active_parser_class()
    return _parser.parse_trades(raw_records)


def get_raw_trades():
    return [
        {
            "id": "761324763710",
            "info": {
                "id": "761324763710",
                "symbol": "BTCUSDT",
                "price": "17171.5",
                "qty": "0.055",
                "side": "Buy",
                "time": "2022-12-01T13:19:24.000Z",
                "trade_time_ms": "1669900764278",
                "is_block_trade": False,
            },
            "timestamp": 1669900764000,
            "datetime": "2022-12-01T13:19:24.000Z",
            "symbol": "BTC/USDT",
            "order": None,
            "type": None,
            "side": "buy",
            "takerOrMaker": "taker",
            "price": 17171.5,
            "amount": 0.055,
            "cost": 944.4325,
            "fees": [{"code": "USDT", "cost": -0.015922}],
            "fee": {},
        }
    ]


def get_parsed_trades():
    return [
        {
           ExchangeConstantsOrderColumns.ID.value: "761324763710",
           ExchangeConstantsOrderColumns.STATUS.value: OrderStatus.CLOSED.value,
           ExchangeConstantsOrderColumns.TIMESTAMP.value: 1669900764,
           ExchangeConstantsOrderColumns.SYMBOL.value: "BTC/USDT",
           ExchangeConstantsOrderColumns.SIDE.value: TradeOrderSide.BUY.value,
           ExchangeConstantsOrderColumns.TYPE.value: TradeOrderType.MARKET.value,
           ExchangeConstantsOrderColumns.OCTOBOT_ORDER_TYPE.value: TraderOrderType.BUY_MARKET.value,
           ExchangeConstantsOrderColumns.TAKER_OR_MAKER.value: ExchangeConstantsMarketPropertyColumns.TAKER.value,
           ExchangeConstantsOrderColumns.PRICE.value: decimal.Decimal("17171.5"),
           ExchangeConstantsOrderColumns.FILLED_PRICE.value: decimal.Decimal("17171.5"),
           ExchangeConstantsOrderColumns.AVERAGE.value: decimal.Decimal("17171.5"),
           ExchangeConstantsOrderColumns.AMOUNT.value: decimal.Decimal("0.055"),
           ExchangeConstantsOrderColumns.REMAINING.value: decimal.Decimal("0"),
           ExchangeConstantsOrderColumns.FILLED_AMOUNT.value: decimal.Decimal("0.055"),
           ExchangeConstantsOrderColumns.COST.value: decimal.Decimal("944.4325"),
           ExchangeConstantsOrderColumns.REDUCE_ONLY.value: None,
           ExchangeConstantsOrderColumns.FEE.value: {
                ExchangeConstantsFeesColumns.COST.value: -0.015922,
                ExchangeConstantsFeesColumns.CURRENCY.value: "USDT",
            },
        }
    ]


async def test_parse_default_trade():
    just_parsed_trades = await active_parser(get_raw_trades())
    assert get_parsed_trades() == just_parsed_trades
