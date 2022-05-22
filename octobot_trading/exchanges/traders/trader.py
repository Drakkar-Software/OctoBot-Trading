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
import octobot_trading.enums as enums
import octobot_trading.constants
import octobot_trading.errors as errors
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
        self.allow_artificial_orders = self.config.get(octobot_commons.constants.CONFIG_TRADER_ALLOW_ARTIFICIAL_ORDERS,
                                                       True)

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

    def clear(self):
        self.exchange_manager = None

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

    async def create_order(self, order, loaded: bool = False, params: dict = None, pre_init_callback=None):
        """
        Create a new order from an OrderFactory created order, update portfolio, registers order in order manager and
        notifies order channel.
        :param order: Order to create
        :param loaded: True if this order is fetched from an exchange only and therefore not created by this OctoBot
        :param params: Additional parameters to give to the order upon creation (used in real trading only)
        :param pre_init_callback: A callback function that will be called just before initializing the order
        :return: The crated order instance
        """
        new_order: object = order

        if loaded:
            new_order.is_from_this_octobot = False
            self.logger.debug(f"Order loaded : {new_order.to_string()} ")
        else:
            try:
                params = params or {}
                new_order = await self._create_new_order(new_order, params)
                self.logger.debug(f"Order creation : {new_order.to_string()} ")
            except TypeError as e:
                self.logger.error(f"Fail to create not loaded order : {e}")
                return None

        if pre_init_callback is not None:
            await pre_init_callback(new_order)

        # force initialize to always create open state
        await new_order.initialize()
        return new_order

    async def create_artificial_order(self, order_type, symbol, current_price, quantity, price):
        """
        Creates an OctoBot managed order (managed orders example: stop loss that is not published on the exchange and
        that is maintained internally).
        """
        await self.create_order(order_factory.create_order_instance(trader=self,
                                                                    order_type=order_type,
                                                                    symbol=symbol,
                                                                    current_price=current_price,
                                                                    quantity=quantity,
                                                                    price=price))

    async def edit_order(self, order: object,
                         edited_quantity: decimal.Decimal = None,
                         edited_price: decimal.Decimal = None,
                         edited_stop_price: decimal.Decimal = None,
                         edited_current_price: decimal.Decimal = None,
                         params: dict = None) -> bool:
        """
        Edits an order, might be a simulated or a real order.
        Fields that can be edited are:
            quantity, price, stop_price and current_price
        Portfolio is updated within this call
        :return: True when an order field got updated
        """
        if not order.can_be_edited():
            raise errors.OrderEditError(f"Order can't be edited, order: {order}")
        changed = False
        previous_order_id = order.order_id
        try:
            async with order.lock:
                # now that we got the lock, ensure we can edit the order
                if not self.simulate and not order.is_self_managed() and order.state is not None:
                    # careful here: make sure we are not editing an order on exchange that is being updated
                    # somewhere else
                    async with order.state.refresh_operation():
                        order_params = self.exchange_manager.exchange.get_order_additional_params(order)
                        order_params.update(params or {})
                        # fill in every param as some exchange rely on re-creating the order altogether
                        edited_order = await self.exchange_manager.exchange.edit_order(
                            order.order_id,
                            order.order_type,
                            order.symbol,
                            quantity=order.origin_quantity if edited_quantity is None else edited_quantity,
                            price=order.origin_price if edited_price is None else edited_price,
                            stop_price=edited_stop_price,
                            side=order.side,
                            current_price=edited_current_price,
                            params=order_params
                        )
                        # apply new values from returned order (even order id might have changed)
                        self.logger.debug(f"Successful order edit on {self.exchange_manager.exchange_name}: "
                                          f"{edited_order}")
                        changed = order.update_from_raw(edited_order)
                        # update portfolio from exchange
                        await self.exchange_manager.exchange_personal_data.handle_portfolio_update_from_order(order)
                else:
                    # consider order as cancelled to release portfolio amounts
                    self.exchange_manager.exchange_personal_data.portfolio_manager.portfolio.update_portfolio_available(
                        order, is_new_order=False
                    )
                    changed = order.update(
                        order.symbol,
                        quantity=edited_quantity,
                        price=edited_stop_price if edited_price is None else edited_price,
                        stop_price=edited_stop_price,
                        current_price=edited_current_price,
                    )
                    # consider order as new order to lock portfolio amounts
                    self.exchange_manager.exchange_personal_data.portfolio_manager.portfolio.update_portfolio_available(
                        order, is_new_order=True
                    )
                self.logger.info(f"Edited order: {order}")
            return changed
        finally:
            if previous_order_id != order.order_id:
                # order id changed: update orders_manager to keep consistency
                self.exchange_manager.exchange_personal_data.orders_manager.replace_order(previous_order_id, order)

    async def _create_new_order(self, new_order: object, params: dict) -> object:
        """
        Creates an exchange managed order, it might be a simulated or a real order.
        Portfolio will be updated by the create order state after order will be initialized
        """
        updated_order = new_order
        if not self.simulate and not new_order.is_self_managed():
            order_params = self.exchange_manager.exchange.get_order_additional_params(new_order)
            order_params.update(params)
            created_order = await self.exchange_manager.exchange.create_order(new_order.order_type,
                                                                              new_order.symbol,
                                                                              new_order.origin_quantity,
                                                                              new_order.origin_price,
                                                                              new_order.origin_stop_price,
                                                                              new_order.side,
                                                                              new_order.created_last_price,
                                                                              params=order_params)

            self.logger.info(f"Created order on {self.exchange_manager.exchange_name}: {created_order}")

            # get real order from exchange
            updated_order = order_factory.create_order_instance_from_raw(self, created_order, force_open=True)

            # rebind local elements to new order instance
            if new_order.order_group:
                updated_order.add_to_order_group(new_order.order_group)
            updated_order.tag = new_order.tag
            updated_order.chained_orders = new_order.chained_orders
            for chained_order in new_order.chained_orders:
                chained_order.triggered_by = updated_order
            updated_order.triggered_by = new_order.triggered_by
            updated_order.has_been_bundled = new_order.has_been_bundled
            updated_order.exchange_creation_params = new_order.exchange_creation_params
            updated_order.is_waiting_for_chained_trigger = new_order.is_waiting_for_chained_trigger
            updated_order.set_shared_signal_order_id(new_order.shared_signal_order_id)
        return updated_order

    async def bundle_chained_order_with_uncreated_order(self, order, chained_order, **kwargs):
        """
        Creates and bundles an order as a chained order to the given order.
        When supported and in real trading, return the stop loss parameters to be given when
        pushing the initial order on exchange
        :param order: the order to create a chained order from after fill
        :param chained_order: the chained order to create when the 1st order is filled
        :return: parameters with chained order details if supported
        """
        params = {}
        is_bundled = self.exchange_manager.exchange.supports_bundled_order_on_order_creation(
            order, chained_order.order_type
        )
        if is_bundled:
            if chained_order.order_type is enums.TraderOrderType.STOP_LOSS:
                params.update(self.exchange_manager.exchange.get_bundled_order_parameters(
                    stop_loss_price=chained_order.origin_price
                ))
            if chained_order.order_type in (enums.TraderOrderType.BUY_MARKET, enums.TraderOrderType.SELL_MARKET,
                                            enums.TraderOrderType.BUY_LIMIT, enums.TraderOrderType.SELL_LIMIT):
                params.update(self.exchange_manager.exchange.get_bundled_order_parameters(
                    take_profit_price=chained_order.origin_price
                ))
        await chained_order.set_as_chained_order(order, is_bundled, {}, **kwargs)
        order.add_chained_order(chained_order)
        return params

    async def cancel_order(self, order: object, ignored_order: object = None) -> bool:
        """
        Cancels the given order and updates the portfolio, publish in order channel
        if order is from a real exchange.
        :param order: Order to cancel
        :param ignored_order: Order not to cancel if found in groupped orders recursive cancels (ex: avoid cancelling
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
            if order.is_waiting_for_chained_trigger:
                # order will just never get created
                order.is_waiting_for_chained_trigger = False
                return success
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

    async def cancel_open_orders(self, symbol, cancel_loaded_orders=True, side=None) -> (bool, list):
        """
        Should be called only if the goal is to cancel all open orders for a given symbol
        :param symbol: The symbol to cancel all orders on
        :param cancel_loaded_orders: When True, also cancels loaded orders (order that are not from this bot instance)
        :param side: When set, only cancels orders from this side
        :return: (True, orders): True if all orders got cancelled, False if an error occurred and the list of
        cancelled orders
        """
        all_cancelled = True
        cancelled_orders = []
        for order in self.exchange_manager.exchange_personal_data.orders_manager.get_open_orders():
            if order.symbol == symbol and \
                    (side is None or order.side is side) and \
                    not order.is_cancelled() and \
                    (cancel_loaded_orders or order.is_from_this_octobot):
                cancelled = await self.cancel_order(order)
                if cancelled:
                    cancelled_orders.append(order)
                all_cancelled = cancelled and all_cancelled
        return all_cancelled, cancelled_orders

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
                all_cancelled = (await self.cancel_open_orders(symbol))[0] and all_cancelled
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
                    await self.create_order(current_order))
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

    async def close_position(self, position, limit_price=None, timeout=1):
        """
        Creates a close position order
        :param position: the position to close
        :param limit_price: the close order limit price if None uses a market order
        :param timeout: the mark price timeout
        :return: the list of created orders
        """
        created_orders = []
        async with self.exchange_manager.exchange_personal_data.portfolio_manager.portfolio.lock:
            _, _, _, price, symbol_market = await order_util.get_pre_order_data(self.exchange_manager,
                                                                                position.symbol,
                                                                                timeout=timeout)
            for order_quantity, order_price in decimal_order_adapter.decimal_check_and_adapt_order_details_if_necessary(
                    position.get_quantity_to_close().copy_abs(), price, symbol_market):

                if limit_price is not None:
                    order_type = enums.TraderOrderType.SELL_LIMIT \
                        if position.is_long() else enums.TraderOrderType.BUY_LIMIT
                else:
                    order_type = enums.TraderOrderType.SELL_MARKET \
                        if position.is_long() else enums.TraderOrderType.BUY_MARKET

                # TODO add reduce_only or close_position attribute
                current_order = order_factory.create_order_instance(trader=self,
                                                                    order_type=order_type,
                                                                    symbol=position.symbol,
                                                                    current_price=order_price,
                                                                    quantity=order_quantity,
                                                                    price=limit_price
                                                                    if limit_price is not None else order_price)
                created_orders.append(
                    await self.create_order(current_order))
        return created_orders

    async def withdraw(self, amount, currency):
        """
        Removes the given amount from the portfolio. Only works in simulated portfolios
        :param amount: the amount to withdraw
        :param currency: the currency to withdraw
        """
        async with self.exchange_manager.exchange_personal_data.portfolio_manager.portfolio.lock:
            await self.exchange_manager.exchange_personal_data.handle_portfolio_update_from_withdrawal(amount, currency)

    async def set_leverage(self, symbol, side, leverage):
        """
        Updates the symbol contract leverage
        Can raise InvalidLeverageValue if leverage value is not matching requirements
        :param symbol: the symbol to update
        :param side: the side to update (TODO)
        :param leverage: the new leverage value
        """
        contract = self.exchange_manager.exchange.get_pair_future_contract(symbol)
        if not contract.check_leverage_update(leverage):
            raise errors.InvalidLeverageValue(f"Trying to update leverage with {leverage} "
                                              f"but maximal value is {contract.maximum_leverage}")
        if contract.current_leverage != leverage:
            if not self.simulate:
                await self.exchange_manager.exchange.set_symbol_leverage(
                    symbol=symbol,
                    leverage=leverage
                )
            contract.set_current_leverage(leverage)

    async def set_symbol_take_profit_stop_loss_mode(self, symbol, new_mode: enums.TakeProfitStopLossMode):
        """
        Updates the take profit and stop loss mode for the given symbol
        Raises NotImplementedError if the endpoint is not implemented on exchange
        :param symbol: the symbol to update
        :param new_mode: the take_profit_stop_loss_mode value
        """
        contract = self.exchange_manager.exchange.get_pair_future_contract(symbol)
        if contract.take_profit_stop_loss_mode != new_mode:
            if not self.simulate:
                await self.exchange_manager.exchange.set_symbol_partial_take_profit_stop_loss(
                    symbol, contract.is_inverse_contract(), new_mode)
            contract.set_take_profit_stop_loss_mode(new_mode)

    async def set_margin_type(self, symbol, side, margin_type):
        """
        Updates the symbol contract margin type
        TODO: recreate position instances if any
        :param symbol: the symbol to update
        :param side: the side to update (TODO)
        :param margin_type: the new margin type (enums.MarginType)
        """
        contract = self.exchange_manager.exchange.get_pair_future_contract(symbol)
        if not self.simulate:
            await self.exchange_manager.exchange.set_symbol_margin_type(
                symbol=symbol,
                isolated=margin_type is enums.MarginType.ISOLATED
            )
        contract.set_margin_type(
            is_isolated=margin_type is enums.MarginType.ISOLATED,
            is_cross=margin_type is enums.MarginType.CROSS
        )

    async def set_position_mode(self, symbol, position_mode):
        """
        Updates the symbol contract position mode
        :param symbol: the symbol to update
        :param position_mode: the new position mode (enums.PositionMode)
        """
        if self._has_open_position(symbol):
            raise errors.TooManyOpenPositionError("Can't update position mode when having open position.")
        contract = self.exchange_manager.exchange.get_pair_future_contract(symbol)
        if not self.simulate:
            await self.exchange_manager.exchange.set_symbol_position_mode(
                symbol=symbol,
                one_way=position_mode is enums.PositionMode.ONE_WAY
            )
        contract.set_position_mode(
            is_one_way=position_mode is enums.PositionMode.ONE_WAY,
            is_hedge=position_mode is enums.PositionMode.HEDGE
        )

    def _has_open_position(self, symbol):
        """
        Checks if open position exists for :symbol:
        :param symbol: the position symbol
        :return: True if open position for :symbol: exists
        """
        return len(self.exchange_manager.exchange_personal_data.positions_manager.get_symbol_positions(
            symbol=symbol)) != 0
