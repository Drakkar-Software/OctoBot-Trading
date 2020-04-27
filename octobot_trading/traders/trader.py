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
import time

from octobot_commons.logging.logging_util import get_logger
from octobot_trading.constants import REAL_TRADER_STR, CONFIG_TRADER_RISK, CONFIG_TRADING, CONFIG_TRADER_RISK_MIN, \
    CONFIG_TRADER_RISK_MAX
from octobot_trading.data.order import Order
from octobot_trading.data.portfolio import Portfolio
from octobot_trading.enums import OrderStatus, TraderOrderType
from octobot_trading.orders.order_adapter import check_and_adapt_order_details_if_necessary
from octobot_trading.orders.order_factory import create_order_instance
from octobot_trading.orders.order_util import get_pre_order_data
from octobot_trading.trades.trade_factory import create_trade_from_order
from octobot_trading.util import is_trader_enabled, get_pairs, get_market_pair
from octobot_trading.util.initializable import Initializable


class Trader(Initializable):
    NO_HISTORY_MESSAGE = "Starting a fresh new trading session using the current portfolio as a profitability " \
                         "reference."

    def __init__(self, config, exchange_manager):
        super().__init__()
        self.exchange_manager = exchange_manager
        self.config = config

        self.risk = 0
        try:
            self.set_risk(self.config[CONFIG_TRADING][CONFIG_TRADER_RISK])
        except KeyError:
            self.set_risk(0)

        # logging
        self.trader_type_str = REAL_TRADER_STR
        self.logger = get_logger(f"{self.__class__.__name__}[{self.exchange_manager.exchange_name}]")

        if not hasattr(self, 'simulate'):
            self.simulate = False

        self.is_enabled = self.__class__.enabled(self.config)
        self.logger.debug(f"{'Enabled' if self.is_enabled else 'Disabled'} on {self.exchange_manager.exchange_name}")

    async def initialize_impl(self):
        if self.is_enabled:
            await self.exchange_manager.register_trader(self)

    @classmethod
    def enabled(cls, config):
        return is_trader_enabled(config)

    def set_risk(self, risk):
        if risk < CONFIG_TRADER_RISK_MIN:
            self.risk = CONFIG_TRADER_RISK_MIN
        elif risk > CONFIG_TRADER_RISK_MAX:
            self.risk = CONFIG_TRADER_RISK_MAX
        else:
            self.risk = risk
        return self.risk

    async def create_order(self, order, portfolio: Portfolio = None, loaded: bool = False):
        if portfolio is None:
            portfolio = self.exchange_manager.exchange_personal_data.portfolio_manager.portfolio

        linked_order: Order = None
        new_order: Order = order

        # if this order is linked to another (ex : a sell limit order with a stop loss order)
        if new_order.linked_to is not None:
            new_order.linked_to.add_linked_order(new_order)
            linked_order = new_order.linked_to

        if loaded:
            new_order.is_from_this_octobot = False
            self.logger.debug(f"Order loaded : {new_order.to_string()} ")
        else:
            try:
                new_order = await self._create_not_loaded_order(new_order, portfolio)
                self.logger.debug(f"Order creation : {new_order.to_string()} ")
            except TypeError as e:
                self.logger.error(f"Fail to create not loaded order : {e}")
                return None

        if new_order.status in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]:
            # notify order manager of a new open order
            await self.exchange_manager.exchange_personal_data.handle_order_instance_update(new_order)
        else:
            await self.exchange_manager.exchange_personal_data.handle_trade_instance_update(
                create_trade_from_order(new_order))

        # if this order is linked to another
        if linked_order is not None:
            new_order.linked_orders.append(linked_order)

        return new_order

    async def create_artificial_order(self, order_type, symbol, current_price, quantity, price, linked_portfolio):
        """
        Creates an OctoBot managed order
        """
        await self.create_order(create_order_instance(trader=self,
                                                      order_type=order_type,
                                                      symbol=symbol,
                                                      current_price=current_price,
                                                      quantity=quantity,
                                                      price=price,
                                                      linked_portfolio=linked_portfolio))

    async def _create_not_loaded_order(self, new_order: Order, portfolio) -> Order:
        """
        Creates an exchange managed order
        """
        if not self.simulate and not new_order.is_self_managed():
            created_order = await self.exchange_manager.exchange.create_order(new_order.order_type,
                                                                              new_order.symbol,
                                                                              new_order.origin_quantity,
                                                                              new_order.origin_price,
                                                                              new_order.origin_stop_price)

            self.logger.info(f"Created order on {self.exchange_manager.exchange_name}: {created_order}")

            # get real order from exchange
            new_order = Order(self)
            new_order.update_from_raw(created_order)

            # rebind linked portfolio to new order instance
            new_order.linked_portfolio = portfolio

        # update the availability of the currency in the portfolio
        portfolio.update_portfolio_available(new_order, is_new_order=True)

        return new_order

    async def cancel_order(self, order: Order):
        if order and not order.is_cancelled() and not order.is_filled():
            async with order.lock:
                odr = order
                cancelled_order = await odr.cancel_order()
                self.logger.info(f"{odr.symbol} {odr.get_name()} at {odr.origin_price}"
                                 f" (ID : {odr.order_id}) cancelled on {self.exchange_manager.exchange_name}")

                # skip_upsert when cancelled_order is None (nothing to update because simulated order)
                skip_upsert = cancelled_order is None
                cancelled_order = odr if skip_upsert else cancelled_order
                await self.exchange_manager.exchange_personal_data.handle_order_update(order.symbol,
                                                                                       order.order_id,
                                                                                       cancelled_order,
                                                                                       skip_upsert=skip_upsert)

    async def cancel_order_with_id(self, order_id):
        try:
            await self.cancel_order(self.exchange_manager.exchange_personal_data.orders_manager.get_order(order_id))
            return True
        except KeyError:
            return False

    # Should be called only if we want to cancel all symbol open orders (no filled)
    async def cancel_open_orders(self, symbol, cancel_loaded_orders=True):
        # use a copy of the list (not the reference)
        for order in copy.copy(self.exchange_manager.exchange_personal_data.orders_manager.get_open_orders()):
            if (order.symbol == symbol and order.status is not OrderStatus.CANCELED) and \
                    (cancel_loaded_orders or order.is_from_this_octobot):
                await self.notify_order_close(order, True)

    async def cancel_all_open_orders_with_currency(self, currency):
        symbols = get_pairs(self.config, currency)
        if symbols:
            for symbol in symbols:
                await self.cancel_open_orders(symbol)

    async def cancel_all_open_orders(self):
        # use a copy of the list (not the reference)
        for order in copy.copy(self.exchange_manager.exchange_personal_data.orders_manager.get_open_orders()):
            if order.status is not OrderStatus.CANCELED:
                await self.notify_order_close(order, True)

    async def _sell_everything(self, symbol, inverted, timeout=None):
        created_orders = []
        order_type = TraderOrderType.BUY_MARKET if inverted else TraderOrderType.SELL_MARKET
        async with self.exchange_manager.exchange_personal_data.portfolio_manager.portfolio.lock:
            current_symbol_holding, current_market_quantity, _, price, symbol_market = \
                await get_pre_order_data(self.exchange_manager, symbol, timeout=timeout)
            if inverted:
                if price > 0:
                    quantity = current_market_quantity / price
                else:
                    quantity = 0
            else:
                quantity = current_symbol_holding
            for order_quantity, order_price in check_and_adapt_order_details_if_necessary(quantity, price,
                                                                                          symbol_market):
                current_order = create_order_instance(trader=self,
                                                      order_type=order_type,
                                                      symbol=symbol,
                                                      current_price=order_price,
                                                      quantity=order_quantity,
                                                      price=order_price)
                created_orders.append(
                    await self.create_order(current_order,
                                            self.exchange_manager.exchange_personal_data.portfolio_manager.portfolio))
        return created_orders

    async def sell_all(self, currencies_to_sell=None, timeout=None):
        orders = []
        currency_list = self.exchange_manager.exchange_personal_data.portfolio_manager.portfolio.portfolio

        if not currencies_to_sell:
            currencies = currency_list
        else:
            currencies = [currency
                          for currency in currencies_to_sell
                          if currency in currency_list]

        for currency in currencies:
            symbol, inverted = get_market_pair(self.config, currency)
            if symbol:
                orders += await self._sell_everything(symbol, inverted, timeout=timeout)
        return orders

    async def notify_order_cancel(self, order, remove_from_manager=False):
        # update portfolio with ended order
        async with self.exchange_manager.exchange_personal_data.get_order_portfolio(order).lock:
            self.exchange_manager.exchange_personal_data.get_order_portfolio(order) \
                .update_portfolio_available(order, is_new_order=False)

        if remove_from_manager:
            # remove order from open_orders
            self.exchange_manager.exchange_personal_data.orders_manager.remove_order_instance(order)

    async def notify_order_close(self, order, cancel=False, cancel_linked_only=False):
        # Cancel linked orders
        for linked_order in order.linked_orders:
            await self.cancel_order(linked_order)

        # If need to cancel the order call the method and no need to update the portfolio (only availability)
        if cancel:
            await self.cancel_order(order)

            self.exchange_manager.exchange_personal_data.trades_manager.upsert_trade_instance(
                create_trade_from_order(order,
                                        close_status=OrderStatus.CANCELED,
                                        canceled_time=time.time()))

        elif cancel_linked_only:
            pass  # nothing to do

        else:
            # update portfolio with ended order
            async with self.exchange_manager.exchange_personal_data.get_order_portfolio(order).lock:
                await self.exchange_manager.exchange_personal_data.handle_portfolio_update_from_order(order)

            # add to trade history and notify
            await self.exchange_manager.exchange_personal_data.handle_trade_instance_update(
                create_trade_from_order(order))

            # remove order from open_orders
            self.exchange_manager.exchange_personal_data.orders_manager.remove_order_instance(order)

    """
    Positions
    """

    async def notify_position_cancel(self, position):
        # # update portfolio with ended order
        # async with self.exchange_manager.exchange_personal_data.get_order_portfolio(order).lock:
        #     self.exchange_manager.exchange_personal_data.get_order_portfolio(order) \
        #         .update_portfolio_available(order, is_new_order=False)
        pass  # TODO

    async def notify_position_close(self, position):
        pass  # TODO

    async def notify_position_liquidate(self, position):
        pass  # TODO

    # TODO : check if it's replaced by trade updater
    # def update_close_orders(self):
    #     for symbol in self.exchange_manager.exchange_config.get_traded_pairs():
    #         for close_order in self.exchange_manager.get_closed_orders(symbol):
    #             self.parse_exchange_order_to_trade_instance(close_order, Order(self))

    # TODO : should use updater methods
    async def force_refresh_orders_and_portfolio(self, portfolio=None, delete_desync_orders=True):
        # TODO: implement when available
        self.logger.error("force_refresh_orders_and_portfolio is not implemented yet in 0.4")
        # await self.exchange_manager.reset_web_sockets_if_any()    # Might now be useless (auto reconnect), to confirm
        # await self.force_refresh_orders(portfolio, delete_desync_orders=delete_desync_orders)
        # await self.force_refresh_portfolio(portfolio)

    #     await self.exchange_manager.reset_web_sockets_if_any()
    #     await self.force_refresh_orders(portfolio, delete_desync_orders=delete_desync_orders)
    #     await self.force_refresh_portfolio(portfolio)

    # TODO : Should be implemented in balance updater
    # async def force_refresh_portfolio(self, portfolio=None):
    #     if not self.simulate:
    #         self.logger.info(f"Triggered forced {self.exchange_manager.name} trader portfolio refresh")
    #         if portfolio:
    #             await portfolio.update_portfolio_balance()
    #         else:
    #             async with self.exchange_manager.exchange_personal_data.portfolio.lock:
    #                 await self.exchange_manager.exchange_personal_data.portfolio.update_portfolio_balance()

    # TODO : Should be implemented in order updater
    # async def force_refresh_orders(self, portfolio=None, delete_desync_orders=True):
    #     # useless in simulation mode
    #     if not self.simulate:
    #         self.logger.info(f"Triggered forced {self.exchange_manager.name} trader orders refresh")
    #         symbols = self.exchange_manager.exchange_config.get_traded_pairs()
    #         added_orders = 0
    #         removed_orders = 0
    #
    #         # get orders from exchange for the specified symbols
    #         for symbol_traded in symbols:
    #             orders = await self.exchange_manager.get_open_orders(symbol=symbol_traded, force_rest=True)
    #
    #             # create missing orders
    #             for open_order in orders:
    #                 # do something only if order not already in list
    #                 if not self.exchange_manager.exchange_personal_data.orders.has_order(open_order["id"]):
    #                     order = self.parse_exchange_order_to_order_instance(open_order)
    #                     if portfolio:
    #                         await self.create_order(order, portfolio, True)
    #                     else:
    #                         async with self.exchange_manager.exchange_personal_data.portfolio.lock:
    #                             await self.create_order(order, self.exchange_manager.exchange_personal_data.portfolio,
    #                                                     True)
    #                     added_orders += 1
    #
    #             if delete_desync_orders:
    #                 # remove orders that are not online anymore
    #                 order_ids = [o["id"] for o in orders]
    #                 for symbol_order in self.exchange_manager.exchange_personal_data.orders.get_orders_with_symbol(
    #                         symbol_traded):
    #                     if symbol_order.order_id not in order_ids:
    #                         # remove order from order manager
    #                         self.exchange_manager.exchange_personal_data.orders.remove_order_from_list(
    #                             symbol_order)
    #                         removed_orders += 1
    #         self.logger.info(f"Orders refreshed: added {added_orders} order(s) and removed {removed_orders} order(s)")

    def parse_order_id(self, order_id):
        return order_id
