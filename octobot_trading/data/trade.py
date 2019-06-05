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
from octobot_trading.data.order import Order


class Trade:
    def __init__(self, exchange, order: Order):
        self.exchange = exchange
        self.order = order
        self.currency, self.market = self.order.get_currency_and_market()
        self.quantity = self.order.filled_quantity
        self.price = self.order.filled_price
        self.cost = self.order.total_cost
        self.order_type = self.order.order_type
        self.final_status = self.order.status
        self.fee = self.order.fee
        self.order_id = self.order.order_id
        self.side = self.order.side
        self.creation_time = self.order.creation_time
        self.canceled_time = self.order.canceled_time
        self.filled_time = self.order.executed_time
        self.symbol = self.order.symbol
        self.simulated = self.order.trader.simulate
