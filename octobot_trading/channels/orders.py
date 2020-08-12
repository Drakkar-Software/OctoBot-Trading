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
from asyncio import CancelledError

from octobot_channels.constants import CHANNEL_WILDCARD

from octobot_trading.channels.exchange_channel import ExchangeChannel, ExchangeChannelProducer, ExchangeChannelConsumer, \
    get_chan
from octobot_trading.constants import BALANCE_CHANNEL


class OrdersProducer(ExchangeChannelProducer):
    async def push(self, orders, is_from_bot=False, are_closed=False):
        await self.perform(orders, is_from_bot=is_from_bot, are_closed=are_closed)

    async def perform(self, orders, is_from_bot=False, are_closed=False):
        try:
            symbol = None
            has_new_order = False
            for order in orders:
                symbol = self.channel.exchange_manager.get_exchange_symbol(
                    self.channel.exchange_manager.exchange.parse_order_symbol(order))
                if self.channel.get_filtered_consumers(symbol=CHANNEL_WILDCARD) or self.channel.get_filtered_consumers(
                        symbol=symbol):
                    order_id: str = self.channel.exchange_manager.exchange.parse_order_id(order)

                    # is this order was not managed by order_manager before
                    is_new_order = not self.channel.exchange_manager.exchange_personal_data.orders_manager. \
                        has_order(order_id)
                    has_new_order |= is_new_order

                    # update this order
                    if are_closed:
                        await self._handle_close_order_update(order_id, order)
                    else:
                        await self._handle_open_order_update(symbol, order, order_id, is_from_bot, is_new_order)

            if not are_closed:
                await self._handle_post_open_order_update(symbol, orders, has_new_order)

        except CancelledError:
            self.logger.info("Update tasks cancelled.")
        except Exception as e:
            self.logger.exception(e, True, f"Exception when triggering update: {e}")

    async def _handle_open_order_update(self, symbol, order, order_id, is_from_bot, is_new_order):
        """
        Create or update an open Order from exchange data
        :param symbol: the order symbol
        :param order: the order dict
        :param order_id: the order id
        :param is_from_bot: If the order was created by OctoBot
        :param is_new_order: True if this open order has been created
        """
        if (await self.channel.exchange_manager.exchange_personal_data.handle_order_update_from_raw(
                order_id, order, is_new_order=is_new_order, should_notify=False)):
            await self.send(cryptocurrency=self.channel.exchange_manager.exchange.
                            get_pair_cryptocurrency(symbol),
                            symbol=symbol, order=order,
                            is_from_bot=is_from_bot,
                            is_new=is_new_order)

    async def _handle_close_order_update(self, order_id, order):
        """
        Create or update a close Order from exchange data
        :param order: the order dict
        :param order_id: the order id
        """
        await self.channel.exchange_manager.exchange_personal_data.handle_closed_order_update(order_id, order)

    async def _handle_post_open_order_update(self, symbol, orders, has_new_order):
        """
        Perform post open Order update actions :
        - Check if some previously known open order has not been found during update
        - Force portfolio refresh if a new order has been loaded
        :param symbol: the update symbol
        :param orders: the update order dicts
        :param has_new_order: if a new order has been loaded
        :return:
        """
        if symbol is not None:
            await self._check_missing_open_orders(symbol, orders) or has_new_order

            # if a new order have been loaded : refresh portfolio to ensure available funds are up to date
            if has_new_order:
                await get_chan(BALANCE_CHANNEL, self.channel.exchange_manager.id).get_internal_producer(). \
                    refresh_real_trader_portfolio()

    async def update_order_from_exchange(self, order, should_notify=False) -> bool:
        """
        Update Order from exchange
        :param order: the order to update
        :param should_notify: if Orders channel consumers should be notified
        :return: True if the order was updated
        """
        self.logger.debug(f"Requested update for {order} on {order.exchange_manager.exchange_name}")
        raw_order = await self.channel.exchange_manager.exchange.get_order(order.order_id, order.symbol)

        if raw_order is not None:
            raw_order = self.channel.exchange_manager.exchange.clean_order(raw_order)
            self.logger.debug(f"Received update for {order} on {order.exchange_manager.exchange_name}: {raw_order}")

            return await self.channel.exchange_manager.exchange_personal_data.handle_order_update_from_raw(
                order.order_id, raw_order, should_notify=should_notify)
        return False

    async def _check_missing_open_orders(self, symbol, orders):
        """
        Check if there is no missing open orders in order_manager compared to exchange open orders
        :param symbol: the order symbol
        :param orders: open orders from exchange
        """
        missing_order_ids = list(
            set(
                order.order_id for order in
                self.channel.exchange_manager.exchange_personal_data.orders_manager.get_open_orders(symbol)
                if not order.is_self_managed()) -
            set(
                self.channel.exchange_manager.exchange.parse_order_id(order)
                for order in orders)
        )
        if missing_order_ids:
            self.logger.warning("Open orders are missing, synchronizing with exchange...")
            for missing_order_id in missing_order_ids:
                try:
                    order_to_update = self.channel.exchange_manager.exchange_personal_data.orders_manager.\
                        get_order(missing_order_id)
                    if order_to_update.state is not None:
                        await order_to_update.state.synchronize()
                except KeyError:
                    self.logger.error(f"Order with id {missing_order_id} could not be synchronized")

    async def send(self, cryptocurrency, symbol, order, is_from_bot=True, is_new=False):
        for consumer in self.channel.get_filtered_consumers(symbol=symbol):
            await consumer.queue.put({
                "exchange": self.channel.exchange_manager.exchange_name,
                "exchange_id": self.channel.exchange_manager.id,
                "cryptocurrency": cryptocurrency,
                "symbol": symbol,
                "order": order,
                "is_new": is_new,
                "is_from_bot": is_from_bot
            })


class OrdersChannel(ExchangeChannel):
    PRODUCER_CLASS = OrdersProducer
    CONSUMER_CLASS = ExchangeChannelConsumer
