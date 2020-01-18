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
import os

from asyncmock import AsyncMock

import time

import copy
import pytest
from mock import patch

from octobot_commons.constants import CONFIG_ENABLED_OPTION, PORTFOLIO_AVAILABLE, PORTFOLIO_TOTAL

from octobot_commons.tests.test_config import load_test_config
from octobot_trading.constants import CONFIG_TRADER, CONFIG_TRADER_RISK, CONFIG_TRADING, CONFIG_TRADER_RISK_MIN, \
    CONFIG_TRADER_RISK_MAX
from octobot_trading.data.order import Order
from octobot_trading.data_manager.prices_manager import PricesManager
from octobot_trading.enums import TraderOrderType, TradeOrderSide, TradeOrderType, OrderStatus
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.orders.types.buy_limit_order import BuyLimitOrder
from octobot_trading.orders.types.buy_market_order import BuyMarketOrder
from octobot_trading.orders import create_order_instance, create_order_instance_from_raw
from octobot_trading.orders.types.sell_limit_order import SellLimitOrder
from octobot_trading.orders.types.sell_market_order import SellMarketOrder
from octobot_trading.orders.types.stop_loss_order import StopLossOrder
from octobot_trading.traders.trader import Trader
from octobot_trading.traders.trader_simulator import TraderSimulator

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


class TestTrader:
    DEFAULT_SYMBOL = "BTC/USDT"
    EXCHANGE_MANAGER_CLASS_STRING = "binance"

    @staticmethod
    async def init_default(simulated=True):
        config = load_test_config()
        exchange_manager = ExchangeManager(config, TestTrader.EXCHANGE_MANAGER_CLASS_STRING)
        exchange_manager.is_simulated = simulated
        await exchange_manager.initialize()

        trader = TraderSimulator(config, exchange_manager)
        await trader.initialize()

        return config, exchange_manager, trader

    @staticmethod
    async def stop(exchange_manager):
        await exchange_manager.stop()

    async def test_enabled(self):
        config, exchange_manager, trader_inst = await self.init_default()
        await self.stop(exchange_manager)

        config[CONFIG_TRADER][CONFIG_ENABLED_OPTION] = True
        assert Trader.enabled(config)

        config[CONFIG_TRADER][CONFIG_ENABLED_OPTION] = False
        assert not Trader.enabled(config)
        await self.stop(exchange_manager)

    async def test_get_risk(self):
        config, exchange_manager, trader_inst = await self.init_default()
        await self.stop(exchange_manager)

        config[CONFIG_TRADING][CONFIG_TRADER_RISK] = 0
        trader_1 = TraderSimulator(config, exchange_manager)
        assert round(trader_1.risk, 2) == CONFIG_TRADER_RISK_MIN
        await self.stop(exchange_manager)

        config[CONFIG_TRADING][CONFIG_TRADER_RISK] = 2
        trader_2 = TraderSimulator(config, exchange_manager)
        assert trader_2.risk == CONFIG_TRADER_RISK_MAX
        await self.stop(exchange_manager)

        config[CONFIG_TRADING][CONFIG_TRADER_RISK] = 0.5
        trader_2 = TraderSimulator(config, exchange_manager)
        assert trader_2.risk == 0.5
        await self.stop(exchange_manager)

    async def test_cancel_order(self):
        _, exchange_manager, trader_inst = await self.init_default()
        orders_manager = exchange_manager.exchange_personal_data.orders_manager

        # Test buy order
        market_buy = BuyMarketOrder(trader_inst)
        market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                          symbol=self.DEFAULT_SYMBOL,
                          current_price=70,
                          quantity=10,
                          price=70)

        assert market_buy not in orders_manager.get_open_orders()

        assert await trader_inst.create_order(market_buy)

        assert market_buy in orders_manager.get_open_orders()

        await trader_inst.cancel_order(market_buy)

        assert market_buy not in orders_manager.get_open_orders()

        await self.stop(exchange_manager)

    async def test_cancel_open_orders_default_symbol(self):
        config, exchange_manager, trader_inst = await self.init_default()
        orders_manager = exchange_manager.exchange_personal_data.orders_manager

        # Test buy order
        market_buy = BuyMarketOrder(trader_inst)
        market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                          symbol=self.DEFAULT_SYMBOL,
                          current_price=70,
                          quantity=10,
                          price=70)

        # Test sell order
        market_sell = SellMarketOrder(trader_inst)
        market_sell.update(order_type=TraderOrderType.SELL_MARKET,
                           symbol=self.DEFAULT_SYMBOL,
                           current_price=70,
                           quantity=10,
                           price=70)

        # Test buy order
        limit_buy = BuyLimitOrder(trader_inst)
        limit_buy.update(order_type=TraderOrderType.BUY_LIMIT,
                         symbol=self.DEFAULT_SYMBOL,
                         current_price=70,
                         quantity=10,
                         price=70)

        await trader_inst.create_order(market_buy)
        await trader_inst.create_order(market_sell)
        await trader_inst.create_order(limit_buy)

        assert market_buy in orders_manager.get_open_orders()
        assert market_sell in orders_manager.get_open_orders()
        assert limit_buy in orders_manager.get_open_orders()

        await trader_inst.cancel_open_orders(self.DEFAULT_SYMBOL)

        assert market_buy not in orders_manager.get_open_orders()
        assert market_sell not in orders_manager.get_open_orders()
        assert limit_buy not in orders_manager.get_open_orders()

        await self.stop(exchange_manager)

    async def test_cancel_open_orders_multi_symbol(self):
        config, exchange_manager, trader_inst = await self.init_default()
        orders_manager = exchange_manager.exchange_personal_data.orders_manager

        # Test buy order
        market_buy = BuyMarketOrder(trader_inst)
        market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                          symbol="BTC/USDC",
                          current_price=70,
                          quantity=10,
                          price=70)

        # Test buy order
        limit_sell = SellLimitOrder(trader_inst)
        limit_sell.update(order_type=TraderOrderType.SELL_LIMIT,
                          symbol="NANO/USDT",
                          current_price=70,
                          quantity=10,
                          price=70)

        # Test sell order
        market_sell = SellMarketOrder(trader_inst)
        market_sell.update(order_type=TraderOrderType.SELL_MARKET,
                           symbol=self.DEFAULT_SYMBOL,
                           current_price=70,
                           quantity=10,
                           price=70)

        # Test buy order
        limit_buy = BuyLimitOrder(trader_inst)
        limit_buy.update(order_type=TraderOrderType.BUY_LIMIT,
                         symbol=self.DEFAULT_SYMBOL,
                         current_price=70,
                         quantity=10,
                         price=70)

        await trader_inst.create_order(market_buy)
        await trader_inst.create_order(market_sell)
        await trader_inst.create_order(limit_buy)
        await trader_inst.create_order(limit_sell)

        assert market_buy in orders_manager.get_open_orders()
        assert market_sell in orders_manager.get_open_orders()
        assert limit_buy in orders_manager.get_open_orders()
        assert limit_sell in orders_manager.get_open_orders()

        await trader_inst.cancel_open_orders(self.DEFAULT_SYMBOL)

        assert market_buy in orders_manager.get_open_orders()
        assert market_sell not in orders_manager.get_open_orders()
        assert limit_buy not in orders_manager.get_open_orders()
        assert limit_sell in orders_manager.get_open_orders()

        await self.stop(exchange_manager)

    async def test_cancel_all_open_orders_with_currency(self):
        config, exchange_manager, trader_inst = await self.init_default()
        orders_manager = exchange_manager.exchange_personal_data.orders_manager

        # Test buy order
        market_buy = BuyMarketOrder(trader_inst)
        market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                          symbol="BTC/USDC",
                          current_price=70,
                          quantity=10,
                          price=70)

        # Test buy order
        limit_sell = SellLimitOrder(trader_inst)
        limit_sell.update(order_type=TraderOrderType.SELL_LIMIT,
                          symbol="XRP/BTC",
                          current_price=70,
                          quantity=10,
                          price=70)

        # Test sell order
        market_sell = SellMarketOrder(trader_inst)
        market_sell.update(order_type=TraderOrderType.SELL_MARKET,
                           symbol=self.DEFAULT_SYMBOL,
                           current_price=70,
                           quantity=10,
                           price=70)

        # Test buy order
        limit_buy = BuyLimitOrder(trader_inst)
        limit_buy.update(order_type=TraderOrderType.BUY_LIMIT,
                         symbol=self.DEFAULT_SYMBOL,
                         current_price=70,
                         quantity=10,
                         price=70)

        # create order notifier to prevent None call
        await trader_inst.create_order(market_buy)
        await trader_inst.create_order(market_sell)
        await trader_inst.create_order(limit_buy)
        await trader_inst.create_order(limit_sell)

        assert market_buy in orders_manager.get_open_orders()
        assert market_sell in orders_manager.get_open_orders()
        assert limit_buy in orders_manager.get_open_orders()
        assert limit_sell in orders_manager.get_open_orders()

        await trader_inst.cancel_all_open_orders_with_currency("XYZ")

        assert market_buy in orders_manager.get_open_orders()
        assert market_sell in orders_manager.get_open_orders()
        assert limit_buy in orders_manager.get_open_orders()
        assert limit_sell in orders_manager.get_open_orders()

        await trader_inst.cancel_all_open_orders_with_currency("XRP")

        assert market_buy in orders_manager.get_open_orders()
        assert market_sell in orders_manager.get_open_orders()
        assert limit_buy in orders_manager.get_open_orders()
        assert limit_sell not in orders_manager.get_open_orders()

        await trader_inst.cancel_all_open_orders_with_currency("USDT")

        assert market_buy in orders_manager.get_open_orders()
        assert market_sell not in orders_manager.get_open_orders()
        assert limit_buy not in orders_manager.get_open_orders()
        assert limit_sell not in orders_manager.get_open_orders()

        await trader_inst.cancel_all_open_orders_with_currency("BTC")

        assert market_buy not in orders_manager.get_open_orders()
        assert market_sell not in orders_manager.get_open_orders()
        assert limit_buy not in orders_manager.get_open_orders()
        assert limit_sell not in orders_manager.get_open_orders()

        await self.stop(exchange_manager)

    async def test_notify_order_close(self):
        config, exchange_manager, trader_inst = await self.init_default()
        orders_manager = exchange_manager.exchange_personal_data.orders_manager

        # Test buy order
        market_buy = BuyMarketOrder(trader_inst)
        market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                          symbol="BTC/USDC",
                          current_price=70,
                          quantity=10,
                          price=70)

        # Test buy order
        limit_sell = SellLimitOrder(trader_inst)
        limit_sell.update(order_type=TraderOrderType.SELL_LIMIT,
                          symbol="NANO/USDT",
                          current_price=70,
                          quantity=10,
                          price=70)

        # Test stop loss order
        stop_loss = StopLossOrder(trader_inst)
        stop_loss.update(order_type=TraderOrderType.STOP_LOSS,
                         symbol="BTC/USDT",
                         current_price=60,
                         quantity=10,
                         price=60)

        await trader_inst.create_order(market_buy)
        await trader_inst.create_order(stop_loss)
        await trader_inst.create_order(limit_sell)

        await trader_inst.notify_order_close(limit_sell, True)
        await trader_inst.notify_order_close(market_buy, True)

        assert market_buy not in orders_manager.get_open_orders()
        assert limit_sell not in orders_manager.get_open_orders()
        assert stop_loss in orders_manager.get_open_orders()

        await self.stop(exchange_manager)

    async def test_notify_sell_limit_order_cancel(self):
        _, exchange_manager, trader_inst = await self.init_default()
        portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
        initial_portfolio = copy.deepcopy(portfolio_manager.portfolio.portfolio)
        orders_manager = exchange_manager.exchange_personal_data.orders_manager

        # Test buy order
        limit_buy = create_order_instance(trader=trader_inst,
                                          order_type=TraderOrderType.BUY_LIMIT,
                                          symbol="BQX/BTC",
                                          current_price=4,
                                          quantity=2,
                                          price=4)

        await trader_inst.create_order(limit_buy, portfolio_manager.portfolio)

        await trader_inst.notify_order_close(limit_buy, True)

        assert limit_buy not in orders_manager.get_open_orders()

        assert initial_portfolio == portfolio_manager.portfolio.portfolio

        await self.stop(exchange_manager)

    async def test_notify_sell_limit_order_cancel_one_in_two(self):
        _, exchange_manager, trader_inst = await self.init_default()
        portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
        initial_portfolio = copy.deepcopy(portfolio_manager.portfolio.portfolio)
        orders_manager = exchange_manager.exchange_personal_data.orders_manager

        # Test buy order
        limit_buy = create_order_instance(trader=trader_inst,
                                          order_type=TraderOrderType.BUY_LIMIT,
                                          symbol="BQX/BTC",
                                          current_price=4,
                                          quantity=2,
                                          price=4)

        await trader_inst.create_order(limit_buy, portfolio_manager.portfolio)

        # Test second buy order
        second_limit_buy = create_order_instance(trader=trader_inst,
                                                 order_type=TraderOrderType.BUY_LIMIT,
                                                 symbol="VEN/BTC",
                                                 current_price=1,
                                                 quantity=1.5,
                                                 price=1)

        await trader_inst.create_order(second_limit_buy, portfolio_manager.portfolio)

        # Cancel only 1st one
        await trader_inst.notify_order_close(limit_buy, True)

        assert limit_buy not in orders_manager.get_open_orders()
        assert second_limit_buy in orders_manager.get_open_orders()

        assert initial_portfolio != portfolio_manager.portfolio
        assert portfolio_manager.portfolio.portfolio["BTC"][PORTFOLIO_AVAILABLE] == 8.5
        assert portfolio_manager.portfolio.portfolio["BTC"][PORTFOLIO_TOTAL] == 10

        await self.stop(exchange_manager)

    async def test_notify_sell_limit_order_fill(self):
        _, exchange_manager, trader_inst = await self.init_default()
        portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
        initial_portfolio = copy.deepcopy(portfolio_manager.portfolio.portfolio)
        orders_manager = exchange_manager.exchange_personal_data.orders_manager

        # Test buy order
        limit_buy = create_order_instance(trader=trader_inst,
                                          order_type=TraderOrderType.BUY_LIMIT,
                                          symbol="BQX/BTC",
                                          current_price=0.1,
                                          quantity=10,
                                          price=0.1)

        await trader_inst.create_order(limit_buy, portfolio_manager.portfolio)

        limit_buy.filled_price = limit_buy.origin_price
        limit_buy.filled_quantity = limit_buy.origin_quantity

        await trader_inst.notify_order_close(limit_buy)

        assert limit_buy not in orders_manager.get_open_orders()

        assert initial_portfolio != portfolio_manager.portfolio
        assert portfolio_manager.portfolio.portfolio["BTC"][PORTFOLIO_AVAILABLE] == 9
        assert portfolio_manager.portfolio.portfolio["BTC"][PORTFOLIO_TOTAL] == 9
        assert portfolio_manager.portfolio.portfolio["BQX"][PORTFOLIO_AVAILABLE] == 10
        assert portfolio_manager.portfolio.portfolio["BQX"][PORTFOLIO_TOTAL] == 10

        await self.stop(exchange_manager)

    async def test_notify_order_close_with_linked_orders(self):
        config, exchange_manager, trader_inst = await self.init_default()
        orders_manager = exchange_manager.exchange_personal_data.orders_manager

        # Test buy order
        market_buy = BuyMarketOrder(trader_inst)
        market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                          symbol="BTC/USDC",
                          current_price=70,
                          quantity=10,
                          price=70)

        # Test buy order
        limit_sell = SellLimitOrder(trader_inst)
        limit_sell.update(order_type=TraderOrderType.SELL_LIMIT,
                          symbol="NANO/USDT",
                          current_price=70,
                          quantity=10,
                          price=70)

        # Test stop loss order
        stop_loss = StopLossOrder(trader_inst)
        stop_loss.update(order_type=TraderOrderType.STOP_LOSS,
                         symbol="BTC/USDT",
                         current_price=60,
                         quantity=10,
                         price=60)

        stop_loss.linked_orders = [limit_sell]
        limit_sell.linked_orders = [stop_loss]

        await trader_inst.create_order(market_buy)
        await trader_inst.create_order(stop_loss)
        await trader_inst.create_order(limit_sell)

        await trader_inst.notify_order_close(limit_sell)

        assert market_buy in orders_manager.get_open_orders()
        assert stop_loss not in orders_manager.get_open_orders()
        assert limit_sell not in orders_manager.get_open_orders()

        await self.stop(exchange_manager)

    async def test_sell_all_currencies(self):
        _, exchange_manager, trader_inst = await self.init_default()
        portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager

        portfolio_manager.portfolio.portfolio["ADA"] = {
            PORTFOLIO_AVAILABLE: 1500,
            PORTFOLIO_TOTAL: 1500
        }
        portfolio_manager.portfolio.portfolio["USDT"] = {
            PORTFOLIO_AVAILABLE: 1000,
            PORTFOLIO_TOTAL: 1000
        }

        if not os.getenv('CYTHON_TEST_IGNORE'):
            with patch('octobot_trading.data_manager.prices_manager.PricesManager.get_mark_price',
                       new=AsyncMock(return_value=1)):
                orders = await trader_inst.sell_all()

            # 1 order to sell ada, 1 order to buy btc (sell usdt), NO order for usd (not in config pairs)
            assert len(orders) == 2

            sell_ADA_order = orders[0]
            assert sell_ADA_order.symbol == "ADA/BTC"
            assert sell_ADA_order.order_type == TraderOrderType.SELL_MARKET
            assert sell_ADA_order.origin_quantity == 1500

            sell_USDT_order = orders[1]
            assert sell_USDT_order.symbol == "BTC/USDT"
            assert sell_USDT_order.order_type == TraderOrderType.BUY_MARKET
            assert round(sell_USDT_order.origin_quantity, 8) == round(1000 / sell_USDT_order.origin_price, 8)

        await self.stop(exchange_manager)

    async def test_sell_all(self):
        _, exchange_manager, trader_inst = await self.init_default()
        portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager

        portfolio_manager.portfolio.portfolio["ADA"] = {
            PORTFOLIO_AVAILABLE: 1500,
            PORTFOLIO_TOTAL: 1500
        }
        portfolio_manager.portfolio.portfolio["USDT"] = {
            PORTFOLIO_AVAILABLE: 1000,
            PORTFOLIO_TOTAL: 1000
        }

        if not os.getenv('CYTHON_TEST_IGNORE'):
            with patch('octobot_trading.data_manager.prices_manager.PricesManager.get_mark_price',
                       new=AsyncMock(return_value=1)):
                orders = await trader_inst.sell_all(currencies_to_sell=["USDT"], timeout=1)
            assert len(orders) == 1

            sell_USDT_order = orders[0]
            assert sell_USDT_order.symbol == "BTC/USDT"
            assert sell_USDT_order.order_type == TraderOrderType.BUY_MARKET
            assert round(sell_USDT_order.origin_quantity, 8) == round(1000 / sell_USDT_order.origin_price, 8)

        if not os.getenv('CYTHON_TEST_IGNORE'):
            with patch('octobot_trading.data_manager.prices_manager.PricesManager.get_mark_price',
                       new=AsyncMock(return_value=1)):
                orders = await trader_inst.sell_all(currencies_to_sell=["ADA"])
            assert len(orders) == 1

            sell_ADA_order = orders[0]
            assert sell_ADA_order.symbol == "ADA/BTC"
            assert sell_ADA_order.order_type == TraderOrderType.SELL_MARKET
            assert sell_ADA_order.origin_quantity == 1500
            assert round(sell_USDT_order.origin_quantity, 8) == round(1000 / sell_USDT_order.origin_price, 8)

        if not os.getenv('CYTHON_TEST_IGNORE'):
            # currency not in portfolio
            with patch('octobot_trading.data_manager.prices_manager.PricesManager.get_mark_price',
                       new=AsyncMock(return_value=1)):
                orders = await trader_inst.sell_all(currencies_to_sell=["XBT"])
            assert len(orders) == 0

            portfolio_manager.portfolio.portfolio["XRP"] = {
                PORTFOLIO_AVAILABLE: 0,
                PORTFOLIO_TOTAL: 0
            }

        if not os.getenv('CYTHON_TEST_IGNORE'):
            # currency in portfolio but with 0 quantity
            with patch('octobot_trading.data_manager.prices_manager.PricesManager.get_mark_price',
                       new=AsyncMock(return_value=1)):
                orders = await trader_inst.sell_all(currencies_to_sell=["XRP"])
            assert len(orders) == 0

        if not os.getenv('CYTHON_TEST_IGNORE'):
            # invalid currency
            with patch('octobot_trading.data_manager.prices_manager.PricesManager.get_mark_price',
                       new=AsyncMock(return_value=1)):
                orders = await trader_inst.sell_all(currencies_to_sell=[""])
            assert len(orders) == 0

            portfolio_manager.portfolio.portfolio["ICX"] = {
                PORTFOLIO_AVAILABLE: 0.0000001,
                PORTFOLIO_TOTAL: 0.0000001
            }

        if not os.getenv('CYTHON_TEST_IGNORE'):
            # currency in portfolio but with close to 0 quantity
            with patch('octobot_trading.data_manager.prices_manager.PricesManager.get_mark_price',
                       new=AsyncMock(return_value=1)):
                orders = await trader_inst.sell_all(currencies_to_sell=["ICX"])
            assert len(orders) == 0

        await self.stop(exchange_manager)

    async def test_parse_exchange_order_to_trade_instance(self):
        _, exchange_manager, trader_inst = await self.init_default()

        timestamp = time.time()
        order_to_test = Order(trader_inst)
        exchange_order = {
            "status": OrderStatus.PARTIALLY_FILLED.value,
            "symbol": self.DEFAULT_SYMBOL,
            # "fee": 0.001,
            "price": 10.1444215411,
            "cost": 100.1444215411,
            "filled": 1.568415145687741563132,
            "timestamp": timestamp
        }

        order_to_test.update_from_raw(exchange_order)

        assert order_to_test.status == OrderStatus.PARTIALLY_FILLED
        assert order_to_test.filled_quantity == 1.568415145687741563132
        assert order_to_test.filled_price == 10.1444215411
        # assert order_to_test.fee == 0.001
        assert order_to_test.total_cost == 100.1444215411

        await self.stop(exchange_manager)

    async def test_parse_exchange_order_to_order_instance(self):
        _, exchange_manager, trader_inst = await self.init_default()

        timestamp = time.time()

        exchange_order = {
            "side": TradeOrderSide.SELL.value,
            "type": TradeOrderType.LIMIT.value,
            "symbol": self.DEFAULT_SYMBOL,
            "amount": 1564.7216721637,
            "filled": 15.15467,
            "id": "1546541123",
            "status": OrderStatus.OPEN.value,
            "price": 10254.4515,
            "timestamp": timestamp
        }

        order_to_test = create_order_instance_from_raw(trader_inst, exchange_order)

        assert order_to_test.order_type == TraderOrderType.SELL_LIMIT
        assert order_to_test.status == OrderStatus.OPEN
        assert order_to_test.linked_to is None
        assert order_to_test.origin_stop_price == 0.0
        assert order_to_test.origin_quantity == 1564.7216721637
        assert order_to_test.origin_price == 10254.4515
        assert order_to_test.filled_quantity == 15.15467
        assert order_to_test.creation_time != 0.0
        assert order_to_test.order_id == "1546541123"

        await self.stop(exchange_manager)


def make_coroutine(response):
    async def coroutine(*args, **kwargs):
        return response

    return coroutine
