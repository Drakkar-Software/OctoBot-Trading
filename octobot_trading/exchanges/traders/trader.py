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

import octobot_commons.logging as logging

import octobot_commons.constants
import octobot_trading.personal_data.orders.order_factory as order_factory
import octobot_trading.personal_data.orders.order_util as order_util
import octobot_trading.personal_data.orders.decimal_order_adapter as decimal_order_adapter
import octobot_trading.personal_data.trades.trade_factory as trade_factory
import octobot_trading.enums
import octobot_trading.constants
import octobot_trading.util as util


class Trader(util.Initializable):
    NO_HISTORY_MESSAGE = "Starting a fresh new trading session using the current portfolio as a profitability " \
                         "reference."

    def __init__(self, config, exchange_manager):
        super().__init__()
        self.exchange_manager = exchange_manager
        self.config = config

        self.risk = octobot_trading.constants.ZERO
        try:
            self.set_risk(decimal.Decimal(str(self.config[octobot_commons.constants.CONFIG_TRADING]
                          [octobot_commons.constants.CONFIG_TRADER_RISK])))
        except KeyError:
            self.set_risk(octobot_trading.constants.ZERO)

        # logging
        self.trader_type_str = octobot_trading.constants.REAL_TRADER_STR
        self.logger = logging.get_logger(f"{self.__class__.__name__}[{self.exchange_manager.exchange_name}]")

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
        return util.is_trader_enabled(config)

    def set_risk(self, risk):
        min_risk = decimal.Decimal(str(octobot_commons.constants.CONFIG_TRADER_RISK_MIN))
        max_risk = decimal.Decimal(str(octobot_commons.constants.CONFIG_TRADER_RISK_MAX))
        if risk < min_risk:
            self.risk = min_risk
        elif risk > max_risk:
            self.risk = max_risk
        else:
            self.risk = risk
        return self.risk

    """
    Orders
    """

    async def create_order(self, order, portfolio: object = None, loaded: bool = False):
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

        linked_order: object = None
        new_order: object = order

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
        await self.create_order(order_factory.create_order_instance(trader=self,
                                                                    order_type=order_type,
                                                                    symbol=symbol,
                                                                    current_price=current_price,
                                                                    quantity=quantity,
                                                                    price=price,
                                                                    linked_portfolio=linked_portfolio))

    async def _create_new_order(self, new_order: object, portfolio) -> object:
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
            new_order = order_factory.create_order_instance_from_raw(self, created_order, force_open=True)

            # rebind linked portfolio to new order instance
            new_order.linked_portfolio = portfolio
        return new_order

    async def cancel_order(self, order: object, ignored_order: object = None) -> bool:
        """
        Cancels the given order and its linked orders, and updates the portfolio, publish in order channel
        if order is from a real exchange.
        :param order: Order to cancel
        :param ignored_order: Order not to cancel if found in linked orders recursive cancels (ex: avoid cancelling
        a filled order)
        :return: None
        """
        if order and order.is_open():
            # always cancel this order first to avoid infinite loop followed by deadlock
            return await self._handle_order_cancellation(order, ignored_order)
        return False

    async def _handle_order_cancellation(self, order: object, ignored_order: object) -> bool:
        success = True
        async with order.lock:
            # if real order: cancel on exchange
            if not self.simulate and not order.is_self_managed():
                success = await self.exchange_manager.exchange.cancel_order(order.order_id, order.symbol)
                if not success:
                    # retry to cancel order
                    success = await self.exchange_manager.exchange.cancel_order(order.order_id, order.symbol)
                if not success:
                    self.logger.warning(f"Failed to cancel order {order}")
                    return False
                else:
                    order.status = octobot_trading.enums.OrderStatus.CLOSED
                    self.logger.debug(f"Successfully cancelled order {order}")
            else:
                order.status = octobot_trading.enums.OrderStatus.CANCELED

        # call CancelState termination
        await order.on_cancel(force_cancel=success,
                              is_from_exchange_data=False,
                              ignored_order=ignored_order)
        return True

    async def cancel_order_with_id(self, order_id):
        """
        Gets order matching order_id from the OrderManager and calls self.cancel_order() on it
        :param order_id: Id of the order to cancel
        :return: True if cancel is successful, False if order is not found or cancellation failed
        """
        try:
            return await self.cancel_order(
                self.exchange_manager.exchange_personal_data.orders_manager.get_order(order_id)
            )
        except KeyError:
            return False

    async def cancel_open_orders(self, symbol, cancel_loaded_orders=True) -> bool:
        """
        Should be called only if the goal is to cancel all open orders for a given symbol
        :param symbol: The symbol to cancel all orders on
        :param cancel_loaded_orders: When True, also cancels loaded orders (order that are not from this bot instance)
        :return: True if all orders got cancelled, False if an error occurred
        """
        all_cancelled = True
        for order in self.exchange_manager.exchange_personal_data.orders_manager.get_open_orders():
            if (order.symbol == symbol and not order.is_cancelled()) and \
                    (cancel_loaded_orders or order.is_from_this_octobot):
                all_cancelled = await self.cancel_order(order) and all_cancelled
        return all_cancelled

    async def cancel_all_open_orders_with_currency(self, currency) -> bool:
        """
        Should be called only if the goal is to cancel all open orders for each traded symbol containing the
        given currency.
        :param currency: Currency to find trading pairs to cancel orders on.
        :return: True if all orders got cancelled, False if an error occurred
        """
        all_cancelled = True
        symbols = util.get_pairs(self.config, currency, enabled_only=True)
        if symbols:
            for symbol in symbols:
                all_cancelled = await self.cancel_open_orders(symbol) and all_cancelled
        return all_cancelled

    async def cancel_all_open_orders(self) -> bool:
        """
        Cancel all open orders registered on this bot.
        :return: True if all orders got cancelled, False if an error occurred
        """
        all_cancelled = True
        for order in self.exchange_manager.exchange_personal_data.orders_manager.get_open_orders():
            if not order.is_cancelled():
                all_cancelled = await self.cancel_order(order) and all_cancelled
        return all_cancelled

    async def _sell_everything(self, symbol, inverted, timeout=None):
        created_orders = []
        order_type = octobot_trading.enums.TraderOrderType.BUY_MARKET \
            if inverted else octobot_trading.enums.TraderOrderType.SELL_MARKET
        async with self.exchange_manager.exchange_personal_data.portfolio_manager.portfolio.lock:
            current_symbol_holding, current_market_quantity, _, price, symbol_market = \
                await order_util.get_pre_order_data(self.exchange_manager, symbol, timeout=timeout)
            if inverted:
                if price > 0:
                    quantity = current_market_quantity / price
                else:
                    quantity = 0
            else:
                quantity = current_symbol_holding
            for order_quantity, order_price in decimal_order_adapter.decimal_check_and_adapt_order_details_if_necessary(quantity, price,
                                                                                                        symbol_market):
                current_order = order_factory.create_order_instance(trader=self,
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
            symbol, inverted = util.get_market_pair(self.config, currency, enabled_only=True)
            if symbol:
                orders += await self._sell_everything(symbol, inverted, timeout=timeout)
        return orders

    def parse_order_id(self, order_id):
        return order_id

    def convert_order_to_trade(self, order):
        """
        Convert an order instance to Trade
        :return: the new Trade instance from order
        """
        return trade_factory.create_trade_from_order(order)

    """
    Positions
    """

    async def close_position(self, position, limit_price=None) -> None:
        """
        Creates a close position order
        :param position: the position to close
        :param limit_price: the close order limit price if None uses a market order
        """
        # TODO use reduce only param
        if limit_price is None:
            # TODO market order
            pass
        else:
            pass

    async def set_leverage(self, position):
        pass  # TODO

    async def set_margin_type(self, new_margin_type):
        pass  # TODO
