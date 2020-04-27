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
import pandas as pd
from time import time

from octobot_trading.enums import TradeOrderSide


class Book:
    def __init__(self):
        self.orders = pd.DataFrame()
        self.timestamp = 0

    def reset(self):
        self.orders = pd.DataFrame()
        self.timestamp = 0

    def handle_book_update(self, orders, id_key="id"):
        self.orders = pd.json_normalize(orders).set_index(id_key).sort_index(ascending=False)
        self.timestamp = time()

    def handle_book_delta_delete(self, orders, id_key="id"):
        ids = [order[id_key] for order in orders]
        self.orders.drop(index=ids, errors='ignore')

    def handle_book_delta_update(self, orders, id_key="id"):
        update_list = pd.json_normalize(orders).set_index(id_key)
        self.orders.update(update_list)
        self.orders = self.orders.sort_index(ascending=False)
        self.timestamp = time()

    def handle_book_delta_insert(self, orders, id_key="id"):
        insert_list = pd.json_normalize(orders).set_index(id_key)
        self.orders.update(insert_list)
        self.orders = self.orders.sort_index(ascending=False)

    def get_asks(self, side=TradeOrderSide.SELL.value):
        return self.orders.query(f"side.str.contains('{side}')", engine='python').values.tolist()

    def get_bids(self, side=TradeOrderSide.BUY.value):
        return self.orders.query(f"side.str.contains('{side}')", engine='python').values.tolist()
