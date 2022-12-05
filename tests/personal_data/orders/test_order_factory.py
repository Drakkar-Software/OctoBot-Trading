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
from octobot_commons.tests.test_config import load_test_config

from tests import event_loop
from octobot_trading.personal_data.orders import Order, parse_order_type
from octobot_trading.enums import ExchangeConstantsMarketPropertyColumns, ExchangeConstantsOrderColumns, OrderStatus, TradeOrderSide, TradeOrderType, TraderOrderType
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.exchanges.traders.trader_simulator import TraderSimulator
from octobot_trading.api.exchange import cancel_ccxt_throttle_task

pytestmark = pytest.mark.asyncio


class TestOrderFactory:
    DEFAULT_SYMBOL = "BTC/USDT"
    EXCHANGE_MANAGER_CLASS_STRING = "binanceus"

    @staticmethod
    async def init_default():
        config = load_test_config()
        exchange_manager = ExchangeManager(config, TestOrderFactory.EXCHANGE_MANAGER_CLASS_STRING)
        await exchange_manager.initialize()

        trader = TraderSimulator(config, exchange_manager)
        await trader.initialize()

        return config, exchange_manager, trader

    @staticmethod
    async def stop(exchange_manager):
        cancel_ccxt_throttle_task()
        await exchange_manager.stop()

    async def test_parse_order_type(self):
        _, exchange_manager, trader_inst = await self.init_default()

        order_to_test = Order(trader_inst)
        assert order_to_test.simulated is True

        ccxt_order_buy_market = {
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
            ExchangeConstantsOrderColumns.FILLED.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.COST.value: decimal.Decimal("0"),
            ExchangeConstantsOrderColumns.REDUCE_ONLY.value: False,
            ExchangeConstantsOrderColumns.FEE.value: None,
        }

        order_to_test.update_from_raw(ccxt_order_buy_market)
        assert order_to_test.order_type == TraderOrderType.BUY_MARKET

        ccxt_order_buy_limit = {
            "side": TradeOrderSide.BUY,
            "type": TradeOrderType.LIMIT
        }
        assert parse_order_type(ccxt_order_buy_limit) == (TradeOrderSide.BUY, TraderOrderType.BUY_LIMIT)

        ccxt_order_sell_market = {
            "side": TradeOrderSide.SELL,
            "type": TradeOrderType.MARKET
        }
        assert parse_order_type(ccxt_order_sell_market) == (TradeOrderSide.SELL, TraderOrderType.SELL_MARKET)

        ccxt_order_sell_limit = {
            "side": TradeOrderSide.SELL,
            "type": TradeOrderType.LIMIT
        }
        assert parse_order_type(ccxt_order_sell_limit) == (TradeOrderSide.SELL, TraderOrderType.SELL_LIMIT)

        await self.stop(exchange_manager)
