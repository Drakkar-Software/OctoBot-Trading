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

import octobot_commons.logging as logging

import octobot_trading.constants
import octobot_trading.enums as enums
import octobot_trading.errors
import octobot_trading.exchange_channel as exchange_channel
import octobot_trading.personal_data.state as state_class


class OrderState(state_class.State):
    def __init__(self, order, is_from_exchange_data, enable_associated_orders_creation=True):
        super().__init__(is_from_exchange_data)

        # ensure order has not been cleared
        self.ensure_not_cleared(order)

        # related order
        self.order = order

        self.enable_associated_orders_creation = enable_associated_orders_creation

    def is_created(self) -> bool:
        """
        :return: True if the Order is created
        """
        return True

    def is_open(self) -> bool:
        """
        :return: True if the Order is considered as open
        """
        return not (self.is_filled() or self.is_canceled() or self.is_closed())

    def is_filled(self) -> bool:
        """
        :return: True if the Order is considered as filled
        """
        return False

    def is_canceled(self) -> bool:
        """
        :return: True if the Order is considered as canceled
        """
        return False

    def get_logger(self):
        """
        :return: the order logger
        """
        return logging.get_logger(self.order.get_logger_name() if self.order is not None else
                                  f"{self.__class__.__name__}_without_order")

    def log_event_message(self, state_message, error=None):
        """
        Log an order state event
        """
        if state_message is enums.StatesMessages.ALREADY_SYNCHRONIZING:
            self.get_logger().debug(f"Trying to update a refreshing state for order: {self.order}")
        elif state_message is enums.StatesMessages.SYNCHRONIZING_ERROR:
            self.get_logger().exception(error, True, f"Error when synchronizing order {self.order}: {error}")
        else:
            exchange_name = self.order.exchange_manager.exchange_name if self.order.exchange_manager \
                else 'unknown exchange'
            self.get_logger().info(f"{self.order} {state_message.value} on {exchange_name}")

    async def should_be_updated(self) -> bool:
        """
        Defines if the instance should be updated
        :return: True when the order type is supported by the exchange
        """
        return self.order.is_self_managed()

    def allows_new_status(self, status) -> bool:
        """
        :return: True if the given status is compatible with the current state
        """
        return True

    async def replace_order(self, new_order):
        async with self.refresh_operation():
            self.order.state = None
            self.order = new_order
            self.order.state = self

    async def _synchronize_with_exchange(self, force_synchronization: bool = False) -> None:
        """
        Ask OrdersChannel Internal producer to refresh the order from the exchange
        :param force_synchronization: When True, for the update of the order from the exchange
        :return: the result of OrdersProducer.update_order_from_exchange()
        """
        try:
            self.ensure_not_cleared(self.order)
            self.get_logger().info(
                f"Synchronizing order {self.order} with {self.order.exchange_manager.exchange_name} exchange"
            )
            await exchange_channel.get_chan(
                octobot_trading.constants.ORDERS_CHANNEL,
                self.order.exchange_manager.id
            ).get_internal_producer().update_order_from_exchange(
                order=self.order,
                wait_for_refresh=True,
                force_job_execution=force_synchronization,
            )
        except octobot_trading.errors.InvalidOrderState:
            self.get_logger().debug(f"Skipping exchange synchronisation as order has already been closed.")

    async def wait_for_next_state(self, timeout) -> None:
        # terminate is called at the end of the state for most order states
        await self.wait_for_terminate(timeout)

    @staticmethod
    def ensure_not_cleared(order):
        if order.is_cleared():
            raise octobot_trading.errors.InvalidOrderState(f"Order has already been cleared. Order: {order}")

    def _is_synchronization_enabled(self):
        return (
            self.order.exchange_manager is not None and
            self.order.exchange_manager.exchange_personal_data.orders_manager.enable_order_auto_synchronization
        )

    def clear(self):
        """
        Clear references
        """
        self.order = None
