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

from octobot_trading.channels.exchange_channel import ExchangeChannel, ExchangeChannelProducer, ExchangeChannelConsumer


class OrdersProducer(ExchangeChannelProducer):
    async def push(self, orders, is_closed=False, is_from_bot=True):
        await self.perform(orders, is_closed=is_closed, is_from_bot=is_from_bot)

    async def perform(self, orders, is_closed=False, is_from_bot=True):
        try:
            symbol = None
            for order in orders:
                symbol = self.channel.exchange_manager.get_exchange_symbol(
                    self.channel.exchange_manager.exchange.parse_order_symbol(order))
                if self.channel.get_filtered_consumers(symbol=CHANNEL_WILDCARD) or self.channel.get_filtered_consumers(
                        symbol=symbol):
                    order_id: str = self.channel.exchange_manager.exchange.parse_order_id(order)

                    if is_closed:
                        # Only possible if closed by OctoBot or if updating closed orders
                        changed = await self.channel.exchange_manager.exchange_personal_data.handle_closed_order_update(
                            symbol,
                            order_id,
                            order,
                            should_notify=False)
                    else:
                        changed = \
                            await self.channel.exchange_manager.exchange_personal_data.handle_order_update_from_raw(
                                symbol,
                                order_id,
                                order,
                                should_notify=False)

                    if changed:
                        await self.send(cryptocurrency=self.channel.exchange_manager.exchange.
                                        get_pair_cryptocurrency(symbol),
                                        symbol=symbol, order=order,
                                        is_from_bot=is_from_bot,
                                        is_closed=is_closed,
                                        is_updated=changed)

            if symbol is not None:
                await self._check_missing_open_orders(symbol, orders)
        except CancelledError:
            self.logger.info("Update tasks cancelled.")
        except Exception as e:
            self.logger.exception(e, True, f"Exception when triggering update: {e}")

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
            return await self.channel.exchange_manager.exchange_personal_data.handle_order_update_from_raw(
                order.symbol,
                order.order_id,
                raw_order,
                should_notify=should_notify)
        else:
            self.logger.warning(f"Order with id {order.order_id} does not exist")
            self.channel.exchange_manager.exchange_personal_data.orders_manager.remove_order_instance(order)
        return True

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
                    await self.update_order_from_exchange(
                        self.channel.exchange_manager.exchange_personal_data.orders_manager.get_order(missing_order_id),
                        should_notify=True)
                except KeyError:
                    self.logger.error(f"Order with id {missing_order_id} could not be synchronized")

    async def send(self, cryptocurrency, symbol, order, is_from_bot=True, is_closed=False, is_updated=False):
        for consumer in self.channel.get_filtered_consumers(symbol=symbol):
            await consumer.queue.put({
                "exchange": self.channel.exchange_manager.exchange_name,
                "exchange_id": self.channel.exchange_manager.id,
                "cryptocurrency": cryptocurrency,
                "symbol": symbol,
                "order": order,
                "is_closed": is_closed,
                "is_updated": is_updated,
                "is_from_bot": is_from_bot
            })


class OrdersChannel(ExchangeChannel):
    PRODUCER_CLASS = OrdersProducer
    CONSUMER_CLASS = ExchangeChannelConsumer
