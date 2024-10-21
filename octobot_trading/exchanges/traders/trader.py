# pylint: disable=W0706
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
import typing

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
import octobot_trading.signals as signals


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

    async def create_order(self, order, loaded: bool = False, params: dict = None,
                           wait_for_creation=True,
                           creation_timeout=octobot_trading.constants.INDIVIDUAL_ORDER_SYNC_TIMEOUT):
        """
        Create a new order from an OrderFactory created order, update portfolio, registers order in order manager and
        notifies order channel.
        :param order: Order to create
        :param loaded: True if this order is fetched from an exchange only and therefore not created by this OctoBot
        :param params: Additional parameters to give to the order upon creation (used in real trading only)
        :param wait_for_creation: when True, always make sure the order is completely created before returning.
        On exchanges async api, a create request will return before the order is actually live on exchange, in this case
        the associated order state will make sure that the order is creating by polling the order from the exchange.
        :param creation_timeout: time before raising a timeout error when waiting for an order creation
        :return: The crated order instance
        """
        if loaded:
            order.is_from_this_octobot = False
            self.logger.debug(f"Order loaded : {order.to_string()} ")
            # force initialize to always create open state
            await order.initialize()
            return order
        # octobot order
        created_order = order
        try:
            params = params or {}
            self.logger.info(f"Creating order: {created_order}")
            created_order = await self._create_new_order(order, params, wait_for_creation=wait_for_creation,
                                                         creation_timeout=creation_timeout)
            if created_order is None:
                self.logger.warning(f"Order not created on {self.exchange_manager.exchange_name} "
                                    f"(failed attempt to create: {order}). This is likely due to "
                                    f"the order being refused by the exchange.")
        except (errors.MissingFunds, errors.AuthenticationError, errors.ExchangeCompliancyError):
            # forward errors that require actions to fix the situation
            raise
        except Exception as e:
            self.logger.exception(e, True, f"Unexpected error when creating order: {e}. Order: {order}")
            return None

        return created_order

    async def create_artificial_order(self, order_type, symbol, current_price, quantity, price,
                                      emit_trading_signals=False,
                                      wait_for_creation=True,
                                      creation_timeout=octobot_trading.constants.INDIVIDUAL_ORDER_SYNC_TIMEOUT):
        """
        Creates an OctoBot managed order (managed orders example: stop loss that is not published on the exchange and
        that is maintained internally).
        """
        order = order_factory.create_order_instance(trader=self,
                                                    order_type=order_type,
                                                    symbol=symbol,
                                                    current_price=current_price,
                                                    quantity=quantity,
                                                    price=price)
        async with signals.remote_signal_publisher(self.exchange_manager, order.symbol, emit_trading_signals):
            await signals.create_order(
                self.exchange_manager,
                emit_trading_signals and signals.should_emit_trading_signal(self.exchange_manager),
                order,
                wait_for_creation=wait_for_creation,
                creation_timeout=creation_timeout
            )

    async def edit_order(self, order,
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
        previous_exchange_order_id = order.exchange_order_id
        try:
            async with order.lock:
                # now that we got the lock, ensure we can edit the order
                if not self.simulate and not order.is_self_managed() and order.state is not None:
                    # careful here: make sure we are not editing an order on exchange that is being updated
                    # somewhere else
                    async with order.state.refresh_operation():
                        self.logger.info(f"Editing order: {order} ["
                                         f"edited_quantity: {str(edited_quantity)} "
                                         f"edited_price: {str(edited_price)} "
                                         f"edited_stop_price: {str(edited_stop_price)} "
                                         f"edited_current_price: {str(edited_current_price)}"
                                         f"]")
                        order_params = self.exchange_manager.exchange.get_order_additional_params(order)
                        order_params.update(params or {})
                        # fill in every param as some exchange rely on re-creating the order altogether
                        edited_order = await self.exchange_manager.exchange.edit_order(
                            order.exchange_order_id,
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
                        self.logger.debug(f"Successfully edited order on {self.exchange_manager.exchange_name}, "
                                          f"new order values: {edited_order}")
                        changed = order.update_from_raw(edited_order)
                        # update portfolio from exchange
                        await self.exchange_manager.exchange_personal_data.\
                            handle_portfolio_and_position_update_from_order(order)
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
                # push order edit into orders channel as edit update
                await self.exchange_manager.exchange_personal_data.handle_order_update_notification(
                    order, enums.OrderUpdateType.EDIT
                )
                self.logger.info(f"Edited order: {order}")
            return changed
        finally:
            if previous_exchange_order_id != order.exchange_order_id:
                # order id changed: update orders_manager to keep consistency
                self.exchange_manager.exchange_personal_data.orders_manager.replace_order(order.order_id, order)

    async def _create_new_order(self, new_order, params: dict,
                                wait_for_creation=True,
                                creation_timeout=octobot_trading.constants.INDIVIDUAL_ORDER_SYNC_TIMEOUT) -> object:
        """
        Creates an exchange managed order, it might be a simulated or a real order.
        Portfolio will be updated by the created order state after order will be initialized
        """
        updated_order = new_order
        is_pending_creation = False
        if not self.simulate and not new_order.is_self_managed():
            order_params = self.exchange_manager.exchange.get_order_additional_params(new_order)
            order_params.update(new_order.exchange_creation_params)
            order_params.update(params)
            created_order = await self.exchange_manager.exchange.create_order(
                order_type=new_order.order_type,
                symbol=new_order.symbol,
                quantity=new_order.origin_quantity,
                price=new_order.origin_price,
                stop_price=new_order.origin_stop_price,
                side=new_order.side,
                current_price=new_order.created_last_price,
                reduce_only=new_order.reduce_only,
                params=order_params
            )
            if created_order is None:
                return None
            self.logger.debug(f"Successfully created order on {self.exchange_manager.exchange_name}: {created_order}")

            # get real order from exchange
            updated_order = order_factory.create_order_instance_from_raw(
                self, created_order, force_open_or_pending_creation=True, has_just_been_created=True
            )
            is_pending_creation = updated_order.status == enums.OrderStatus.PENDING_CREATION

            # rebind local elements to new order instance
            if new_order.order_group:
                updated_order.add_to_order_group(new_order.order_group)
            updated_order.order_id = new_order.order_id
            updated_order.tag = new_order.tag
            updated_order.chained_orders = new_order.chained_orders
            for chained_order in new_order.chained_orders:
                chained_order.triggered_by = updated_order
            updated_order.triggered_by = new_order.triggered_by
            updated_order.has_been_bundled = new_order.has_been_bundled
            updated_order.exchange_creation_params = new_order.exchange_creation_params
            updated_order.is_waiting_for_chained_trigger = new_order.is_waiting_for_chained_trigger
            updated_order.associated_entry_ids = new_order.associated_entry_ids
            updated_order.update_with_triggering_order_fees = new_order.update_with_triggering_order_fees

            if is_pending_creation:
                # register order as pending order, it will then be added to live orders in order manager once open
                self.exchange_manager.exchange_personal_data.orders_manager.register_pending_creation_order(
                    updated_order
                )

        await updated_order.initialize()
        if is_pending_creation and wait_for_creation \
                and updated_order.state is not None and updated_order.state.is_pending()\
                and self.exchange_manager.exchange_personal_data.orders_manager.enable_order_auto_synchronization:
            await updated_order.state.wait_for_terminate(creation_timeout)
        return updated_order

    def get_take_profit_order_type(self, base_order, order_type: enums.TraderOrderType) -> enums.TraderOrderType:
        """
        Returns the adapted take profit order enums.TraderOrderType.
        :return: enums.TraderOrderType.TAKE_PROFIT when order can be bundled and considered as a real take profit
        from exchange and the given order_type otherwise
        """
        if not self.simulate and self.exchange_manager.exchange.supports_bundled_order_on_order_creation(
            base_order, enums.TraderOrderType.TAKE_PROFIT
        ):
            # use take profit order type for bundled orders, use default order type otherwise
            return enums.TraderOrderType.TAKE_PROFIT
        return order_type

    async def bundle_chained_order_with_uncreated_order(
        self, order, chained_order, update_with_triggering_order_fees, **kwargs
    ) -> dict:
        """
        Creates and bundles an order as a chained order to the given order.
        When supported and in real trading, return the stop loss parameters to be given when
        pushing the initial order on exchange
        :param order: the order to create a chained order from after fill
        :param chained_order: the chained order to create when the 1st order is filled
        :param update_with_triggering_order_fees: if the chained order quantity should
        be updated with triggering order fees
        :return: parameters with chained order details if supported
        """
        params = {}
        is_bundled = self.exchange_manager.exchange.supports_bundled_order_on_order_creation(
            order, chained_order.order_type
        )
        if is_bundled:
            # warning: doesn't work for multiple stop loss / take profits
            if chained_order.order_type is enums.TraderOrderType.STOP_LOSS:
                params.update(self.exchange_manager.exchange.get_bundled_order_parameters(
                    order,
                    stop_loss_price=chained_order.origin_price
                ))
            elif chained_order.order_type in (enums.TraderOrderType.TAKE_PROFIT,
                                              enums.TraderOrderType.BUY_MARKET, enums.TraderOrderType.SELL_MARKET,
                                              enums.TraderOrderType.BUY_LIMIT, enums.TraderOrderType.SELL_LIMIT):
                params.update(self.exchange_manager.exchange.get_bundled_order_parameters(
                    order,
                    stop_loss_price=None,   # required for cython
                    take_profit_price=chained_order.origin_price
                ))
            if params:
                self.logger.debug(
                    f"Including {chained_order.order_type} chained order into order "
                    f"parameters to handle it directly on exchange."
                )
        await self.chain_order(order, chained_order, update_with_triggering_order_fees, is_bundled, **kwargs)
        return params

    async def chain_order(self, order, chained_order, update_with_triggering_order_fees, is_bundled, **kwargs):
        await chained_order.set_as_chained_order(order, is_bundled, {}, update_with_triggering_order_fees, **kwargs)
        order.add_chained_order(chained_order)
        self.logger.info(f"Added chained order [{chained_order}] to [{order}] order.")

    async def cancel_order(self, order, ignored_order=None,
                           wait_for_cancelling=True,
                           cancelling_timeout=octobot_trading.constants.INDIVIDUAL_ORDER_SYNC_TIMEOUT) -> bool:
        """
        Cancels the given order and updates the portfolio, publish in order channel
        if order is from a real exchange.
        :param order: Order to cancel
        :param ignored_order: Order not to cancel if found in groupped orders recursive cancels (ex: avoid cancelling
        a filled order)
        :param wait_for_cancelling: when True, always make sure the order is completely cancelled before returning.
        On exchanges async api, a cancel request will return before the order is actually cancelled, in this case
        the associated order state will make sure that the order is cancelled by polling the order from the exchange.
        :param cancelling_timeout: time before raising a timeout error when waiting for an order cancel
        :return: None
        """
        if order and order.is_open():
            self.logger.info(f"Cancelling order: {order}")
            # always cancel this order first to avoid infinite loop followed by deadlock
            return await self._handle_order_cancellation(order, ignored_order,
                                                         wait_for_cancelling, cancelling_timeout)
        return False

    async def _handle_order_cancellation(
        self, order, ignored_order, wait_for_cancelling: bool, cancelling_timeout: float
    ) -> bool:
        success = True
        if order.is_waiting_for_chained_trigger:
            # order will just never get created
            order.is_waiting_for_chained_trigger = False
            return success
        # if real order: cancel on exchange
        if not self.simulate and not order.is_self_managed():
            try:
                async with order.lock:
                    try:
                        order_status = await self.exchange_manager.exchange.cancel_order(
                            order.exchange_order_id, order.symbol, order.order_type
                        )
                    except errors.NotSupported:
                        raise
                    except (errors.OrderCancelError, Exception) as inner_err:
                        # retry to cancel order
                        self.logger.info(
                            f"Failed to cancel order ({inner_err} {inner_err.__class__.__name__}), retrying"
                        )
                        order_status = await self.exchange_manager.exchange.cancel_order(
                            order.exchange_order_id, order.symbol, order.order_type
                        )
            except errors.OrderCancelError as err:
                if await self._handle_order_cancel_error(order, err, wait_for_cancelling, cancelling_timeout):
                    return True
            except Exception as err:
                self.logger.exception(err, True, f"Failed to cancel order {order}")
                return False
            if order_status is enums.OrderStatus.CANCELED:
                order.status = octobot_trading.enums.OrderStatus.CANCELED
                self.logger.debug(f"Successfully cancelled order {order}")
            elif order_status is enums.OrderStatus.PENDING_CANCEL:
                order.status = octobot_trading.enums.OrderStatus.PENDING_CANCEL
                self.logger.debug(f"Order cancel in progress for {order}")
        else:
            order.status = octobot_trading.enums.OrderStatus.CANCELED

        await order.on_cancel(force_cancel=order.status is octobot_trading.enums.OrderStatus.CANCELED,
                              is_from_exchange_data=False,
                              ignored_order=ignored_order)
        if wait_for_cancelling and order.state is not None and order.state.is_pending():
            await self._wait_for_order_cancel(order, cancelling_timeout)
        return True

    async def _handle_order_cancel_error(self, order, err, wait_for_cancelling, cancelling_timeout):
        """
        Use when an order can't be cancelled: it usually means that the order is not open on exchange anymore.
        Will synch the given order on exchange to figure out the cancel issue if any.
        Returns True when the order cancel ends up successful even though an error initially occurred
        Raises OrderCancelError on unrecoverable cases
        Raises a subclass of UnexpectedExchangeSideOrderStateError when the order is in a unexpected state
        on exchange but is still manageable.
        """
        if order.state is None:
            raise errors.OrderCancelError(
                f"Error when cancelling order. This order state is unset, which makes "
                f"it impossible to handle this the issue. Please report it if you see it. "
                f"Order: {order}"
            ) from err
        # trigger forced refresh to get an update of the order
        if order.state.is_refreshing():
            await order.state.wait_for_next_state(cancelling_timeout)
        else:
            previous_status = order.status
            await order.state.synchronize(force_synchronization=True)
            if previous_status != order.status:
                # status changed: wait for state change
                await order.state.wait_for_next_state(cancelling_timeout)
        if order.is_cancelled():
            self.logger.debug(f"Tried to cancel an already cancelled order. Order: {order}")
            return True
        if order.is_cancelling():
            if wait_for_cancelling:
                await self._wait_for_order_cancel(order, cancelling_timeout)
            return True
        elif order.is_open():
            if isinstance(err, errors.OrderNotFoundOnCancelError):
                raise errors.OrderNotFoundOnCancelError(
                    f"Tried to cancel an order that can't be found, it might be cancelled or filled already ({err}). "
                    f"Order: {order}"
                ) from err
            raise errors.OpenOrderError(
                f"Order is open, but can't be cancelled. This is unexpected. Order: {order}"
            ) from err
        elif order.is_filled():
            raise errors.FilledOrderError(f"Order is filled, it can't be cancelled. Order: {order}") from err
        elif order.is_closed():
            raise errors.ClosedOrderError(f"Order is closed, it can't be cancelled. Order: {order}") from err
        else:
            # should not happen
            raise errors.OrderCancelError(
                f"Can't cancel order and unknown post sync order state for order: {order}."
            ) from err

    async def cancel_all_orders(
        self,
        symbol: str,
        allow_single_order_cancel_fallback: bool,
        wait_for_cancelling: bool = True,
        cancelling_timeout: float = octobot_trading.constants.INDIVIDUAL_ORDER_SYNC_TIMEOUT
    ) -> bool:
        orders_to_cancel = self.exchange_manager.exchange_personal_data.orders_manager.get_all_orders(symbol)
        success = True
        if orders_to_cancel:
            self.logger.info(f"Cancelling all {len(orders_to_cancel)} {symbol} orders")
        else:
            return success
        try:
            cancel_on_exchange = False
            for order in orders_to_cancel:
                await order.lock.acquire()
                if self.simulate or order.is_self_managed():
                    order.status = octobot_trading.enums.OrderStatus.CANCELED
                else:
                    cancel_on_exchange = True
            if cancel_on_exchange:
                try:
                    success = False
                    await self.exchange_manager.exchange.cancel_all_orders(symbol)
                    success = True
                except errors.NotSupported:
                    if allow_single_order_cancel_fallback:
                        self.logger.debug(
                            f"cancel_all_orders is not supported on {self.exchange_manager.exchange_name}. Falling "
                            f"back to one by one cancel"
                        )
                        for order in orders_to_cancel:
                            if not await self.cancel_order(
                                order.symbol,
                                wait_for_cancelling=wait_for_cancelling,
                                cancelling_timeout=cancelling_timeout
                            ):
                                success = False
                    else:
                        # not supported and no fallback allowed: re-raise errors.NotSupported
                        raise
            for order in orders_to_cancel:
                await order.on_cancel(force_cancel=True, is_from_exchange_data=False)
                if wait_for_cancelling and order.state is not None and order.state.is_pending():
                    await self._wait_for_order_cancel(order, cancelling_timeout)
        finally:
            for order in orders_to_cancel:
                order.lock.release()
        self.logger.info(f"Cancelling of all {len(orders_to_cancel)} {symbol} orders complete")
        return success

    async def _wait_for_order_cancel(self, order, cancelling_timeout):
        self.logger.debug(f"Waiting for order cancelling, order: {order}")
        await order.state.wait_for_terminate(cancelling_timeout)
        self.logger.debug(f"Completed order cancelling, order: {order}")

    async def cancel_order_with_id(self, exchange_order_id, emit_trading_signals=False,
                                   wait_for_cancelling=True,
                                   cancelling_timeout=octobot_trading.constants.INDIVIDUAL_ORDER_SYNC_TIMEOUT):
        """
        Gets order matching order_id from the OrderManager and calls self.cancel_order() on it
        :param exchange_order_id: Exchange id of the order to cancel
        :param emit_trading_signals: when true, trading signals will be emitted
        :param wait_for_cancelling: when True, always make sure the order is completely cancelled before returning.
        :param cancelling_timeout: time before raising a timeout error when waiting for an order cancel
        :return: True if cancel is successful, False if order is not found or cancellation failed
        """
        try:
            order = self.exchange_manager.exchange_personal_data.orders_manager.get_order(exchange_order_id)
            async with signals.remote_signal_publisher(self.exchange_manager, order.symbol, emit_trading_signals):
                return await signals.cancel_order(
                    self.exchange_manager,
                    emit_trading_signals and signals.should_emit_trading_signal(self.exchange_manager),
                    order,
                    wait_for_cancelling=wait_for_cancelling,
                    cancelling_timeout=cancelling_timeout,
                )
        except KeyError:
            return False

    async def cancel_open_orders(self, symbol, cancel_loaded_orders=True, side=None,
                                 emit_trading_signals=False,
                                 wait_for_cancelling=True,
                                 cancelling_timeout=octobot_trading.constants.INDIVIDUAL_ORDER_SYNC_TIMEOUT, 
                                 since: typing.Union[int, float] = octobot_trading.constants.NO_DATA_LIMIT, 
                                 until: typing.Union[int, float] = octobot_trading.constants.NO_DATA_LIMIT
                                 ) -> (bool, list):
        """
        Should be called only if the goal is to cancel all open orders for a given symbol
        :param symbol: The symbol to cancel all orders on
        :param cancel_loaded_orders: When True, also cancels loaded orders (order that are not from this bot instance)
        :param side: When set, only cancels orders from this side
        :param emit_trading_signals: when true, trading signals will be emitted
        :param wait_for_cancelling: when True, always make sure the order is completely cancelled before returning.
        :param cancelling_timeout: time before raising a timeout error when waiting for an order cancel
        :return: (True, orders): True if all orders got cancelled, False if an error occurred and the list of
        cancelled orders
        """
        all_cancelled = True
        cancelled_orders = []
        for order in self.exchange_manager.exchange_personal_data.orders_manager.get_open_orders(since=since, until=until):
            if order.symbol == symbol and \
                    (side is None or order.side is side) and \
                    not (order.is_cancelled() or order.is_closed()) and \
                    (cancel_loaded_orders or order.is_from_this_octobot):
                try:
                    async with signals.remote_signal_publisher(self.exchange_manager, order.symbol, emit_trading_signals):
                        cancelled = await signals.cancel_order(
                            self.exchange_manager,
                            emit_trading_signals and signals.should_emit_trading_signal(self.exchange_manager),
                            order,
                            wait_for_cancelling=wait_for_cancelling,
                            cancelling_timeout=cancelling_timeout, )
                    if cancelled:
                        cancelled_orders.append(order)
                    all_cancelled = cancelled and all_cancelled
                except (errors.OrderCancelError, errors.UnexpectedExchangeSideOrderStateError) as err:
                    self.logger.warning(f"Skipping order cancel: {err} ({err.__class__.__name__})")
        return all_cancelled, cancelled_orders

    async def cancel_all_open_orders_with_currency(
            self, currency, emit_trading_signals=False,
            wait_for_cancelling=True,
            cancelling_timeout=octobot_trading.constants.INDIVIDUAL_ORDER_SYNC_TIMEOUT
    ) -> bool:
        """
        Should be called only if the goal is to cancel all open orders for each traded symbol containing the
        given currency.
        :param currency: Currency to find trading pairs to cancel orders on.
        :param emit_trading_signals: when true, trading signals will be emitted
        :param wait_for_cancelling: when True, always make sure the order is completely cancelled before returning.
        :param cancelling_timeout: time before raising a timeout error when waiting for an order cancel
        :return: True if all orders got cancelled, False if an error occurred
        """
        all_cancelled = True
        symbols = util.get_pairs(self.config, currency, enabled_only=True)
        if symbols:
            for symbol in symbols:
                all_cancelled = (await self.cancel_open_orders(symbol, emit_trading_signals=emit_trading_signals,
                                                               wait_for_cancelling=wait_for_cancelling,
                                                               cancelling_timeout=cancelling_timeout))[0] \
                                and all_cancelled
        return all_cancelled

    async def cancel_all_open_orders(
            self, emit_trading_signals=False,
            wait_for_cancelling=True,
            cancelling_timeout=octobot_trading.constants.INDIVIDUAL_ORDER_SYNC_TIMEOUT
    ) -> bool:
        """
        Cancel all open orders registered on this bot.
        :param emit_trading_signals: when true, trading signals will be emitted
        :param wait_for_cancelling: when True, always make sure the order is completely cancelled before returning.
        :param cancelling_timeout: time before raising a timeout error when waiting for an order cancel
        :return: True if all orders got cancelled, False if an error occurred
        """
        all_cancelled = True
        for order in self.exchange_manager.exchange_personal_data.orders_manager.get_open_orders():
            if not order.is_cancelled():
                try:
                    async with signals.remote_signal_publisher(
                            self.exchange_manager, order.symbol, emit_trading_signals
                    ):
                        all_cancelled = await signals.cancel_order(
                            self.exchange_manager,
                            emit_trading_signals and signals.should_emit_trading_signal(self.exchange_manager),
                            order,
                            wait_for_cancelling=wait_for_cancelling,
                            cancelling_timeout=cancelling_timeout, ) and all_cancelled
                except (errors.OrderCancelError, errors.UnexpectedExchangeSideOrderStateError) as err:
                    self.logger.warning(f"Skipping order cancel: {err} ({err.__class__.__name__})")
                    all_cancelled = False
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
            for order_quantity, order_price in decimal_order_adapter.decimal_check_and_adapt_order_details_if_necessary(
                    quantity, price,
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

    async def close_position(self, position, limit_price=None, timeout=1, emit_trading_signals=False,
                             wait_for_creation=True,
                             creation_timeout=octobot_trading.constants.INDIVIDUAL_ORDER_SYNC_TIMEOUT):
        """
        Creates a close position order
        :param position: the position to close
        :param limit_price: the close order limit price if None uses a market order
        :param timeout: the mark price timeout
        :param emit_trading_signals: when true, trading signals will be emitted
        :param wait_for_creation: when True, always make sure the order is completely created before returning.
        On exchanges async api, a create request will return before the order is actually live on exchange, in this case
        the associated order state will make sure that the order is creating by polling the order from the exchange.
        :param creation_timeout: time before raising a timeout error when waiting for an order creation
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

                current_order = order_factory.create_order_instance(trader=self,
                                                                    order_type=order_type,
                                                                    symbol=position.symbol,
                                                                    current_price=order_price,
                                                                    quantity=order_quantity,
                                                                    price=limit_price
                                                                    if limit_price is not None else order_price,
                                                                    reduce_only=True,
                                                                    close_position=True)
                async with signals.remote_signal_publisher(self.exchange_manager, current_order.symbol,
                                                           emit_trading_signals):
                    order = await signals.create_order(
                        self.exchange_manager,
                        emit_trading_signals and signals.should_emit_trading_signal(self.exchange_manager),
                        current_order,
                        wait_for_creation=wait_for_creation,
                        creation_timeout=creation_timeout
                    )
                created_orders.append(order)
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
            self.logger.info(f"Switching {symbol} leverage from {contract.current_leverage} to {leverage}")
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
            self.logger.info(
                f"Switching {symbol} profit_stop_loss_mode from {contract.take_profit_stop_loss_mode} to {new_mode}"
            )
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
        if contract.margin_type != margin_type:
            if not self.simulate:
                await self.exchange_manager.exchange.set_symbol_margin_type(
                    symbol=symbol,
                    isolated=margin_type is enums.MarginType.ISOLATED
                )
            self.logger.info(f"Switching {symbol} margin_type from {contract.margin_type} to {margin_type}")
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
