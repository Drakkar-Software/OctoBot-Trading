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
import asyncio
import decimal

import octobot_commons.logging as logging

import octobot_trading.enums as enums
import octobot_trading.constants as constants
import octobot_trading.personal_data.orders.order as order_class


class TrailingStopOrder(order_class.Order):
    UNINITIALIZED_TRAILING_PERCENT = decimal.Decimal(str(-1))
    DEFAULT_TRAILING_PERCENT = decimal.Decimal(str(5))

    def __init__(self, trader, side=enums.TradeOrderSide.SELL, trailing_percent=UNINITIALIZED_TRAILING_PERCENT):
        super().__init__(trader, side=side)
        self.order_type = enums.TraderOrderType.TRAILING_STOP
        self.trailing_stop_price_hit_event = None
        self.trailing_price_hit_event = None
        self.wait_for_stop_price_hit_event_task = None
        self.wait_for_price_hit_event_task = None
        self.trailing_percent = trailing_percent

    async def update_order_status(self, force_refresh=False):
        if not self.trader.simulate and (not self.is_synchronized_with_exchange or force_refresh):
            await self.default_exchange_update_order_status()
        await self._reset_events(self.origin_price, self.creation_time)

    async def set_trailing_percent(self, trailing_percent):
        """
        Set trailing percent and reset event and tasks
        :param trailing_percent: the new trailing percent
        """
        self.trailing_percent = trailing_percent
        await self._reset_events(self.origin_price, self.creation_time)

    async def _reset_events(self, new_price, new_price_time):
        """
        Reset events and tasks
        :param new_price: the new trailing price
        """
        self._clear_event_and_tasks()
        price_events_manager = self.exchange_manager.exchange_symbols_data. \
            get_exchange_symbol_data(self.symbol).price_events_manager
        self._create_hit_events(price_events_manager, new_price, new_price_time)
        self._create_hit_tasks()

    def _create_hit_events(self, price_events_manager, new_price, new_price_time):
        """
        Create prices hit events
        :param price_events_manager: the price events manager to use
        :param new_price: the new trailing price
        """
        if self.trailing_stop_price_hit_event is None:
            self.trailing_stop_price_hit_event = price_events_manager.add_event(
                self._calculate_stop_price(new_price), new_price_time,
                self.side is enums.TradeOrderSide.BUY)
        if self.trailing_price_hit_event is None:
            self.trailing_price_hit_event = price_events_manager.add_event(new_price, new_price_time,
                                                                           self.side is enums.TradeOrderSide.SELL)

    def _calculate_stop_price(self, new_price):
        """
        Calculate the trailing stop price from price and trailing percent
        :param new_price: the price
        :return: the stop price related to the specified price
        """
        trailing_price_factor = (self.trailing_percent
                                 if self.trailing_percent != self.UNINITIALIZED_TRAILING_PERCENT
                                 else self.DEFAULT_TRAILING_PERCENT) / decimal.Decimal("100")
        trailing_price_factor *= constants.ONE if self.side is enums.TradeOrderSide.BUY else -constants.ONE
        return new_price * (constants.ONE + trailing_price_factor)

    def _create_hit_tasks(self):
        """
        Create event hit waiting tasks
        """
        if self.wait_for_price_hit_event_task is None and self.trailing_price_hit_event is not None:
            self.wait_for_price_hit_event_task = asyncio.create_task(
                _wait_for_price_hit(self.trailing_price_hit_event, self._on_price_hit))

        if self.wait_for_stop_price_hit_event_task is None and self.trailing_stop_price_hit_event is not None:
            self.wait_for_stop_price_hit_event_task = asyncio.create_task(
                _wait_for_price_hit(self.trailing_stop_price_hit_event, self.on_fill))

    def _remove_events(self, price_events_manager):
        """
        Remove events from the price events manager
        :param price_events_manager: the price events manager to use
        """
        if self.trailing_stop_price_hit_event is not None:
            price_events_manager.remove_event(self.trailing_stop_price_hit_event)
            self.trailing_stop_price_hit_event = None
        if self.trailing_price_hit_event is not None:
            price_events_manager.remove_event(self.trailing_price_hit_event)
            self.trailing_price_hit_event = None

    def _cancel_hit_tasks(self):
        """
        Cancel and destroy event hit waiting tasks
        """
        if self.wait_for_price_hit_event_task is not None:
            if not self.trailing_price_hit_event.is_set():
                self.wait_for_price_hit_event_task.cancel()
            self.wait_for_price_hit_event_task = None

        if self.wait_for_stop_price_hit_event_task is not None:
            if not self.trailing_stop_price_hit_event.is_set():
                self.wait_for_stop_price_hit_event_task.cancel()
            self.wait_for_stop_price_hit_event_task = None

    async def _on_price_hit(self):
        """
        Is called when the trailing price is hit
        """
        prices_manager = self.exchange_manager.exchange_symbols_data. \
            get_exchange_symbol_data(self.symbol).prices_manager
        logging.get_logger(self.get_logger_name()).debug(f"New price hit {prices_manager.mark_price}, "
                                                         f"replacing stop...")
        await self._reset_events(decimal.Decimal(str(prices_manager.mark_price)), prices_manager.mark_price_set_time)

    async def on_filled(self):
        """
        Create an artificial when trailing stop is filled
        """
        await order_class.Order.on_filled(self)
        await self.trader.create_artificial_order(enums.TraderOrderType.SELL_MARKET
                                                  if self.side is enums.TradeOrderSide.SELL
                                                  else enums.TraderOrderType.BUY_MARKET,
                                                  self.symbol, self.origin_stop_price,
                                                  self.origin_quantity, self.origin_stop_price,
                                                  self.linked_portfolio)

    def _clear_event_and_tasks(self):
        """
        Clear prices hit events and their related tasks
        """
        self._cancel_hit_tasks()
        self._remove_events(self.exchange_manager.exchange_symbols_data.
                            get_exchange_symbol_data(self.symbol).price_events_manager)

    def clear(self):
        """
        Clear prices hit events and their related tasks and call super clear
        """
        self._clear_event_and_tasks()
        order_class.Order.clear(self)


async def _wait_for_price_hit(event_to_wait, callback):
    """
    Awaitable wait for event and call the specified callback
    :param event_to_wait: the event to wait
    :param callback: the callback to call
    """
    await asyncio.wait_for(event_to_wait.wait(), timeout=None)
    await callback()
