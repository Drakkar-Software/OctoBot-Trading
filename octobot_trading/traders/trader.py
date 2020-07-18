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

    async def initialize_impl(self):
        self.is_enabled = self.is_enabled and self.exchange_manager.is_trading
        if self.is_enabled:
            await self.exchange_manager.register_trader(self)
        self.logger.debug(f"{'Enabled' if self.is_enabled else 'Disabled'} on {self.exchange_manager.exchange_name}")

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
        """
        Create a new order from an OrderFactory created order, update portfolio, registers order in order manager and
        notifies order channel. Handles linked orders.
        :param order: Order to create
        :param portfolio: Portfolio to update (default is this exchange's portfolio)
        :param loaded: True if this order is fetched from an exchange only and therefore not created by this OctoBot
        :return: The crated order instance
        """
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
                new_order = await self._create_new_order(new_order, portfolio)
                self.logger.debug(f"Order creation : {new_order.to_string()} ")
            except TypeError as e:
                self.logger.error(f"Fail to create not loaded order : {e}")
                return None

        if new_order.is_open():
            # notify order manager of a new open order
            await self.exchange_manager.exchange_personal_data.handle_order_instance_update(new_order)
        else:
            # notify order channel than an order has been created even though it's already closed
            await self.exchange_manager.exchange_personal_data.handle_order_update_notification(new_order, True)
            await self.exchange_manager.exchange_personal_data.handle_trade_instance_update(
                create_trade_from_order(new_order))

        # if this order is linked to another
        if linked_order is not None:
            new_order.linked_orders.append(linked_order)

        await new_order.initialize()
        return new_order

    async def create_artificial_order(self, order_type, symbol, current_price, quantity, price, linked_portfolio):
        """
        Creates an OctoBot managed order (managed orders example: stop loss that is not published on the exchange and
        that is maintained internally).
        """
        await self.create_order(create_order_instance(trader=self,
                                                      order_type=order_type,
                                                      symbol=symbol,
                                                      current_price=current_price,
                                                      quantity=quantity,
                                                      price=price,
                                                      linked_portfolio=linked_portfolio))

    async def _create_new_order(self, new_order: Order, portfolio) -> Order:
        """
        Creates an exchange managed order, it might be a simulated or a real order. Then updates the portfolio.
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

    async def close_filled_order(self, order):
        """
        Closes the given filled order starting buy cancelling its linked orders, updating the portfolio, creating
        the new trade and finally removing the order from order manager. Does not update the order attributes.
        :param order: Already filled order
        :return: None
        """
        self.logger.info(f"Filled order: {order}")
        # Cancel linked orders
        for linked_order in order.linked_orders:
            await self.cancel_order(linked_order, ignored_order=order)

        # update portfolio with filled order
        async with self.exchange_manager.exchange_personal_data.get_order_portfolio(order).lock:
            await self.exchange_manager.exchange_personal_data.handle_portfolio_update_from_order(order)

        # add to trade history and notify
        await self.exchange_manager.exchange_personal_data.handle_trade_instance_update(
            create_trade_from_order(order))

        # notify order trade created
        await order.on_trade_creation()

        # remove order from open_orders
        self.exchange_manager.exchange_personal_data.orders_manager.remove_order_instance(order)

    async def cancel_order(self, order: Order, is_cancelled_from_exchange: bool = False, ignored_order: Order = None,
                           should_notify: bool = True):
        """
        Cancels the given order and its linked orders, and updates the portfolio, publish in order channel
        if order is from a real exchange.
        :param order: Order to cancel
        :param is_cancelled_from_exchange: When True, will not try to cancel this order on real exchange
        :param ignored_order: Order not to cancel if found in linked orders recursive cancels (ex: avoid cancelling
        a filled order)
        :return: None
        """
        if order and ((not order.is_cancelled() and not order.is_filled()) or is_cancelled_from_exchange):
            async with order.lock:
                # always cancel this order first to avoid infinite loop followed by deadlock
                order.cancel_order()
                for linked_order in order.linked_orders:
                    if linked_order is not ignored_order:
                        await self.cancel_order(linked_order, ignored_order=ignored_order)
                if await self._handle_order_cancellation(order, is_cancelled_from_exchange):
                    self.logger.info(f"Cancelled order: {order} on {self.exchange_manager.exchange_name}")
                    if should_notify:
                        await self.exchange_manager.exchange_personal_data.handle_order_update_notification(order,
                                                                                                            True)

    async def _handle_order_cancellation(self, order: Order, is_cancelled_from_exchange: bool) -> bool:
        success = True
        # if real order: cancel on exchange
        if not self.simulate and not order.is_self_managed() and not is_cancelled_from_exchange:
            success = await self.exchange_manager.exchange.cancel_order(order.order_id, order.symbol)
            if not success:
                # retry to cancel order
                success = await self.exchange_manager.exchange.cancel_order(order.order_id, order.symbol)
            if not success:
                raise RuntimeError(f"Failed to cancel order {order}")
            else:
                self.logger.debug(f"Successfully cancelled order {order}")

        # add to trade history and notify
        await self.exchange_manager.exchange_personal_data.handle_trade_instance_update(
            create_trade_from_order(order,
                                    close_status=OrderStatus.CANCELED,
                                    canceled_time=self.exchange_manager.exchange.get_exchange_current_time()))

        # update portfolio with cancelled funds order
        async with self.exchange_manager.exchange_personal_data.get_order_portfolio(order).lock:
            self.exchange_manager.exchange_personal_data.get_order_portfolio(order) \
                .update_portfolio_available(order, is_new_order=False)

        # remove order from open_orders
        self.exchange_manager.exchange_personal_data.orders_manager.remove_order_instance(order)

        return success

    async def cancel_order_with_id(self, order_id):
        """
        Gets order matching order_id from the OrderManager and calls self.cancel_order() on it
        :param order_id: Id of the order to cancel
        :return: True if cancel is successful, False if order is not found
        """
        try:
            await self.cancel_order(self.exchange_manager.exchange_personal_data.orders_manager.get_order(order_id))
            return True
        except KeyError:
            return False

    async def cancel_open_orders(self, symbol, cancel_loaded_orders=True):
        """
        Should be called only if the goal is to cancel all open orders for a given symbol
        :param symbol: The symbol to cancel all orders on
        :param cancel_loaded_orders: When True, also cancels loaded orders (order that are not from this bot instance)
        :return: None
        """
        for order in self.exchange_manager.exchange_personal_data.orders_manager.get_open_orders():
            if (order.symbol == symbol and order.status is not OrderStatus.CANCELED) and \
                    (cancel_loaded_orders or order.is_from_this_octobot):
                await self.cancel_order(order)

    async def cancel_all_open_orders_with_currency(self, currency):
        """
        Should be called only if the goal is to cancel all open orders for each traded symbol containing the
        given currency.
        :param currency: Currency to find trading pairs to cancel orders on.
        :return: None
        """
        symbols = get_pairs(self.config, currency)
        if symbols:
            for symbol in symbols:
                await self.cancel_open_orders(symbol)

    async def cancel_all_open_orders(self):
        """
        Cancel all open orders registered on this bot.
        :return: None
        """
        for order in self.exchange_manager.exchange_personal_data.orders_manager.get_open_orders():
            if order.status is not OrderStatus.CANCELED:
                await self.cancel_order(order)

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
        """
        Sell every currency in portfolio for reference market using market orders.
        :param currencies_to_sell: List of currencies to sell, default values consider every currency in portfolio
        :param timeout: Timeout to get market price
        :return: The created orders
        """
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
