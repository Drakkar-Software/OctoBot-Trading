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
import copy
import os
import ccxt.async_support
import decimal

import pytest
import time
from mock import AsyncMock, patch, Mock

from tests import event_loop
import octobot_commons.constants as commons_constants
from octobot_commons.asyncio_tools import wait_asyncio_next_cycle
from octobot_commons.tests.test_config import load_test_config
from octobot_trading.personal_data.orders import Order
from octobot_trading.enums import TraderOrderType, TradeOrderSide, TradeOrderType, OrderStatus, FeePropertyColumns
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.personal_data.orders.order_factory import create_order_instance, create_order_instance_from_raw
from octobot_trading.personal_data.orders import BuyLimitOrder, BuyMarketOrder, SellLimitOrder, StopLossOrder
from octobot_trading.personal_data.orders.types.market.sell_market_order import SellMarketOrder
import octobot_trading.personal_data.portfolios.assets as portfolio_assets
from octobot_trading.exchanges.traders.trader import Trader
from octobot_trading.exchanges.traders.trader_simulator import TraderSimulator
from octobot_trading.api.exchange import cancel_ccxt_throttle_task
import octobot_trading.constants as constants

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

FEES_MOCK = {
    FeePropertyColumns.COST.value: 0.1,
    FeePropertyColumns.CURRENCY.value: "BQX"
}


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

        # set afterwards backtesting attribute to force orders instant initialization
        exchange_manager.is_backtesting = True

        return config, exchange_manager, trader

    @staticmethod
    async def stop(exchange_manager):
        cancel_ccxt_throttle_task()
        await exchange_manager.stop()
        # let updaters gracefully shutdown
        await wait_asyncio_next_cycle()

    async def test_enabled(self):
        config, exchange_manager, trader_inst = await self.init_default()
        await self.stop(exchange_manager)

        config[commons_constants.CONFIG_TRADER][commons_constants.CONFIG_ENABLED_OPTION] = True
        assert Trader.enabled(config)

        config[commons_constants.CONFIG_TRADER][commons_constants.CONFIG_ENABLED_OPTION] = False
        assert not Trader.enabled(config)
        await self.stop(exchange_manager)

    async def test_get_risk(self):
        config, exchange_manager, trader_inst = await self.init_default()
        await self.stop(exchange_manager)

        config[commons_constants.CONFIG_TRADING][commons_constants.CONFIG_TRADER_RISK] = 0
        trader_1 = TraderSimulator(config, exchange_manager)
        assert round(trader_1.risk, 2) == decimal.Decimal(str(commons_constants.CONFIG_TRADER_RISK_MIN))
        await self.stop(exchange_manager)

        config[commons_constants.CONFIG_TRADING][commons_constants.CONFIG_TRADER_RISK] = 2
        trader_2 = TraderSimulator(config, exchange_manager)
        assert trader_2.risk == decimal.Decimal(str(commons_constants.CONFIG_TRADER_RISK_MAX))
        await self.stop(exchange_manager)

        config[commons_constants.CONFIG_TRADING][commons_constants.CONFIG_TRADER_RISK] = 0.5
        trader_2 = TraderSimulator(config, exchange_manager)
        assert trader_2.risk == decimal.Decimal(str(0.5))
        await self.stop(exchange_manager)

    async def test_cancel_limit_order(self):
        _, exchange_manager, trader_inst = await self.init_default()
        orders_manager = exchange_manager.exchange_personal_data.orders_manager

        # Test buy order
        limit_buy = BuyLimitOrder(trader_inst)
        limit_buy.update(order_type=TraderOrderType.BUY_LIMIT,
                         symbol=self.DEFAULT_SYMBOL,
                         current_price=decimal.Decimal("70"),
                         quantity=decimal.Decimal("10"),
                         price=decimal.Decimal("70"))

        assert limit_buy not in orders_manager.get_open_orders()

        assert await trader_inst.create_order(limit_buy)

        assert limit_buy in orders_manager.get_open_orders()

        assert await trader_inst.cancel_order(limit_buy) is True

        assert limit_buy not in orders_manager.get_open_orders()

        await self.stop(exchange_manager)

    async def test_cancel_stop_order(self):
        _, exchange_manager, trader_inst = await self.init_default()
        orders_manager = exchange_manager.exchange_personal_data.orders_manager

        # Test buy order
        stop_order = StopLossOrder(trader_inst)
        stop_order.update(order_type=TraderOrderType.STOP_LOSS,
                          symbol=self.DEFAULT_SYMBOL,
                          current_price=decimal.Decimal("70"),
                          quantity=decimal.Decimal("10"),
                          price=decimal.Decimal("70"))

        assert stop_order not in orders_manager.get_open_orders()

        assert await trader_inst.create_order(stop_order)

        assert stop_order in orders_manager.get_open_orders()

        assert await trader_inst.cancel_order(stop_order) is True

        assert stop_order not in orders_manager.get_open_orders()

        await self.stop(exchange_manager)

    async def test_cancel_closed_order(self):
        _, exchange_manager, trader_inst = await self.init_default()

        # Test buy order
        limit_buy = BuyLimitOrder(trader_inst)
        limit_buy.update(order_type=TraderOrderType.SELL_LIMIT,
                         symbol=self.DEFAULT_SYMBOL,
                         current_price=decimal.Decimal("70"),
                         quantity=decimal.Decimal("10"),
                         price=decimal.Decimal("70"))

        # 1. cancel order: success
        assert await trader_inst.cancel_order(limit_buy) is True
        # 2. re-cancel order: failure (already cancelled)
        assert await trader_inst.cancel_order(limit_buy) is False

        await self.stop(exchange_manager)

    async def test_cancel_open_orders_default_symbol(self):
        config, exchange_manager, trader_inst = await self.init_default()
        orders_manager = exchange_manager.exchange_personal_data.orders_manager
        trades_manager = exchange_manager.exchange_personal_data.trades_manager
        portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
        initial_portfolio = copy.deepcopy(portfolio_manager.portfolio.portfolio)

        # Test buy order
        limit_buy_1 = BuyLimitOrder(trader_inst)
        limit_buy_1.update(order_type=TraderOrderType.BUY_LIMIT,
                           symbol=self.DEFAULT_SYMBOL,
                           current_price=decimal.Decimal("70"),
                           quantity=decimal.Decimal("10"),
                           price=decimal.Decimal("70"))

        # Test sell order
        limit_sell = SellLimitOrder(trader_inst)
        limit_sell.update(order_type=TraderOrderType.SELL_LIMIT,
                          symbol=self.DEFAULT_SYMBOL,
                          current_price=decimal.Decimal("70"),
                          quantity=decimal.Decimal("10"),
                          price=decimal.Decimal("70"))

        # Test buy order
        limit_buy_2 = BuyLimitOrder(trader_inst)
        limit_buy_2.update(order_type=TraderOrderType.BUY_LIMIT,
                           symbol=self.DEFAULT_SYMBOL,
                           current_price=decimal.Decimal("30"),
                           quantity=decimal.Decimal("10"),
                           price=decimal.Decimal("30"))

        await trader_inst.create_order(limit_buy_1)
        await trader_inst.create_order(limit_sell)
        await trader_inst.create_order(limit_buy_2)

        assert limit_buy_1 in orders_manager.get_open_orders()
        assert limit_sell in orders_manager.get_open_orders()
        assert limit_buy_2 in orders_manager.get_open_orders()

        assert not trades_manager.trades

        assert await trader_inst.cancel_open_orders(self.DEFAULT_SYMBOL) is True

        assert limit_buy_1 not in orders_manager.get_open_orders()
        assert limit_sell not in orders_manager.get_open_orders()
        assert limit_buy_2 not in orders_manager.get_open_orders()

        # added cancelled orders as cancelled trades
        assert len(trades_manager.trades) == 3
        assert all(trade.status is OrderStatus.CANCELED
                   for trade in trades_manager.trades.values())
        assert all(
            portfolio_manager.portfolio.portfolio[currency] == initial_portfolio[currency]
            for currency in portfolio_manager.portfolio.portfolio.keys()
        )

        await self.stop(exchange_manager)

    async def test_cancel_open_orders_multi_symbol(self):
        config, exchange_manager, trader_inst = await self.init_default()
        orders_manager = exchange_manager.exchange_personal_data.orders_manager
        trades_manager = exchange_manager.exchange_personal_data.trades_manager

        # Test buy order
        market_buy = BuyMarketOrder(trader_inst)
        market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                          symbol="BTC/USDC",
                          current_price=decimal.Decimal("70"),
                          quantity=decimal.Decimal("10"),
                          price=decimal.Decimal("70"))

        # Test buy order
        limit_sell = SellLimitOrder(trader_inst)
        limit_sell.update(order_type=TraderOrderType.SELL_LIMIT,
                          symbol="NANO/USDT",
                          current_price=decimal.Decimal("70"),
                          quantity=decimal.Decimal("10"),
                          price=decimal.Decimal("70"))

        # Test sell order
        market_sell = SellMarketOrder(trader_inst)
        market_sell.update(order_type=TraderOrderType.SELL_MARKET,
                           symbol=self.DEFAULT_SYMBOL,
                           current_price=decimal.Decimal("70"),
                           quantity=decimal.Decimal("10"),
                           price=decimal.Decimal("70"))

        # Test buy order
        limit_buy = BuyLimitOrder(trader_inst)
        limit_buy.update(order_type=TraderOrderType.BUY_LIMIT,
                         symbol=self.DEFAULT_SYMBOL,
                         current_price=decimal.Decimal("70"),
                         quantity=decimal.Decimal("10"),
                         price=decimal.Decimal("70"))

        await trader_inst.create_order(market_buy)
        await trader_inst.create_order(market_sell)
        await trader_inst.create_order(limit_buy)
        await trader_inst.create_order(limit_sell)

        # market orders not in open orders as they are instantly filled
        assert market_buy not in orders_manager.get_open_orders()
        assert market_sell not in orders_manager.get_open_orders()

        assert limit_buy in orders_manager.get_open_orders()
        assert limit_sell in orders_manager.get_open_orders()

        assert len(trades_manager.trades) == 2

        assert await trader_inst.cancel_open_orders(self.DEFAULT_SYMBOL) is True

        assert limit_buy not in orders_manager.get_open_orders()
        assert limit_sell in orders_manager.get_open_orders()

        # added cancelled orders as cancelled trades
        assert len(trades_manager.trades) == 3

        await self.stop(exchange_manager)

    async def test_cancel_all_open_orders_with_currency(self):
        config, exchange_manager, trader_inst = await self.init_default()
        orders_manager = exchange_manager.exchange_personal_data.orders_manager
        trades_manager = exchange_manager.exchange_personal_data.trades_manager

        # Test buy order
        market_buy = BuyMarketOrder(trader_inst)
        market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                          symbol="BTC/USDC",
                          current_price=decimal.Decimal("70"),
                          quantity=decimal.Decimal("10"),
                          price=decimal.Decimal("70"))

        # Test buy order
        limit_sell = SellLimitOrder(trader_inst)
        limit_sell.update(order_type=TraderOrderType.SELL_LIMIT,
                          symbol="XRP/BTC",
                          current_price=decimal.Decimal("70"),
                          quantity=decimal.Decimal("10"),
                          price=decimal.Decimal("70"))

        # Test sell order
        market_sell = SellMarketOrder(trader_inst)
        market_sell.update(order_type=TraderOrderType.SELL_MARKET,
                           symbol=self.DEFAULT_SYMBOL,
                           current_price=decimal.Decimal("70"),
                           quantity=decimal.Decimal("10"),
                           price=decimal.Decimal("70"))

        # Test buy order
        limit_buy = BuyLimitOrder(trader_inst)
        limit_buy.update(order_type=TraderOrderType.BUY_LIMIT,
                         symbol=self.DEFAULT_SYMBOL,
                         current_price=decimal.Decimal("70"),
                         quantity=decimal.Decimal("10"),
                         price=decimal.Decimal("70"))

        # create order notifier to prevent None call
        await trader_inst.create_order(market_buy)
        await trader_inst.create_order(market_sell)
        await trader_inst.create_order(limit_buy)
        await trader_inst.create_order(limit_sell)

        # market orders not in open orders as they are instantly filled
        assert market_buy not in orders_manager.get_open_orders()
        assert market_sell not in orders_manager.get_open_orders()
        assert limit_buy in orders_manager.get_open_orders()
        assert limit_sell in orders_manager.get_open_orders()

        assert len(trades_manager.trades) == 2

        assert await trader_inst.cancel_all_open_orders_with_currency("XYZ") is True

        assert limit_buy in orders_manager.get_open_orders()
        assert limit_sell in orders_manager.get_open_orders()

        assert len(trades_manager.trades) == 2

        assert await trader_inst.cancel_all_open_orders_with_currency("XRP") is True

        assert limit_buy in orders_manager.get_open_orders()
        assert limit_sell not in orders_manager.get_open_orders()

        # added cancelled orders as cancelled trades
        assert len(trades_manager.trades) == 3

        await trader_inst.cancel_all_open_orders_with_currency("USDT")

        assert limit_buy not in orders_manager.get_open_orders()
        assert limit_sell not in orders_manager.get_open_orders()

        # added cancelled orders as cancelled trades
        assert len(trades_manager.trades) == 4

        await trader_inst.cancel_all_open_orders_with_currency("BTC")

        assert market_buy not in orders_manager.get_open_orders()
        assert market_sell not in orders_manager.get_open_orders()
        assert limit_buy not in orders_manager.get_open_orders()
        assert limit_sell not in orders_manager.get_open_orders()

        # added cancelled orders as cancelled trades
        assert len(trades_manager.trades) == 4

        await self.stop(exchange_manager)

    async def test_close_filled_order(self):
        config, exchange_manager, trader_inst = await self.init_default()
        orders_manager = exchange_manager.exchange_personal_data.orders_manager
        trades_manager = exchange_manager.exchange_personal_data.trades_manager

        # Test buy order
        market_buy = BuyMarketOrder(trader_inst)
        market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                          symbol="BTC/USDC",
                          current_price=decimal.Decimal("70"),
                          quantity=decimal.Decimal("10"),
                          price=decimal.Decimal("70"))

        # Test buy order
        limit_sell = SellLimitOrder(trader_inst)
        limit_sell.update(order_type=TraderOrderType.SELL_LIMIT,
                          symbol="NANO/USDT",
                          current_price=decimal.Decimal("70"),
                          quantity=decimal.Decimal("10"),
                          price=decimal.Decimal("70"))

        # Test stop loss order
        stop_loss = StopLossOrder(trader_inst)
        stop_loss.update(order_type=TraderOrderType.STOP_LOSS,
                         symbol="BTC/USDT",
                         current_price=decimal.Decimal("60"),
                         quantity=decimal.Decimal("10"),
                         price=decimal.Decimal("60"))

        await trader_inst.create_order(market_buy)
        await trader_inst.create_order(stop_loss)
        await trader_inst.create_order(limit_sell)

        assert len(trades_manager.trades) == 1

        await limit_sell.on_fill(force_fill=True)

        # market orders not in open orders as they are instantly filled
        assert market_buy not in orders_manager.get_open_orders()
        assert limit_sell not in orders_manager.get_open_orders()
        assert stop_loss in orders_manager.get_open_orders()

        # added filled orders as filled trades
        assert len(trades_manager.trades) == 2
        assert trades_manager.get_trade(market_buy.order_id).status is OrderStatus.FILLED
        assert trades_manager.get_trade(limit_sell.order_id).status is OrderStatus.FILLED

        await self.stop(exchange_manager)

    async def test_close_filled_buy_limit_order(self):
        _, exchange_manager, trader_inst = await self.init_default()
        portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
        initial_portfolio = copy.deepcopy(portfolio_manager.portfolio.portfolio)
        orders_manager = exchange_manager.exchange_personal_data.orders_manager
        trades_manager = exchange_manager.exchange_personal_data.trades_manager

        # Test buy order
        limit_buy = create_order_instance(trader=trader_inst,
                                          order_type=TraderOrderType.BUY_LIMIT,
                                          symbol="BQX/BTC",
                                          current_price=decimal.Decimal("4"),
                                          quantity=decimal.Decimal("2"),
                                          price=decimal.Decimal("4"))

        await trader_inst.create_order(limit_buy, portfolio_manager.portfolio)

        assert not trades_manager.trades

        await limit_buy.on_fill(force_fill=True)

        assert limit_buy not in orders_manager.get_open_orders()

        assert not initial_portfolio == portfolio_manager.portfolio.portfolio

        # added filled orders as filled trades
        assert len(trades_manager.trades) == 1
        assert all(trade.status is limit_buy.status for trade in trades_manager.trades.values())

        await self.stop(exchange_manager)

    async def test_close_filled_stop_sell_order(self):
        _, exchange_manager, trader_inst = await self.init_default()
        portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
        initial_portfolio = copy.deepcopy(portfolio_manager.portfolio.portfolio)
        orders_manager = exchange_manager.exchange_personal_data.orders_manager
        trades_manager = exchange_manager.exchange_personal_data.trades_manager

        # Test buy order
        stop_order = create_order_instance(trader=trader_inst,
                                           order_type=TraderOrderType.BUY_LIMIT,
                                           symbol="BQX/BTC",
                                           current_price=decimal.Decimal("4"),
                                           quantity=decimal.Decimal("2"),
                                           price=decimal.Decimal("4"),
                                           side=TradeOrderSide.SELL)

        await trader_inst.create_order(stop_order, portfolio_manager.portfolio)

        assert not trades_manager.trades

        await stop_order.on_fill(force_fill=True)

        assert stop_order not in orders_manager.get_open_orders()

        assert not initial_portfolio == portfolio_manager.portfolio.portfolio

        # added filled orders as filled trades
        assert len(trades_manager.trades) == 1
        assert all(trade.status is stop_order.status for trade in trades_manager.trades.values())

        await self.stop(exchange_manager)

    async def test_close_filled_stop_buy_order(self):
        _, exchange_manager, trader_inst = await self.init_default()
        portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
        initial_portfolio = copy.deepcopy(portfolio_manager.portfolio.portfolio)
        orders_manager = exchange_manager.exchange_personal_data.orders_manager
        trades_manager = exchange_manager.exchange_personal_data.trades_manager

        # Test buy order
        stop_order = create_order_instance(trader=trader_inst,
                                           order_type=TraderOrderType.BUY_LIMIT,
                                           symbol="BQX/BTC",
                                           current_price=decimal.Decimal("4"),
                                           quantity=decimal.Decimal("2"),
                                           price=decimal.Decimal("4"),
                                           side=TradeOrderSide.BUY)

        await trader_inst.create_order(stop_order, portfolio_manager.portfolio)

        assert not trades_manager.trades

        await stop_order.on_fill(force_fill=True)

        assert stop_order not in orders_manager.get_open_orders()

        assert not initial_portfolio == portfolio_manager.portfolio.portfolio

        # added filled orders as filled trades
        assert len(trades_manager.trades) == 1
        assert all(trade.status is stop_order.status for trade in trades_manager.trades.values())

        await self.stop(exchange_manager)

    async def test_close_filled_sell_limit_order_one_in_two(self):
        _, exchange_manager, trader_inst = await self.init_default()
        portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
        initial_portfolio = copy.deepcopy(portfolio_manager.portfolio.portfolio)
        orders_manager = exchange_manager.exchange_personal_data.orders_manager
        trades_manager = exchange_manager.exchange_personal_data.trades_manager

        # Test buy order
        limit_buy = create_order_instance(trader=trader_inst,
                                          order_type=TraderOrderType.BUY_LIMIT,
                                          symbol="BQX/BTC",
                                          current_price=decimal.Decimal("4"),
                                          quantity=decimal.Decimal("2"),
                                          price=decimal.Decimal("4"))

        await trader_inst.create_order(limit_buy, portfolio_manager.portfolio)

        # Test second buy order
        second_limit_buy = create_order_instance(trader=trader_inst,
                                                 order_type=TraderOrderType.BUY_LIMIT,
                                                 symbol="VEN/BTC",
                                                 current_price=decimal.Decimal("1"),
                                                 quantity=decimal.Decimal("1.5"),
                                                 price=decimal.Decimal("1"))

        await trader_inst.create_order(second_limit_buy, portfolio_manager.portfolio)

        assert not trades_manager.trades

        with pytest.raises(KeyError):
            assert portfolio_manager.portfolio.portfolio["BQX"].available == 0
        assert portfolio_manager.portfolio.portfolio["BTC"].available == 0.5

        # Fill only 1st one
        limit_buy.filled_price = 4
        limit_buy.status = OrderStatus.FILLED
        with patch.object(ccxt.async_support.binance, "calculate_fee", Mock(return_value=FEES_MOCK)) \
                as calculate_fee_mock:
            await limit_buy.on_fill(force_fill=True)
            # ensure call ccxt calculate_fee for order fees
            calculate_fee_mock.assert_called_once()

        # added filled orders as filled trades
        assert len(trades_manager.trades) == 1
        assert all(trade.status is OrderStatus.FILLED for trade in trades_manager.trades.values())

        assert limit_buy not in orders_manager.get_open_orders()
        assert second_limit_buy in orders_manager.get_open_orders()

        assert initial_portfolio != portfolio_manager.portfolio
        # (mocked) fees are taken into account
        assert portfolio_manager.portfolio.portfolio["BQX"].available == decimal.Decimal(str(2 - 0.1))
        assert portfolio_manager.portfolio.portfolio["BTC"].available == decimal.Decimal("0.5")
        assert portfolio_manager.portfolio.portfolio["BTC"].total == decimal.Decimal("2")

        await self.stop(exchange_manager)

    async def test_close_filled_sell_limit_order(self):
        _, exchange_manager, trader_inst = await self.init_default()
        portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
        initial_portfolio = copy.deepcopy(portfolio_manager.portfolio.portfolio)
        orders_manager = exchange_manager.exchange_personal_data.orders_manager
        trades_manager = exchange_manager.exchange_personal_data.trades_manager

        # Test buy order
        limit_buy = create_order_instance(trader=trader_inst,
                                          order_type=TraderOrderType.BUY_LIMIT,
                                          symbol="BQX/BTC",
                                          current_price=decimal.Decimal("0.1"),
                                          quantity=decimal.Decimal("10"),
                                          price=decimal.Decimal("0.1"))

        await trader_inst.create_order(limit_buy, portfolio_manager.portfolio)

        limit_buy.filled_price = limit_buy.origin_price
        limit_buy.filled_quantity = limit_buy.origin_quantity
        limit_buy.status = OrderStatus.FILLED

        assert not trades_manager.trades

        with patch.object(ccxt.async_support.binance, "calculate_fee", Mock(return_value=FEES_MOCK)) \
                as calculate_fee_mock:
            await limit_buy.on_fill(force_fill=True)
            calculate_fee_mock.assert_called_once()

        assert limit_buy not in orders_manager.get_open_orders()

        # added filled orders as filled trades
        assert len(trades_manager.trades) == 1
        assert all(trade.status is OrderStatus.FILLED for trade in trades_manager.trades.values())

        assert initial_portfolio != portfolio_manager.portfolio
        assert portfolio_manager.portfolio.portfolio["BTC"].available == decimal.Decimal("9")
        assert portfolio_manager.portfolio.portfolio["BTC"].total == decimal.Decimal("9")
        # 0.1 as fee
        assert portfolio_manager.portfolio.portfolio["BQX"].available == decimal.Decimal("9.9")
        assert portfolio_manager.portfolio.portfolio["BQX"].total == decimal.Decimal("9.9")

        await self.stop(exchange_manager)

    async def test_close_filled_order_with_linked_orders(self):
        config, exchange_manager, trader_inst = await self.init_default()
        orders_manager = exchange_manager.exchange_personal_data.orders_manager
        trades_manager = exchange_manager.exchange_personal_data.trades_manager

        # Test buy order
        market_buy = BuyMarketOrder(trader_inst)
        market_buy.update(order_type=TraderOrderType.BUY_MARKET,
                          symbol="BTC/USDC",
                          current_price=decimal.Decimal("70"),
                          quantity=decimal.Decimal("10"),
                          price=decimal.Decimal("70"))

        # Test buy order
        limit_sell = SellLimitOrder(trader_inst)
        limit_sell.update(order_type=TraderOrderType.SELL_LIMIT,
                          symbol="NANO/USDT",
                          current_price=decimal.Decimal("70"),
                          quantity=decimal.Decimal("10"),
                          price=decimal.Decimal("70"))

        # Test stop loss order
        stop_loss = StopLossOrder(trader_inst)
        stop_loss.update(order_type=TraderOrderType.STOP_LOSS,
                         symbol="BTC/USDT",
                         current_price=decimal.Decimal("60"),
                         quantity=decimal.Decimal("10"),
                         price=decimal.Decimal("60"))

        stop_loss.linked_orders = [limit_sell]
        limit_sell.linked_orders = [stop_loss]

        await trader_inst.create_order(market_buy)
        await trader_inst.create_order(stop_loss)
        await trader_inst.create_order(limit_sell)

        assert len(trades_manager.trades) == 1

        limit_sell.filled_price = limit_sell.origin_price
        limit_sell.status = OrderStatus.FILLED
        await limit_sell.on_fill(force_fill=True)

        assert market_buy not in orders_manager.get_open_orders()
        assert stop_loss not in orders_manager.get_open_orders()
        assert limit_sell not in orders_manager.get_open_orders()

        # added filled orders as filled trades
        assert len(trades_manager.trades) == 3
        assert trades_manager.get_trade(market_buy.order_id).status is OrderStatus.FILLED
        assert trades_manager.get_trade(limit_sell.order_id).status is OrderStatus.FILLED
        assert trades_manager.get_trade(stop_loss.order_id).status is OrderStatus.CANCELED
        with pytest.raises(KeyError):
            trades_manager.get_trade(f"{market_buy.order_id}1")

        await self.stop(exchange_manager)

    async def test_sell_all_currencies(self):
        _, exchange_manager, trader_inst = await self.init_default()
        portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager

        portfolio_manager.portfolio.portfolio["ADA"] = portfolio_assets.SpotAsset(
            name="ADA",
            available=decimal.Decimal("1500"),
            total=decimal.Decimal("1500")
        )

        portfolio_manager.portfolio.portfolio["USDT"] = portfolio_assets.SpotAsset(
            name="USDT",
            available=decimal.Decimal("1000"),
            total=decimal.Decimal("1000")
        )

        if not os.getenv('CYTHON_IGNORE'):
            with patch('octobot_trading.exchange_data.prices.prices_manager.PricesManager.get_mark_price',
                       new=AsyncMock(return_value=1)):
                orders = await trader_inst.sell_all()

            # 1 order to sell ada, 1 order to buy btc (sell usdt), NO order for usd (not in config pairs)
            assert len(orders) == 2

            if orders[0].symbol == "ADA/BTC":
                sell_ADA_order = orders[0]
                sell_USDT_order = orders[1]
            else:
                sell_ADA_order = orders[1]
                sell_USDT_order = orders[0]

            assert sell_ADA_order.symbol == "ADA/BTC"
            assert sell_ADA_order.order_type == TraderOrderType.SELL_MARKET
            assert sell_ADA_order.origin_quantity == decimal.Decimal("1500")

            assert sell_USDT_order.symbol == "BTC/USDT"
            assert sell_USDT_order.order_type == TraderOrderType.BUY_MARKET
            assert round(sell_USDT_order.origin_quantity, 8) == round(1000 / sell_USDT_order.origin_price, 8)
            # let market orders get filled before stopping exchange
            await wait_asyncio_next_cycle()

        await self.stop(exchange_manager)

    async def test_sell_all(self):
        _, exchange_manager, trader_inst = await self.init_default()
        portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager

        portfolio_manager.portfolio.portfolio["ADA"] = portfolio_assets.SpotAsset(
            name="ADA",
            available=decimal.Decimal("1500"),
            total=decimal.Decimal("1500")
        )

        portfolio_manager.portfolio.portfolio["USDT"] = portfolio_assets.SpotAsset(
            name="USDT",
            available=decimal.Decimal("1000"),
            total=decimal.Decimal("1000")
        )

        if not os.getenv('CYTHON_IGNORE'):
            with patch('octobot_trading.exchange_data.prices.prices_manager.PricesManager.get_mark_price',
                       new=AsyncMock(return_value=1)):
                orders = await trader_inst.sell_all(currencies_to_sell=["USDT"], timeout=1)
            assert len(orders) == 1

            sell_USDT_order = orders[0]
            assert sell_USDT_order.symbol == "BTC/USDT"
            assert sell_USDT_order.order_type == TraderOrderType.BUY_MARKET
            assert round(sell_USDT_order.origin_quantity, 8) == round(1000 / sell_USDT_order.origin_price, 8)

        if not os.getenv('CYTHON_IGNORE'):
            with patch('octobot_trading.exchange_data.prices.prices_manager.PricesManager.get_mark_price',
                       new=AsyncMock(return_value=1)):
                orders = await trader_inst.sell_all(currencies_to_sell=["ADA"])
            assert len(orders) == 1

            sell_ADA_order = orders[0]
            assert sell_ADA_order.symbol == "ADA/BTC"
            assert sell_ADA_order.order_type == TraderOrderType.SELL_MARKET
            assert sell_ADA_order.origin_quantity == 1500
            assert round(sell_USDT_order.origin_quantity, 8) == round(1000 / sell_USDT_order.origin_price, 8)

        if not os.getenv('CYTHON_IGNORE'):
            # currency not in portfolio
            with patch('octobot_trading.exchange_data.prices.prices_manager.PricesManager.get_mark_price',
                       new=AsyncMock(return_value=1)):
                orders = await trader_inst.sell_all(currencies_to_sell=["XBT"])
            assert len(orders) == 0

            portfolio_manager.portfolio.portfolio["XRP"] = portfolio_assets.SpotAsset(
                name="XRP",
                available=constants.ZERO,
                total=constants.ZERO
            )

        if not os.getenv('CYTHON_IGNORE'):
            # currency in portfolio but with 0 quantity
            with patch('octobot_trading.exchange_data.prices.prices_manager.PricesManager.get_mark_price',
                       new=AsyncMock(return_value=1)):
                orders = await trader_inst.sell_all(currencies_to_sell=["XRP"])
            assert len(orders) == 0

        if not os.getenv('CYTHON_IGNORE'):
            # invalid currency
            with patch('octobot_trading.exchange_data.prices.prices_manager.PricesManager.get_mark_price',
                       new=AsyncMock(return_value=1)):
                orders = await trader_inst.sell_all(currencies_to_sell=[""])
            assert len(orders) == 0

            portfolio_manager.portfolio.portfolio["ICX"] = portfolio_assets.SpotAsset(
                name="ICX",
                available=decimal.Decimal("0.0000001"),
                total=decimal.Decimal("0.0000001")
            )

        if not os.getenv('CYTHON_IGNORE'):
            # currency in portfolio but with close to 0 quantity
            with patch('octobot_trading.exchange_data.prices.prices_manager.PricesManager.get_mark_price',
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
        assert order_to_test.filled_quantity == decimal.Decimal("1.5684151456877415")
        assert order_to_test.filled_price == decimal.Decimal("10.1444215411")
        # assert order_to_test.fee == 0.001
        assert order_to_test.total_cost == decimal.Decimal("100.1444215411")

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
        assert order_to_test.origin_stop_price == constants.ZERO
        assert order_to_test.origin_quantity == decimal.Decimal("1564.7216721637")
        assert order_to_test.origin_price == decimal.Decimal("10254.4515")
        assert order_to_test.filled_quantity == decimal.Decimal("15.15467")
        assert order_to_test.creation_time != constants.ZERO
        assert order_to_test.order_id == "1546541123"

        await self.stop(exchange_manager)


def make_coroutine(response):
    async def coroutine(*args, **kwargs):
        return response

    return coroutine
