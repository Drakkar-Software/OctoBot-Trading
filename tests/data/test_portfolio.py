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
# All test coroutines will be treated as marked.
from octobot_commons.constants import PORTFOLIO_AVAILABLE, PORTFOLIO_TOTAL
from octobot_commons.tests.test_config import load_test_config

from octobot_trading.constants import CONFIG_SIMULATOR_FEES_MAKER, CONFIG_SIMULATOR_FEES_TAKER, CONFIG_SIMULATOR, \
    CONFIG_SIMULATOR_FEES
from octobot_trading.data.order import Order
from octobot_trading.data.portfolio import Portfolio
from octobot_trading.enums import TraderOrderType, TradeOrderSide
from octobot_trading.exchanges.exchange_builder import ExchangeBuilder
from octobot_trading.orders.types.buy_limit_order import BuyLimitOrder
from octobot_trading.orders.types.buy_market_order import BuyMarketOrder
from octobot_trading.orders.types.sell_limit_order import SellLimitOrder
from octobot_trading.orders.types.sell_market_order import SellMarketOrder
from octobot_trading.orders.types.stop_loss_order import StopLossOrder
from tests.test_utils.order_util import fill_market_order, fill_limit_or_stop_order

pytestmark = pytest.mark.asyncio


class TestPortfolio:
    EXCHANGE_NAME = "binance"

    @staticmethod
    async def init_default(config=None):
        if not config:
            config = load_test_config()

        exchange_builder = ExchangeBuilder(config, TestPortfolio.EXCHANGE_NAME).\
            is_rest_only().\
            is_simulated().\
            disable_trading_mode()
        exchange_manager = await exchange_builder.build()

        return config, exchange_manager, \
               exchange_manager.exchange_personal_data.portfolio_manager, exchange_manager.trader

    @staticmethod
    async def stop_default(exchange_manager):
        await exchange_manager.stop()

    async def test_load_portfolio(self):
        _, exchange_manager, portfolio_manager, _ = await self.init_default()
        assert portfolio_manager.portfolio.portfolio == {
            'BTC': {'available': 10, 'total': 10},
            'USDT': {'available': 1000, 'total': 1000}
        }
        await self.stop_default(exchange_manager)

    async def test_get_portfolio_from_amount_dict(self):
        _, exchange_manager, portfolio_manager, _ = await self.init_default()
        assert portfolio_manager.portfolio.get_portfolio_from_amount_dict({"zyx": 10, "BTC": 1}) == {
            'zyx': {'available': 10, 'total': 10},
            'BTC': {'available': 1, 'total': 1}
        }
        assert portfolio_manager.portfolio.get_portfolio_from_amount_dict({}) == {}
        with pytest.raises(RuntimeError):
            portfolio_manager.portfolio.get_portfolio_from_amount_dict({"zyx": "10", "BTC": 1})
        await self.stop_default(exchange_manager)

    async def test_get_currency_portfolio(self):
        _, exchange_manager, portfolio_manager, _ = await self.init_default()
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 10
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 10
        assert portfolio_manager.portfolio.get_currency_portfolio("NANO", PORTFOLIO_TOTAL) == 0
        await self.stop_default(exchange_manager)

    async def test_update_portfolio_available(self):
        _, exchange_manager, portfolio_manager, trader = await self.init_default()

        # Test buy order
        market_buy = BuyMarketOrder(trader)
        market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                          symbol="BTC/USDT",
                          current_price=70,
                          quantity=10,
                          price=70)

        # test buy order creation
        portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 10
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 300
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 10
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 1000

        # test buy order canceled --> return to init state and the update_portfolio will sync TOTAL with AVAILABLE
        portfolio_manager.portfolio.update_portfolio_available(market_buy, False)
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 10
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 1000
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 10
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 1000

        # Test sell order
        limit_sell = SellLimitOrder(trader)
        limit_sell.update(order_type=TraderOrderType.SELL_LIMIT,
                          symbol="BTC/USDT",
                          current_price=60,
                          quantity=8,
                          price=60)
        # test sell order creation
        portfolio_manager.portfolio.update_portfolio_available(limit_sell, True)
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 2
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 1000
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 10
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 1000

        # test sell order canceled --> return to init state and the update_portfolio will sync TOTAL with AVAILABLE
        portfolio_manager.portfolio.update_portfolio_available(limit_sell, False)
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 10
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 1000
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 10
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 1000

        await self.stop_default(exchange_manager)

    async def test_update_portfolio(self):
        _, exchange_manager, portfolio_manager, trader = await self.init_default()

        # Test buy order
        limit_buy = BuyLimitOrder(trader)
        limit_buy.update(order_type=TraderOrderType.BUY_LIMIT,
                         symbol="BTC/USDT",
                         current_price=70,
                         quantity=10,
                         price=70)

        # update portfolio with creations
        portfolio_manager.portfolio.update_portfolio_available(limit_buy, True)
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 10
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 300

        await fill_limit_or_stop_order(limit_buy, 69, 71)

        await self._update_portfolio_from_order_without_fees(portfolio_manager, limit_buy)
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 20
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 300
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 20
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 300

        # Test buy order
        market_sell = SellMarketOrder(trader)
        market_sell.update(order_type=TraderOrderType.SELL_MARKET,
                           symbol="BTC/USDT",
                           current_price=80,
                           quantity=8,
                           price=80)

        # update portfolio with creations
        portfolio_manager.portfolio.update_portfolio_available(market_sell, True)
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 12
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 300

        await fill_market_order(market_sell, 80)

        # when filling market sell
        await self._update_portfolio_from_order_without_fees(portfolio_manager, market_sell)
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 12
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 940
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 12
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 940

        await self.stop_default(exchange_manager)

    async def test_update_portfolio_with_filled_orders(self):
        _, exchange_manager, portfolio_manager, trader = await self.init_default()

        # force fees => should have consequences
        exchange_manager.exchange.config[CONFIG_SIMULATOR][CONFIG_SIMULATOR_FEES] = {
            CONFIG_SIMULATOR_FEES_MAKER: 0.05,
            CONFIG_SIMULATOR_FEES_TAKER: 0.1
        }

        # Test buy order
        market_sell = SellMarketOrder(trader)
        market_sell.update(order_type=TraderOrderType.SELL_MARKET,
                           symbol="BTC/USDT",
                           current_price=70,
                           quantity=3,
                           price=70)

        await fill_market_order(market_sell, 70)

        # Test sell order
        limit_sell = SellLimitOrder(trader)
        limit_sell.update(order_type=TraderOrderType.SELL_LIMIT,
                          symbol="BTC/USDT",
                          current_price=100,
                          quantity=4.2,
                          price=100)

        # Test stop loss order
        stop_loss = StopLossOrder(trader)
        stop_loss.update(order_type=TraderOrderType.STOP_LOSS,
                         symbol="BTC/USDT",
                         current_price=80,
                         quantity=4.2,
                         price=80)

        limit_sell.add_linked_order(stop_loss)
        stop_loss.add_linked_order(limit_sell)

        # Test buy order
        limit_buy = BuyLimitOrder(trader)
        limit_buy.update(order_type=TraderOrderType.BUY_LIMIT,
                         symbol="BTC/USDT",
                         current_price=50,
                         quantity=2,
                         price=50)

        await fill_limit_or_stop_order(limit_buy, 49, 51)

        # update portfolio with creations
        portfolio_manager.portfolio.update_portfolio_available(market_sell, True)
        portfolio_manager.portfolio.update_portfolio_available(limit_sell, True)
        portfolio_manager.portfolio.update_portfolio_available(stop_loss, True)
        portfolio_manager.portfolio.update_portfolio_available(limit_buy, True)

        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 2.8
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 900

        # when cancelling limit sell, market sell and stop orders
        portfolio_manager.portfolio.update_portfolio_available(stop_loss, False)
        portfolio_manager.portfolio.update_portfolio_available(limit_sell, False)

        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 7
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 900

        # when filling limit buy
        await self._update_portfolio_from_order_with_fees(portfolio_manager, limit_buy)

        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 8.998
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 900
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 11.998
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 900

        # when filling market sell
        await self._update_portfolio_from_order_with_fees(portfolio_manager, market_sell)

        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 8.998
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 1109.79
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 8.998
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 1109.79

        await self.stop_default(exchange_manager)

    async def test_update_portfolio_with_cancelled_orders(self):
        _, exchange_manager, portfolio_manager, trader = await self.init_default()

        # force fees => shouldn't do anything
        exchange_manager.exchange.config[CONFIG_SIMULATOR][CONFIG_SIMULATOR_FEES] = {
            CONFIG_SIMULATOR_FEES_MAKER: 0.05,
            CONFIG_SIMULATOR_FEES_TAKER: 0.1
        }

        # Test buy order
        market_sell = SellMarketOrder(trader)
        market_sell.update(order_type=TraderOrderType.SELL_MARKET,
                           symbol="BTC/USDT",
                           current_price=80,
                           quantity=4.1,
                           price=80)

        # Test sell order
        limit_sell = SellLimitOrder(trader)
        limit_sell.update(order_type=TraderOrderType.SELL_LIMIT,
                          symbol="BTC/USDT",
                          current_price=10,
                          quantity=4.2,
                          price=10)

        # Test stop loss order
        stop_loss = StopLossOrder(trader)
        stop_loss.update(order_type=TraderOrderType.STOP_LOSS,
                         symbol="BTC/USDT",
                         current_price=80,
                         quantity=3.6,
                         price=80)

        portfolio_manager.portfolio.update_portfolio_available(stop_loss, True)
        portfolio_manager.portfolio.update_portfolio_available(limit_sell, True)

        # Test buy order
        limit_buy = BuyLimitOrder(trader)
        limit_buy.update(order_type=TraderOrderType.BUY_LIMIT,
                         symbol="BTC/USDT",
                         current_price=50,
                         quantity=4,
                         price=50)

        portfolio_manager.portfolio.update_portfolio_available(limit_buy, True)
        portfolio_manager.portfolio.update_portfolio_available(market_sell, True)

        assert round(portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE), 1) == 1.7
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 800
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 10
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 1000

        # with no filled orders
        portfolio_manager.portfolio.update_portfolio_available(stop_loss, False)
        portfolio_manager.portfolio.update_portfolio_available(limit_sell, False)
        portfolio_manager.portfolio.update_portfolio_available(limit_buy, False)
        portfolio_manager.portfolio.update_portfolio_available(market_sell, False)

        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 10
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 1000
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 10
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 1000

        await self.stop_default(exchange_manager)

    async def test_update_portfolio_with_stop_loss_orders(self):
        _, exchange_manager, portfolio_manager, trader = await self.init_default()

        # Test buy order
        limit_sell = SellLimitOrder(trader)
        limit_sell.update(order_type=TraderOrderType.SELL_LIMIT,
                          symbol="BTC/USDT",
                          current_price=90,
                          quantity=4,
                          price=90)

        # Test buy order
        limit_buy = BuyLimitOrder(trader)
        limit_buy.update(order_type=TraderOrderType.BUY_LIMIT,
                         symbol="BTC/USDT",
                         current_price=50,
                         quantity=4,
                         price=50)

        # Test stop loss order
        stop_loss = StopLossOrder(trader)
        stop_loss.update(order_type=TraderOrderType.STOP_LOSS,
                         symbol="BTC/USDT",
                         current_price=60,
                         quantity=4,
                         price=60)

        await fill_limit_or_stop_order(stop_loss, 59, 61)

        portfolio_manager.portfolio.update_portfolio_available(stop_loss, True)
        portfolio_manager.portfolio.update_portfolio_available(limit_sell, True)
        portfolio_manager.portfolio.update_portfolio_available(limit_buy, True)

        assert round(portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE), 1) == 6
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 800
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 10
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 1000

        # cancel limits
        portfolio_manager.portfolio.update_portfolio_available(limit_buy, False)
        portfolio_manager.portfolio.update_portfolio_available(limit_sell, False)

        # filling stop loss
        # typical stop loss behavior --> update available before update portfolio
        await self._update_portfolio_from_order_without_fees(portfolio_manager, stop_loss)

        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 6
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 1240
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 6
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 1240

        await self.stop_default(exchange_manager)

    async def test_update_portfolio_with_some_filled_orders(self):
        _, exchange_manager, portfolio_manager, trader = await self.init_default()

        # Test buy order
        limit_sell = SellLimitOrder(trader)
        limit_sell.update(order_type=TraderOrderType.SELL_LIMIT,
                          symbol="BTC/USDT",
                          current_price=90,
                          quantity=4,
                          price=90)

        # Test buy order
        limit_buy = BuyLimitOrder(trader)
        limit_buy.update(order_type=TraderOrderType.BUY_LIMIT,
                         symbol="BTC/USDT",
                         current_price=60,
                         quantity=2,
                         price=60)

        # Test buy order
        limit_buy_2 = BuyLimitOrder(trader)
        limit_buy_2.update(order_type=TraderOrderType.BUY_LIMIT,
                           symbol="BTC/USDT",
                           current_price=50,
                           quantity=4,
                           price=50)

        # Test sell order
        limit_sell_2 = SellLimitOrder(trader)
        limit_sell_2.update(order_type=TraderOrderType.SELL_LIMIT,
                            symbol="BTC/USDT",
                            current_price=10,
                            quantity=2,
                            price=10)

        # Test stop loss order
        stop_loss_2 = StopLossOrder(trader)
        stop_loss_2.update(order_type=TraderOrderType.STOP_LOSS,
                           symbol="BTC/USDT",
                           current_price=10,
                           quantity=2,
                           price=10)

        # Test sell order
        limit_sell_3 = SellLimitOrder(trader)
        limit_sell_3.update(order_type=TraderOrderType.SELL_LIMIT,
                            symbol="BTC/USDT",
                            current_price=20,
                            quantity=1,
                            price=20)

        # Test stop loss order
        stop_loss_3 = StopLossOrder(trader)
        stop_loss_3.update(order_type=TraderOrderType.STOP_LOSS,
                           symbol="BTC/USDT",
                           current_price=20,
                           quantity=1,
                           price=20)

        portfolio_manager.portfolio.update_portfolio_available(stop_loss_2, True)
        portfolio_manager.portfolio.update_portfolio_available(stop_loss_3, True)
        portfolio_manager.portfolio.update_portfolio_available(limit_sell, True)
        portfolio_manager.portfolio.update_portfolio_available(limit_sell_2, True)
        portfolio_manager.portfolio.update_portfolio_available(limit_sell_3, True)
        portfolio_manager.portfolio.update_portfolio_available(limit_buy, True)
        portfolio_manager.portfolio.update_portfolio_available(limit_buy_2, True)

        assert round(portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE), 1) == 3
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 680
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 10
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 1000

        # cancels
        portfolio_manager.portfolio.update_portfolio_available(stop_loss_3, False)
        portfolio_manager.portfolio.update_portfolio_available(limit_sell_2, False)
        portfolio_manager.portfolio.update_portfolio_available(limit_buy, False)

        # filling
        await fill_limit_or_stop_order(stop_loss_2, 9, 11)
        await fill_limit_or_stop_order(limit_sell, 89, 91)
        await fill_limit_or_stop_order(limit_sell_3, 19, 21)
        await fill_limit_or_stop_order(limit_buy_2, 49, 51)

        await self._update_portfolio_from_order_without_fees(portfolio_manager, stop_loss_2)
        await self._update_portfolio_from_order_without_fees(portfolio_manager, limit_sell)
        await self._update_portfolio_from_order_without_fees(portfolio_manager, limit_sell_3)
        await self._update_portfolio_from_order_without_fees(portfolio_manager, limit_buy_2)

        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 7
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 1200
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 7
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 1200

        await self.stop_default(exchange_manager)

    async def test_update_portfolio_with_multiple_filled_orders(self):
        _, exchange_manager, portfolio_manager, trader = await self.init_default()

        # Test buy order
        limit_sell = SellLimitOrder(trader)
        limit_sell.update(order_type=TraderOrderType.SELL_LIMIT,
                          symbol="BTC/USDT",
                          current_price=90,
                          quantity=4,
                          price=90)

        # Test buy order
        limit_buy = BuyLimitOrder(trader)
        limit_buy.update(order_type=TraderOrderType.BUY_LIMIT,
                         symbol="BTC/USDT",
                         current_price=60,
                         quantity=2,
                         price=60)

        # Test buy order
        limit_buy_2 = BuyLimitOrder(trader)
        limit_buy_2.update(order_type=TraderOrderType.BUY_LIMIT,
                           symbol="BTC/USDT",
                           current_price=50,
                           quantity=4,
                           price=50)

        # Test buy order
        limit_buy_3 = BuyLimitOrder(trader)
        limit_buy_3.update(order_type=TraderOrderType.BUY_LIMIT,
                           symbol="BTC/USDT",
                           current_price=46,
                           quantity=2,
                           price=46)

        # Test buy order
        limit_buy_4 = BuyLimitOrder(trader)
        limit_buy_4.update(order_type=TraderOrderType.BUY_LIMIT,
                           symbol="BTC/USDT",
                           current_price=41,
                           quantity=1.78,
                           price=41)

        # Test buy order
        limit_buy_5 = BuyLimitOrder(trader)
        limit_buy_5.update(order_type=TraderOrderType.BUY_LIMIT,
                           symbol="BTC/USDT",
                           current_price=0.2122427,
                           quantity=3.72448,
                           price=0.2122427)

        # Test buy order
        limit_buy_6 = BuyLimitOrder(trader)
        limit_buy_6.update(order_type=TraderOrderType.BUY_LIMIT,
                           symbol="BTC/USDT",
                           current_price=430,
                           quantity=1.05,
                           price=430)

        # Test sell order
        limit_sell_2 = SellLimitOrder(trader)
        limit_sell_2.update(order_type=TraderOrderType.SELL_LIMIT,
                            symbol="BTC/USDT",
                            current_price=10,
                            quantity=2,
                            price=10)

        # Test stop loss order
        stop_loss_2 = StopLossOrder(trader)
        stop_loss_2.update(order_type=TraderOrderType.STOP_LOSS,
                           symbol="BTC/USDT",
                           current_price=10,
                           quantity=2,
                           price=10)

        # Test sell order
        limit_sell_3 = SellLimitOrder(trader)
        limit_sell_3.update(order_type=TraderOrderType.SELL_LIMIT,
                            symbol="BTC/USDT",
                            current_price=20,
                            quantity=1,
                            price=20)

        # Test stop loss order
        stop_loss_3 = StopLossOrder(trader)
        stop_loss_3.update(order_type=TraderOrderType.STOP_LOSS,
                           symbol="BTC/USDT",
                           current_price=20,
                           quantity=1,
                           price=20)

        # Test sell order
        limit_sell_4 = SellLimitOrder(trader)
        limit_sell_4.update(order_type=TraderOrderType.SELL_LIMIT,
                            symbol="BTC/USDT",
                            current_price=50,
                            quantity=0.2,
                            price=50)

        # Test stop loss order
        stop_loss_4 = StopLossOrder(trader)
        stop_loss_4.update(order_type=TraderOrderType.STOP_LOSS,
                           symbol="BTC/USDT",
                           current_price=45,
                           quantity=0.2,
                           price=45)

        # Test sell order
        limit_sell_5 = SellLimitOrder(trader)
        limit_sell_5.update(order_type=TraderOrderType.SELL_LIMIT,
                            symbol="BTC/USDT",
                            current_price=11,
                            quantity=0.7,
                            price=11)

        # Test stop loss order
        stop_loss_5 = StopLossOrder(trader)
        stop_loss_5.update(order_type=TraderOrderType.STOP_LOSS,
                           symbol="BTC/USDT",
                           current_price=9,
                           quantity=0.7,
                           price=9)

        portfolio_manager.portfolio.update_portfolio_available(stop_loss_2, True)
        portfolio_manager.portfolio.update_portfolio_available(stop_loss_3, True)
        portfolio_manager.portfolio.update_portfolio_available(stop_loss_4, True)
        portfolio_manager.portfolio.update_portfolio_available(stop_loss_5, True)
        portfolio_manager.portfolio.update_portfolio_available(limit_sell, True)
        portfolio_manager.portfolio.update_portfolio_available(limit_sell_2, True)
        portfolio_manager.portfolio.update_portfolio_available(limit_sell_3, True)
        portfolio_manager.portfolio.update_portfolio_available(limit_sell_4, True)
        portfolio_manager.portfolio.update_portfolio_available(limit_sell_5, True)
        portfolio_manager.portfolio.update_portfolio_available(limit_buy, True)
        portfolio_manager.portfolio.update_portfolio_available(limit_buy_2, True)
        portfolio_manager.portfolio.update_portfolio_available(limit_buy_3, True)
        portfolio_manager.portfolio.update_portfolio_available(limit_buy_4, True)
        portfolio_manager.portfolio.update_portfolio_available(limit_buy_5, True)
        portfolio_manager.portfolio.update_portfolio_available(limit_buy_6, True)

        assert round(portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE), 1) == 2.1
        assert round(portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE), 7) == 62.7295063
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 10
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 1000

        # cancels
        portfolio_manager.portfolio.update_portfolio_available(stop_loss_3, False)
        portfolio_manager.portfolio.update_portfolio_available(stop_loss_5, False)
        portfolio_manager.portfolio.update_portfolio_available(limit_sell_2, False)
        portfolio_manager.portfolio.update_portfolio_available(limit_buy, False)
        portfolio_manager.portfolio.update_portfolio_available(limit_buy_3, False)
        portfolio_manager.portfolio.update_portfolio_available(limit_buy_5, False)
        portfolio_manager.portfolio.update_portfolio_available(limit_sell_4, False)

        # filling
        await fill_limit_or_stop_order(stop_loss_2, 9, 11)
        await fill_limit_or_stop_order(limit_sell, 89, 91)
        await fill_limit_or_stop_order(limit_sell_3, 19, 21)
        await fill_limit_or_stop_order(limit_buy_2, 49, 51)
        await fill_limit_or_stop_order(limit_sell_5, 9, 12)
        await fill_limit_or_stop_order(stop_loss_4, 44, 46)
        await fill_limit_or_stop_order(limit_buy_4, 40, 42)
        await fill_limit_or_stop_order(limit_buy_5, 0.2122426, 0.2122428)
        await fill_limit_or_stop_order(limit_buy_6, 429, 431)

        await self._update_portfolio_from_order_without_fees(portfolio_manager, stop_loss_2)
        await self._update_portfolio_from_order_without_fees(portfolio_manager, limit_buy_4)
        await self._update_portfolio_from_order_without_fees(portfolio_manager, limit_sell)
        await self._update_portfolio_from_order_without_fees(portfolio_manager, limit_sell_3)
        await self._update_portfolio_from_order_without_fees(portfolio_manager, limit_buy_2)
        await self._update_portfolio_from_order_without_fees(portfolio_manager, limit_sell_5)
        await self._update_portfolio_from_order_without_fees(portfolio_manager, stop_loss_4)
        await self._update_portfolio_from_order_without_fees(portfolio_manager, limit_buy_5)
        await self._update_portfolio_from_order_without_fees(portfolio_manager, limit_buy_6)

        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 12.65448
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 692.22
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 12.65448
        assert round(portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL), 7) == 691.4295063

        await self.stop_default(exchange_manager)

    async def test_update_portfolio_with_multiple_symbols_orders(self):
        _, exchange_manager, portfolio_manager, trader = await self.init_default()

        # Test buy order
        market_buy = BuyMarketOrder(trader)
        market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                          symbol="ETH/USDT",
                          current_price=7,
                          quantity=100,
                          price=7)

        # test buy order creation
        portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
        assert portfolio_manager.portfolio.get_currency_portfolio("ETH", PORTFOLIO_AVAILABLE) == 0
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 300
        assert portfolio_manager.portfolio.get_currency_portfolio("ETH", PORTFOLIO_TOTAL) == 0
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 1000

        await fill_market_order(market_buy, 7)

        await self._update_portfolio_from_order_without_fees(portfolio_manager, market_buy)
        assert portfolio_manager.portfolio.get_currency_portfolio("ETH", PORTFOLIO_AVAILABLE) == 100
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 300
        assert portfolio_manager.portfolio.get_currency_portfolio("ETH", PORTFOLIO_TOTAL) == 100
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 300

        # Test buy order
        market_buy = BuyMarketOrder(trader)
        market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                          symbol="LTC/BTC",
                          current_price=0.0135222,
                          quantity=100,
                          price=0.0135222)

        # test buy order creation
        portfolio_manager.portfolio.update_portfolio_available(market_buy, True)
        assert portfolio_manager.portfolio.get_currency_portfolio("LTC", PORTFOLIO_AVAILABLE) == 0
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 8.647780000000001
        assert portfolio_manager.portfolio.get_currency_portfolio("LTC", PORTFOLIO_TOTAL) == 0
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 10

        await fill_market_order(market_buy, 0.0135222)

        await self._update_portfolio_from_order_without_fees(portfolio_manager, market_buy)
        assert portfolio_manager.portfolio.get_currency_portfolio("LTC", PORTFOLIO_AVAILABLE) == 100
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 8.647780000000001
        assert portfolio_manager.portfolio.get_currency_portfolio("LTC", PORTFOLIO_TOTAL) == 100
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 8.647780000000001

        # Test buy order
        limit_buy = BuyLimitOrder(trader)
        limit_buy.update(order_type=TraderOrderType.BUY_LIMIT,
                         symbol="XRP/BTC",
                         current_price=0.00012232132312312,
                         quantity=3000.1214545,
                         price=0.00012232132312312)

        # test buy order creation
        portfolio_manager.portfolio.update_portfolio_available(limit_buy, True)
        assert portfolio_manager.portfolio.get_currency_portfolio("XRP", PORTFOLIO_AVAILABLE) == 0
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 8.280801174155501
        assert portfolio_manager.portfolio.get_currency_portfolio("XRP", PORTFOLIO_TOTAL) == 0
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 8.647780000000001

        # cancel
        portfolio_manager.portfolio.update_portfolio_available(limit_buy, False)
        assert portfolio_manager.portfolio.get_currency_portfolio("XRP", PORTFOLIO_AVAILABLE) == 0
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 8.647780000000001
        assert portfolio_manager.portfolio.get_currency_portfolio("XRP", PORTFOLIO_TOTAL) == 0
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 8.647780000000001

        await self.stop_default(exchange_manager)

    async def test_reset_portfolio_available(self):
        _, exchange_manager, portfolio_manager, trader = await self.init_default()

        # Test buy order
        limit_sell = SellLimitOrder(trader)
        limit_sell.update(order_type=TraderOrderType.SELL_LIMIT,
                          symbol="BTC/USDT",
                          current_price=90,
                          quantity=4,
                          price=90)

        portfolio_manager.portfolio.update_portfolio_available(limit_sell, True)
        portfolio_manager.portfolio.reset_portfolio_available()

        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 10
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 1000
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 10
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 1000

        # Test sell order
        limit_sell = SellLimitOrder(trader)
        limit_sell.update(order_type=TraderOrderType.SELL_LIMIT,
                          symbol="BTC/USDT",
                          current_price=90,
                          quantity=4,
                          price=90)

        portfolio_manager.portfolio.update_portfolio_available(limit_sell, True)
        # Test buy order
        limit_buy = BuyLimitOrder(trader)
        limit_buy.update(order_type=TraderOrderType.BUY_LIMIT,
                         symbol="VEN/BTC",
                         current_price=0.5,
                         quantity=4,
                         price=0.5)

        portfolio_manager.portfolio.update_portfolio_available(limit_buy, True)

        # Test buy order
        btc_limit_buy = BuyLimitOrder(trader)
        btc_limit_buy.update(order_type=TraderOrderType.BUY_LIMIT,
                             symbol="BTC/USDT",
                             current_price=10,
                             quantity=50,
                             price=10)

        portfolio_manager.portfolio.update_portfolio_available(btc_limit_buy, True)

        # Test buy order
        btc_limit_buy2 = BuyLimitOrder(trader)
        btc_limit_buy2.update(order_type=TraderOrderType.BUY_LIMIT,
                              symbol="BTC/USDT",
                              current_price=10,
                              quantity=50,
                              price=10)

        portfolio_manager.portfolio.update_portfolio_available(btc_limit_buy2, True)

        # reset equivalent of the ven buy order
        portfolio_manager.portfolio.reset_portfolio_available("BTC", 4 * 0.5)

        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 6
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 10
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 0
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 1000

        # reset equivalent of the btc buy orders 1 and 2
        portfolio_manager.portfolio.reset_portfolio_available("USDT")

        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_AVAILABLE) == 6
        assert portfolio_manager.portfolio.get_currency_portfolio("BTC", PORTFOLIO_TOTAL) == 10
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_AVAILABLE) == 1000
        assert portfolio_manager.portfolio.get_currency_portfolio("USDT", PORTFOLIO_TOTAL) == 1000

        await self.stop_default(exchange_manager)

    async def _update_portfolio_from_order_without_fees(self, portfolio_manager, order):
        order.fee = None
        await portfolio_manager.portfolio.update_portfolio_from_order(order)

    async def _update_portfolio_from_order_with_fees(self, portfolio_manager, order):
        await portfolio_manager.portfolio.update_portfolio_from_order(order)
