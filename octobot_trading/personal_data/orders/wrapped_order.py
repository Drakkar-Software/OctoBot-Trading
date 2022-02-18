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
import octobot_trading.errors as errors


class WrappedOrder:
    """
    WrappedOrder wraps an order to potentially be created later on
    """
    def __init__(self, order, triggered_by, is_waiting_for_chained_trigger=True, portfolio: object = None,
                 params: dict = None, to_be_fetched_only: bool = False, **kwargs):
        self.order = order
        self.triggered_by = triggered_by
        self.portfolio = portfolio
        self.to_be_fetched_only = to_be_fetched_only
        self.params = params
        self.kwargs = kwargs

        self.created = False
        self.created_order = None

        self.order.is_waiting_for_chained_trigger = is_waiting_for_chained_trigger

    async def create_order(self):
        try:
            self.order.is_waiting_for_chained_trigger = False
            if not self.order.trader.simulate and self.to_be_fetched_only:
                # exchange should have created it already, it will automatically be fetched at the next update
                # TODO: check if we need to really fetch it through updater etc
                #  (issue is that we don't have an id yet so we can't just fetch this order in particular)
                pass
            else:
                self.created_order = await self.order.trader.create_order(
                    self.order,
                    portfolio=self.portfolio,
                    loaded=False,
                    params=self.params,
                    triggered_by=self.triggered_by,
                    **self.kwargs
                )
                if self.created_order is None:
                    raise errors.OrderCreationError(f"Failed to create order: {self.order}")
        finally:
            # set created now to consider creation failures as created as well (the caller can always retry later on)
            self.created = True

    def should_be_created(self):
        return not self.created and self.order.is_waiting_for_chained_trigger
