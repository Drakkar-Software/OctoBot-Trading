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
import cryptofeed.defines as cryptofeed_constants
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
    ExchangeOrderCCXTColumns as CCXTOrderCols,
)
import octobot_trading.exchanges.parser as parser
from .parser_tests_util import (
    mock_abstract_exchange,
)

pytestmark = pytest.mark.asyncio


def ccxt_generic_parser_class():
    return parser.GenericCCXTTradesParser(exchange=mock_abstract_exchange())


def ccxt_generic_parser(raw_records):
    _parser = ccxt_generic_parser_class()
    return _parser.parse_trades(raw_records)


def ccxt_parser_class():
    return parser.CCXTTradesParser(exchange=mock_abstract_exchange())


def ccxt_parser(raw_records):
    _parser = ccxt_parser_class()
    return _parser.parse_trades(raw_records)


def base_parser_class():
    _parser = parser.TradesParser(exchange=mock_abstract_exchange())
    _parser.USE_INFO_SUB_DICT_FOR_REDUCE_ONLY: bool = True
    _parser.TIMESTAMP_KEYS: list = [CCXTOrderCols.TIMESTAMP.value]
    _parser.STATUS_KEYS: list = [CCXTOrderCols.STATUS.value]
    _parser.ID_KEYS: list = [CCXTOrderCols.ID.value]
    _parser.SYMBOL_KEYS: list = [CCXTOrderCols.SYMBOL.value]
    _parser.SIDE_KEYS: list = [CCXTOrderCols.SIDE.value]
    _parser.TYPE_KEYS: list = [CCXTOrderCols.TYPE.value]
    _parser.TAKER_OR_MAKER_KEYS: list = [CCXTOrderCols.TAKER_OR_MAKER.value]
    _parser.PRICE_KEYS: list = [
        CCXTOrderCols.AVERAGE.value,  # first try average as its more accurate
        CCXTOrderCols.PRICE.value,
        CCXTOrderCols.STOP_PRICE.value,  # use only if others are missing
    ]
    _parser.FILLED_PRICE_KEYS: list = [CCXTOrderCols.AVERAGE.value] 
    _parser.AMOUNT_KEYS: list = [CCXTOrderCols.AMOUNT.value]
    _parser.REMAINING_KEYS: list = [CCXTOrderCols.REMAINING.value]
    _parser.FILLED_AMOUNT_KEYS: list = []  # todo
    _parser.COST_KEYS: list = [CCXTOrderCols.COST.value]
    _parser.REDUCE_ONLY_KEYS: list = [CCXTOrderCols.REDUCE_ONLY.value]
    _parser.TIME_IN_FORCE_KEYS: list = []
    _parser.TAG_KEYS: list = [CCXTOrderCols.TAG.value]
    _parser.FEE_KEYS: list = [CCXTOrderCols.FEE, CCXTOrderCols.FEES.value]
    _parser.QUANTITY_CURRENCY_KEYS: list = [CCXTOrderCols.QUANTITY_CURRENCY.value]
    return _parser


def base_parser(raw_records):
    _parser = base_parser_class()
    return _parser.parse_trades(raw_records)


def crypto_feed_parser_class():
    return parser.CryptoFeedTradesParser(exchange=mock_abstract_exchange())


def crypto_feed_parser(raw_record):
    _parser = crypto_feed_parser_class()
    return _parser.parse_trade(raw_record)


class CryptoFeedTradeMock:
    id = "761324763710"
    timestamp = 1669900764000
    symbol = "BTC/USDT"
    type = cryptofeed_constants.MARKET
    side = cryptofeed_constants.BUY
    price = 17171.5
    amount = 0.055
    remaining = 0
    status = cryptofeed_constants.CLOSED


def get_raw_trades():
    return [
        {
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
            CCXTOrderCols.ID.value: "761324763710",
            CCXTOrderCols.TIMESTAMP.value: 1669900764000,
            CCXTOrderCols.DATETIME.value: "2022-12-01T13:19:24.000Z",
            CCXTOrderCols.SYMBOL.value: "BTC/USDT",
            CCXTOrderCols.ORDER.value: None,
            CCXTOrderCols.TYPE.value: None,
            CCXTOrderCols.SIDE.value: "buy",
            CCXTOrderCols.TAKER_OR_MAKER.value: "taker",
            CCXTOrderCols.PRICE.value: 17171.5,
            CCXTOrderCols.AMOUNT.value: 0.055,
            CCXTOrderCols.COST.value: 944.4325,
            CCXTOrderCols.FEES.value: [{"code": "USDT", "cost": -0.015922}],
            CCXTOrderCols.FEE.value: {},
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
            ExchangeConstantsOrderColumns.TYPE.value: TraderOrderType.BUY_MARKET.value,
            ExchangeConstantsOrderColumns.TAKER_OR_MAKER.value: ExchangeConstantsMarketPropertyColumns.TAKER.value,
            ExchangeConstantsOrderColumns.PRICE.value: decimal.Decimal("17171.5"),
            ExchangeConstantsOrderColumns.FILLED_PRICE.value: decimal.Decimal(
                "17171.5"
            ),
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


async def test_base_parser_default_trade():
    just_parsed_trades = await base_parser(get_raw_trades())
    assert get_parsed_trades() == just_parsed_trades


async def test_ccxt_parser_default_trade():
    just_parsed_trades = await ccxt_parser(get_raw_trades())
    assert get_parsed_trades() == just_parsed_trades


async def test_ccxt_generic_parser_default_trade():
    just_parsed_trades = await ccxt_generic_parser(get_raw_trades())
    assert get_parsed_trades() == just_parsed_trades


async def test_crypto_feed_parser_default_trade():
    just_parsed_trades = await crypto_feed_parser(CryptoFeedTradeMock)
    should_be_trade = get_parsed_trades()[0]
    should_be_trade.pop(ExchangeConstantsOrderColumns.FEE.value)
    should_be_trade.pop(ExchangeConstantsOrderColumns.COST.value)
    assert should_be_trade == just_parsed_trades
