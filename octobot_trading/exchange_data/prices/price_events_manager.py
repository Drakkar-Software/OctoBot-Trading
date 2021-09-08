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
from octobot_trading.enums import ExchangeConstantsOrderColumns as ECOC


class PriceEventsManager:
    """
    Manage price events for a specific price and timestamp
    Mainly used for updating Order status
    """

    """
    The price event index from a price event tuple
    """
    PRICE_EVENT_INDEX = 2

    def __init__(self):
        self.logger = logging.get_logger(self.__class__.__name__)
        self.events = []

    def reset(self):
        """
        Reset price events
        """
        self.events.clear()

    def handle_recent_trades(self, recent_trades):
        """
        Handle new recent trades prices
        :param recent_trades: prices to check
        """
        for recent_trade in recent_trades:
            try:
                for event_to_set in self._check_events(decimal.Decimal(str(recent_trade[ECOC.PRICE.value])),
                                                       recent_trade[ECOC.TIMESTAMP.value]):
                    self._remove_and_set_event(event_to_set)
            except KeyError:
                self.logger.error("Error when checking price events with recent trades data")

    def handle_price(self, price, timestamp):
        """
        Handle new simple price with timestamp
        :param price: the price to check
        :param timestamp: the timestamp to check
        """
        for event_to_set in self._check_events(decimal.Decimal(str(price)), timestamp):
            self._remove_and_set_event(event_to_set)

    def add_event(self, price, timestamp, trigger_above):
        """
        Add a new event at price and timestamp
        :param price: the trigger price
        :param timestamp: the timestamp to wait for
        :param trigger_above: True if waiting for an upper price
        :return: the price event
        """
        price_event_tuple = _new_price_event(price, timestamp, trigger_above)
        self.events.append(price_event_tuple)
        return price_event_tuple[PriceEventsManager.PRICE_EVENT_INDEX]

    def remove_event(self, event_to_remove):
        """
        Public method that calls _remove_event()
        :param event_to_remove: the event to remove
        """
        return self._remove_event(event_to_remove)

    def _remove_and_set_event(self, event_to_set):
        """
        Set the event and remove it from event list
        :param event_to_set: the event to set
        :return: the event index removed from event list
        """
        event_to_set.set()
        return self._remove_event(event_to_set)

    def _remove_event(self, event_to_remove):
        """
        Remove the event from events list
        :param event_to_remove: the event to remove
        """
        for price_event_data in self.events:
            if event_to_remove in price_event_data:
                return self.events.remove(price_event_data)

    def _check_events(self, price, timestamp):
        """
        Check for each price, timestamp pair event if it should be triggered
        :param price: the price used to check
        :param timestamp: the timestamp used to check
        :return: the event list that match
        """
        return [
            event
            for event_price, event_timestamp, event, trigger_above in self.events
            if event_timestamp <= timestamp and
            (
                (trigger_above and event_price <= price) or
                (not trigger_above and event_price >= price)
            )
        ]


def _new_price_event(price, timestamp, trigger_above):
    """
    Create a new price event item
    :param price: the price condition
    :param timestamp: the timestamp condition
    :param trigger_above: True if waiting for an upper price
    :return: a tuple to be added into events list
    """
    return price, timestamp, asyncio.Event(), trigger_above
