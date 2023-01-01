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
    _parser = parser.GenericCCXTOrdersParser(exchange=mock_abstract_exchange())
    _parser.MARKET_ORDERS_WITH_STOP_PRICE_ARE_STOP_ORDERS = True
    return _parser


def ccxt_generic_parser(raw_records):
    _parser = ccxt_generic_parser_class()
    return _parser.parse_orders(raw_records)


def ccxt_parser_class():
    return parser.CCXTOrdersParser(exchange=mock_abstract_exchange())


def ccxt_parser(raw_records):
    _parser = ccxt_parser_class()
    _parser.USE_INFO_SUB_DICT_FOR_REDUCE_ONLY: bool = True
    return _parser.parse_orders(raw_records)


def crypto_feed_parser_class():
    return parser.CryptoFeedOrdersParser(exchange=mock_abstract_exchange())


def crypto_feed_parser(raw_record):
    _parser = crypto_feed_parser_class()
    return _parser.parse_order(raw_record)


def base_parser_class():
    _parser = parser.OrdersParser(exchange=mock_abstract_exchange())
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
    _parser.AMOUNT_KEYS: list = [CCXTOrderCols.AMOUNT.value]
    _parser.REMAINING_KEYS: list = [CCXTOrderCols.REMAINING.value]
    _parser.COST_KEYS: list = [CCXTOrderCols.COST.value]
    _parser.REDUCE_ONLY_KEYS: list = [CCXTOrderCols.REDUCE_ONLY.value]
    _parser.TAG_KEYS: list = [CCXTOrderCols.TAG.value]
    _parser.FEE_KEYS: list = [CCXTOrderCols.FEE, CCXTOrderCols.FEES.value]
    _parser.QUANTITY_CURRENCY_KEYS: list = [CCXTOrderCols.QUANTITY_CURRENCY.value]
    return _parser


def base_parser(raw_records):
    _parser = base_parser_class()
    return _parser.parse_orders(raw_records)


class CryptoFeedOrderCancelledMock:
    id = "da13fb16-daa0-4520-bc01-52a4103c50ca"
    timestamp = 1669156312000
    symbol = "BTC/USDT"
    type = cryptofeed_constants.LIMIT
    side = cryptofeed_constants.SELL
    price = 17349.0
    amount = 0.004
    remaining = 0.004
    status = cryptofeed_constants.CANCELLED


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
                CCXTOrderCols.REDUCE_ONLY.value: True,
                "close_on_trigger": True,
                "take_profit": "0",
                "stop_loss": "0",
                "created_time": "2022-11-22T22:31:52Z",
                "updated_time": "2022-11-22T22:45:34Z",
            },
            CCXTOrderCols.ID.value: "da13fb16-daa0-4520-bc01-52a4103c50ca",
            CCXTOrderCols.TIMESTAMP.value: 1669156312000,
            CCXTOrderCols.DATETIME.value: "2022-11-22T22:31:52.000Z",
            CCXTOrderCols.LAST_TRADE_TIMESTAMP.value: 1669157134000,
            CCXTOrderCols.SYMBOL.value: "BTC/USDT",
            CCXTOrderCols.TYPE.value: "limit",
            CCXTOrderCols.SIDE.value: "sell",
            CCXTOrderCols.PRICE.value: 17349.0,
            CCXTOrderCols.STOP_PRICE.value: None,
            CCXTOrderCols.AMOUNT.value: 0.004,
            CCXTOrderCols.COST.value: 0.0,
            CCXTOrderCols.AVERAGE.value: None,
            CCXTOrderCols.FILLED.value: 0.0,
            CCXTOrderCols.REMAINING.value: 0.004,
            CCXTOrderCols.STATUS.value: "canceled",
            CCXTOrderCols.FEE.value: {"cost": 0.0, "currency": "USDT"},
            CCXTOrderCols.TRADES.value: [],
            CCXTOrderCols.FEES.value: [{"cost": 0.0, "currency": "USDT"}],
        }
    ]


class CryptoFeedOrderOpenMarketMock:
    id = "16b1bf6c-b3eb-4145-9a31-c24e68562d8a"
    timestamp = 1669905894000
    symbol = "BTC/USDT"
    type = cryptofeed_constants.MARKET
    side = cryptofeed_constants.BUY
    price = 17964.5
    amount = 0.006
    remaining = 0.006
    status = cryptofeed_constants.OPEN


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
                CCXTOrderCols.REDUCE_ONLY.value: False,
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
            CCXTOrderCols.ID.value: "16b1bf6c-b3eb-4145-9a31-c24e68562d8a",
            CCXTOrderCols.TIMESTAMP.value: 1669905894000,
            CCXTOrderCols.DATETIME.value: "2022-12-01T14:44:54.000Z",
            CCXTOrderCols.LAST_TRADE_TIMESTAMP.value: 1669905894000,
            CCXTOrderCols.SYMBOL.value: "BTC/USDT",
            CCXTOrderCols.TYPE.value: "market",
            CCXTOrderCols.SIDE.value: "buy",
            CCXTOrderCols.PRICE.value: 17964.5,
            CCXTOrderCols.STOP_PRICE.value: None,
            CCXTOrderCols.AMOUNT.value: 0.006,
            CCXTOrderCols.COST.value: 0.0,
            CCXTOrderCols.AVERAGE.value: None,
            CCXTOrderCols.FILLED.value: 0.0,
            CCXTOrderCols.REMAINING.value: 0.006,
            CCXTOrderCols.STATUS.value: "open",
            CCXTOrderCols.FEE.value: {"cost": 0.0, "currency": "USDT"},
            CCXTOrderCols.TRADES.value: [],
            CCXTOrderCols.FEES.value: [{"cost": 0.0, "currency": "USDT"}],
        },
    ]


class CryptoFeedOrderLongLimitTPMock:
    id = "f9bcf5e1-004f-44d3-9487-901b982d4c62"
    timestamp = 1669906989000
    symbol = "BTC/USDT"
    type = cryptofeed_constants.LIMIT
    side = cryptofeed_constants.SELL
    price = 18394.0
    amount = 0.006
    remaining = 0.006
    status = cryptofeed_constants.OPEN


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
                CCXTOrderCols.REDUCE_ONLY.value: True,
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
            CCXTOrderCols.ID.value: "f9bcf5e1-004f-44d3-9487-901b982d4c62",
            CCXTOrderCols.TIMESTAMP.value: 1669906989000,
            CCXTOrderCols.DATETIME.value: "2022-12-01T15:03:09.000Z",
            CCXTOrderCols.LAST_TRADE_TIMESTAMP.value: 1669906989000,
            CCXTOrderCols.SYMBOL.value: "BTC/USDT",
            CCXTOrderCols.TYPE.value: "limit",
            CCXTOrderCols.SIDE.value: "sell",
            CCXTOrderCols.PRICE.value: 18394.0,
            CCXTOrderCols.STOP_PRICE.value: None,
            CCXTOrderCols.AMOUNT.value: 0.006,
            CCXTOrderCols.COST.value: 0.0,
            CCXTOrderCols.AVERAGE.value: None,
            CCXTOrderCols.FILLED.value: 0.0,
            CCXTOrderCols.REMAINING.value: 0.006,
            CCXTOrderCols.STATUS.value: "open",
            CCXTOrderCols.FEE.value: {"cost": 0.0, "currency": "USDT"},
            CCXTOrderCols.TRADES.value: [],
            CCXTOrderCols.FEES.value: [{"cost": 0.0, "currency": "USDT"}],
        },
    ]


class CryptoFeedOrderShortLimitTPMock:
    id = "de11a287-24cd-421a-ade8-8888f336779a"
    timestamp = 1669909167000
    symbol = "BTC/USDT"
    type = cryptofeed_constants.LIMIT
    side = cryptofeed_constants.BUY
    price = 15785.5
    amount = 0.006
    remaining = 0.006
    status = cryptofeed_constants.OPEN


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
                CCXTOrderCols.REDUCE_ONLY.value: True,
                "close_on_trigger": True,
                "take_profit": "0",
                "stop_loss": "0",
                "created_time": "2022-12-01T15:03:09Z",
                "updated_time": "2022-12-01T15:03:09Z",
            },
            CCXTOrderCols.ID.value: "de11a287-24cd-421a-ade8-8888f336779a",
            CCXTOrderCols.TIMESTAMP.value: 1669909167000,
            CCXTOrderCols.DATETIME.value: "2022-12-01T15:39:27.000Z",
            CCXTOrderCols.LAST_TRADE_TIMESTAMP.value: 1669909167000,
            CCXTOrderCols.SYMBOL.value: "BTC/USDT",
            CCXTOrderCols.TYPE.value: "limit",
            CCXTOrderCols.SIDE.value: "buy",
            CCXTOrderCols.PRICE.value: 15785.5,
            CCXTOrderCols.STOP_PRICE.value: None,
            CCXTOrderCols.AMOUNT.value: 0.006,
            CCXTOrderCols.COST.value: 0.0,
            CCXTOrderCols.AVERAGE.value: None,
            CCXTOrderCols.FILLED.value: 0.0,
            CCXTOrderCols.REMAINING.value: 0.006,
            CCXTOrderCols.STATUS.value: "open",
            CCXTOrderCols.FEE.value: {"cost": 0.0, "currency": "USDT"},
            CCXTOrderCols.TRADES.value: [],
            CCXTOrderCols.FEES.value: [{"cost": 0.0, "currency": "USDT"}],
        },
    ]


class CryptoFeedOrderLongSLMock:
    id = "71830ad6-5f0d-410c-a0fc-82deb1b7b989"
    timestamp = 1669905894000
    symbol = "BTC/USDT"
    type = cryptofeed_constants.STOP_MARKET
    side = cryptofeed_constants.SELL
    price = 16938
    amount = 0.006
    remaining = 0.006
    status = cryptofeed_constants.OPEN


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
                CCXTOrderCols.REDUCE_ONLY.value: True,
                "close_on_trigger": True,
                "take_profit": "0",
                "stop_loss": "0",
                "created_time": "2022-12-01T14:44:54.000Z",
                "updated_time": "2022-12-01T14:44:54.000Z",
            },
            CCXTOrderCols.ID.value: "71830ad6-5f0d-410c-a0fc-82deb1b7b989",
            CCXTOrderCols.TIMESTAMP.value: 1669905894000,
            CCXTOrderCols.DATETIME.value: "2022-12-01T14:44:54.000Z",
            CCXTOrderCols.LAST_TRADE_TIMESTAMP.value: 1669905894000,
            CCXTOrderCols.SYMBOL.value: "BTC/USDT",
            CCXTOrderCols.TYPE.value: "market",
            CCXTOrderCols.SIDE.value: "sell",
            CCXTOrderCols.PRICE.value: None,
            CCXTOrderCols.STOP_PRICE.value: "16938",
            CCXTOrderCols.AMOUNT.value: 0.006,
            CCXTOrderCols.COST.value: None,
            CCXTOrderCols.AVERAGE.value: None,
            CCXTOrderCols.FILLED.value: None,
            CCXTOrderCols.REMAINING.value: None,
            CCXTOrderCols.STATUS.value: "open",
            CCXTOrderCols.FEE.value: None,
            CCXTOrderCols.TRADES.value: [],
            CCXTOrderCols.FEES.value: [],
        },
    ]


class CryptoFeedOrderShortSLMock:
    id = "71830ad6-5f0d-410c-a0fc-82deb1b7b989"
    timestamp = 1669905894000
    symbol = "BTC/USDT"
    type = cryptofeed_constants.STOP_MARKET
    side = cryptofeed_constants.BUY
    price = 17170
    amount = 0.006
    remaining = 0.006
    status = cryptofeed_constants.OPEN


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
                CCXTOrderCols.REDUCE_ONLY.value: True,
                "close_on_trigger": True,
                "take_profit": "0",
                "stop_loss": "0",
                "created_time": "2022-12-01T14:44:54.000Z",
                "updated_time": "2022-12-01T14:44:54.000Z",
            },
            CCXTOrderCols.ID.value: "71830ad6-5f0d-410c-a0fc-82deb1b7b989",
            CCXTOrderCols.TIMESTAMP.value: 1669905894000,
            CCXTOrderCols.DATETIME.value: "2022-12-01T15:39:15.000Z",
            CCXTOrderCols.LAST_TRADE_TIMESTAMP.value: 1669905894000,
            CCXTOrderCols.SYMBOL.value: "BTC/USDT",
            CCXTOrderCols.TYPE.value: "market",
            CCXTOrderCols.SIDE.value: "buy",
            CCXTOrderCols.PRICE.value: None,
            CCXTOrderCols.STOP_PRICE.value: "17170",
            CCXTOrderCols.AMOUNT.value: 0.006,
            CCXTOrderCols.COST.value: None,
            CCXTOrderCols.AVERAGE.value: None,
            CCXTOrderCols.FILLED.value: None,
            CCXTOrderCols.REMAINING.value: None,
            CCXTOrderCols.STATUS.value: "open",
            CCXTOrderCols.FEE.value: None,
            CCXTOrderCols.TRADES.value: [],
            CCXTOrderCols.FEES.value: [],
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
            ExchangeConstantsOrderColumns.TYPE.value: TraderOrderType.SELL_LIMIT.value,
            ExchangeConstantsOrderColumns.TAKER_OR_MAKER.value: ExchangeConstantsMarketPropertyColumns.MAKER.value,
            ExchangeConstantsOrderColumns.PRICE.value: decimal.Decimal("17349.0"),
            ExchangeConstantsOrderColumns.FILLED_PRICE.value: decimal.Decimal("0"),
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
            ExchangeConstantsOrderColumns.TYPE.value: TraderOrderType.BUY_MARKET.value,
            ExchangeConstantsOrderColumns.TAKER_OR_MAKER.value: ExchangeConstantsMarketPropertyColumns.TAKER.value,
            ExchangeConstantsOrderColumns.PRICE.value: decimal.Decimal("17964.5"),
            ExchangeConstantsOrderColumns.FILLED_PRICE.value: decimal.Decimal("0"),
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
            ExchangeConstantsOrderColumns.TYPE.value: TraderOrderType.SELL_LIMIT.value,
            ExchangeConstantsOrderColumns.TAKER_OR_MAKER.value: ExchangeConstantsMarketPropertyColumns.MAKER.value,
            ExchangeConstantsOrderColumns.PRICE.value: decimal.Decimal("18394.0"),
            ExchangeConstantsOrderColumns.FILLED_PRICE.value: decimal.Decimal("0"),
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
            ExchangeConstantsOrderColumns.TYPE.value: TraderOrderType.BUY_LIMIT.value,
            ExchangeConstantsOrderColumns.TAKER_OR_MAKER.value: ExchangeConstantsMarketPropertyColumns.MAKER.value,
            ExchangeConstantsOrderColumns.PRICE.value: decimal.Decimal("15785.5"),
            ExchangeConstantsOrderColumns.FILLED_PRICE.value: decimal.Decimal("0"),
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
            ExchangeConstantsOrderColumns.TYPE.value: TraderOrderType.STOP_LOSS.value,
            ExchangeConstantsOrderColumns.TAKER_OR_MAKER.value: ExchangeConstantsMarketPropertyColumns.TAKER.value,
            ExchangeConstantsOrderColumns.PRICE.value: decimal.Decimal("17170"),
            ExchangeConstantsOrderColumns.FILLED_PRICE.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.AMOUNT.value: decimal.Decimal("0.006"),
            ExchangeConstantsOrderColumns.REMAINING.value: decimal.Decimal("0.006"),
            ExchangeConstantsOrderColumns.FILLED_AMOUNT.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.COST.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.REDUCE_ONLY.value: True,
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
            ExchangeConstantsOrderColumns.TYPE.value: TraderOrderType.STOP_LOSS.value,
            ExchangeConstantsOrderColumns.TAKER_OR_MAKER.value: ExchangeConstantsMarketPropertyColumns.TAKER.value,
            ExchangeConstantsOrderColumns.PRICE.value: decimal.Decimal("16938"),
            ExchangeConstantsOrderColumns.FILLED_PRICE.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.AMOUNT.value: decimal.Decimal("0.006"),
            ExchangeConstantsOrderColumns.REMAINING.value: decimal.Decimal("0.006"),
            ExchangeConstantsOrderColumns.FILLED_AMOUNT.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.COST.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.REDUCE_ONLY.value: True,
        }
    ]


async def test_ccxt_parse_default_open_market_orders(
    raw_open_market_orders=get_raw_open_market_orders(),
):
    just_parsed_orders = await ccxt_parser(raw_open_market_orders)
    assert get_parsed_open_market_orders() == just_parsed_orders


async def test_ccxt_generic_parse_default_open_market_orders(
    raw_open_market_orders=get_raw_open_market_orders(),
):
    just_parsed_orders = await ccxt_generic_parser(raw_open_market_orders)
    assert get_parsed_open_market_orders() == just_parsed_orders


async def test_base_parse_default_open_market_orders(
    raw_open_market_orders=get_raw_open_market_orders(),
):
    just_parsed_orders = await base_parser(raw_open_market_orders)
    assert get_parsed_open_market_orders() == just_parsed_orders


async def test_crypto_feed_parse_default_open_market_orders():
    just_parsed_orders = await crypto_feed_parser(CryptoFeedOrderOpenMarketMock)
    should_be_order = get_parsed_open_market_orders()[0]
    should_be_order[ExchangeConstantsOrderColumns.REDUCE_ONLY.value] = None
    should_be_order.pop(ExchangeConstantsOrderColumns.FEE.value)
    should_be_order.pop(ExchangeConstantsOrderColumns.COST.value)
    assert should_be_order == just_parsed_orders


async def test_crypto_feed_parse_default_canceled_orders():
    just_parsed_orders = await crypto_feed_parser(CryptoFeedOrderCancelledMock)
    should_be_order = get_parsed_canceled_orders()[0]
    should_be_order[ExchangeConstantsOrderColumns.REDUCE_ONLY.value] = None
    should_be_order.pop(ExchangeConstantsOrderColumns.FEE.value)
    should_be_order.pop(ExchangeConstantsOrderColumns.COST.value)
    assert should_be_order == just_parsed_orders


async def test_base_parse_default_canceled_orders(
    raw_canceled_orders=get_raw_canceled_orders(),
):
    just_parsed_orders = await base_parser(raw_canceled_orders)
    assert get_parsed_canceled_orders() == just_parsed_orders


async def test_ccxt_parse_default_canceled_orders(
    raw_canceled_orders=get_raw_canceled_orders(),
):
    just_parsed_orders = await ccxt_parser(raw_canceled_orders)
    assert get_parsed_canceled_orders() == just_parsed_orders


async def test_ccxt_generic_parse_default_canceled_orders(
    raw_canceled_orders=get_raw_canceled_orders(),
):
    just_parsed_orders = await ccxt_generic_parser(raw_canceled_orders)
    assert get_parsed_canceled_orders() == just_parsed_orders


async def test_base_parse_default_open_long_limit_tp_orders(
    raw_open_long_limit_tp_orders=get_raw_open_long_limit_tp_orders(),
):
    just_parsed_orders = await base_parser(raw_open_long_limit_tp_orders)
    assert get_parsed_open_long_limit_tp_orders() == just_parsed_orders


async def test_crypto_feed_parse_default_open_long_limit_tp_orders():
    just_parsed_orders = await crypto_feed_parser(CryptoFeedOrderLongLimitTPMock)
    should_be_order = get_parsed_open_long_limit_tp_orders()[0]
    should_be_order[ExchangeConstantsOrderColumns.REDUCE_ONLY.value] = None
    should_be_order.pop(ExchangeConstantsOrderColumns.FEE.value)
    should_be_order.pop(ExchangeConstantsOrderColumns.COST.value)
    assert should_be_order == just_parsed_orders


async def test_ccxt_parse_default_open_long_limit_tp_orders(
    raw_open_long_limit_tp_orders=get_raw_open_long_limit_tp_orders(),
):
    just_parsed_orders = await ccxt_parser(raw_open_long_limit_tp_orders)
    assert get_parsed_open_long_limit_tp_orders() == just_parsed_orders


async def test_ccxt_generic_parse_default_open_long_limit_tp_orders(
    raw_open_long_limit_tp_orders=get_raw_open_long_limit_tp_orders(),
):
    just_parsed_orders = await ccxt_generic_parser(raw_open_long_limit_tp_orders)
    assert get_parsed_open_long_limit_tp_orders() == just_parsed_orders


async def test_base_parse_default_short_limit_tp_orders(
    raw_open_short_limit_tp_orders=get_raw_open_short_limit_tp_orders(),
):
    just_parsed_orders = await base_parser(raw_open_short_limit_tp_orders)
    assert get_parsed_open_short_limit_tp_orders() == just_parsed_orders


async def test_crypto_feed_parse_default_short_limit_tp_orders():
    just_parsed_orders = await crypto_feed_parser(CryptoFeedOrderShortLimitTPMock)
    should_be_order = get_parsed_open_short_limit_tp_orders()[0]
    should_be_order[ExchangeConstantsOrderColumns.REDUCE_ONLY.value] = None
    should_be_order.pop(ExchangeConstantsOrderColumns.FEE.value)
    should_be_order.pop(ExchangeConstantsOrderColumns.COST.value)
    assert should_be_order == just_parsed_orders


async def test_ccxt_parse_default_short_limit_tp_orders(
    raw_open_short_limit_tp_orders=get_raw_open_short_limit_tp_orders(),
):
    just_parsed_orders = await ccxt_parser(raw_open_short_limit_tp_orders)
    assert get_parsed_open_short_limit_tp_orders() == just_parsed_orders


async def test_ccxt_generic_parse_default_short_limit_tp_orders(
    raw_open_short_limit_tp_orders=get_raw_open_short_limit_tp_orders(),
):
    just_parsed_orders = await ccxt_generic_parser(raw_open_short_limit_tp_orders)
    assert get_parsed_open_short_limit_tp_orders() == just_parsed_orders


async def test_base_parse_default_open_long_sl_orders(
    raw_open_long_sl_orders=get_raw_open_long_sl_orders(),
):
    raw_open_long_sl_orders[0][
        CCXTOrderCols.TYPE.value
    ] = TradeOrderType.STOP_LOSS.value
    just_parsed_orders = await base_parser(raw_open_long_sl_orders)
    assert get_parsed_open_long_sl_orders() == just_parsed_orders


async def test_crypto_feed_parse_default_open_long_sl_orders():
    should_be_order = get_parsed_open_long_sl_orders()[0]
    should_be_order.pop(ExchangeConstantsOrderColumns.COST.value)
    just_parsed_order = await crypto_feed_parser(CryptoFeedOrderLongSLMock())
    assert should_be_order == just_parsed_order


async def test_ccxt_parse_default_open_long_sl_orders(
    raw_open_long_sl_orders=get_raw_open_long_sl_orders(),
):
    raw_open_long_sl_orders[0][
        CCXTOrderCols.TYPE.value
    ] = TradeOrderType.STOP_LOSS.value
    raw_open_long_sl_orders[0][
        CCXTOrderCols.PRICE.value
    ] = raw_open_long_sl_orders[0][
        CCXTOrderCols.STOP_PRICE.value
    ]
    just_parsed_orders = await ccxt_parser(raw_open_long_sl_orders)
    should_be_order = get_parsed_open_long_sl_orders()
    assert should_be_order == just_parsed_orders


async def test_ccxt_generic_parse_default_open_long_sl_orders(
    raw_open_long_sl_orders=get_raw_open_long_sl_orders(),
):
    just_parsed_orders = await ccxt_generic_parser(raw_open_long_sl_orders)
    assert get_parsed_open_long_sl_orders() == just_parsed_orders


async def test_base_parse_default_open_short_sl_orders(
    raw_open_short_sl_orders=get_raw_open_short_sl_orders(),
):
    raw_open_short_sl_orders[0][
        CCXTOrderCols.TYPE.value
    ] = TradeOrderType.STOP_LOSS.value

    just_parsed_orders = await base_parser(raw_open_short_sl_orders)
    assert get_parsed_open_short_sl_orders() == just_parsed_orders


async def test_base_parse_default_open_short_sl_orders(
    raw_open_short_sl_orders=get_raw_open_short_sl_orders(),
):
    raw_open_short_sl_orders[0][
        CCXTOrderCols.TYPE.value
    ] = TradeOrderType.STOP_LOSS.value

    just_parsed_orders = await base_parser(raw_open_short_sl_orders)
    assert get_parsed_open_short_sl_orders() == just_parsed_orders


async def test_ccxt_parse_default_open_short_sl_orders(
    raw_open_short_sl_orders=get_raw_open_short_sl_orders(),
):
    raw_open_short_sl_orders[0][
        CCXTOrderCols.TYPE.value
    ] = TradeOrderType.STOP_LOSS.value
    raw_open_short_sl_orders[0][
        CCXTOrderCols.PRICE.value
    ] = raw_open_short_sl_orders[0][
        CCXTOrderCols.STOP_PRICE.value
    ]
    just_parsed_orders = await ccxt_parser(raw_open_short_sl_orders)  
    should_be_order = get_parsed_open_short_sl_orders()
    assert should_be_order == just_parsed_orders


async def test_ccxt_generic_parse_default_open_short_sl_orders(
    raw_open_short_sl_orders=get_raw_open_short_sl_orders(),
):
    just_parsed_orders = await ccxt_generic_parser(raw_open_short_sl_orders)
    assert get_parsed_open_short_sl_orders() == just_parsed_orders
