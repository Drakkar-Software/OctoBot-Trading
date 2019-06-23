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
import time


class Position:
    def __init__(self, trader):
        self.trader = trader

        self.position_id = None
        self.timestamp = None
        self.symbol = None
        self.currency, self.market = None, None
        self.creation_time = None
        self.entry_price = None
        self.mark_price = None
        self.quantity = None
        self.liquidation_price = None
        self.unrealised_pnl = None
        self.leverage = None
        self.is_open = None

    def update(self, position_id, symbol, currency, market,
               timestamp, entry_price, mark_price, quantity,
               liquidation_price, unrealised_pnl, leverage, is_open):
        changed: bool = False

        if position_id and self.position_id != position_id:
            self.position_id = position_id

        if symbol and self.symbol != symbol:
            self.symbol, self.currency, self.market = symbol, currency, market

        if timestamp and self.timestamp != timestamp:
            self.timestamp = timestamp
        if not self.timestamp:
            if not timestamp:
                self.creation_time = time.time()
            else:
                # if we have a timestamp, it's a real trader => need to format timestamp if necessary
                self.creation_time = self.exchange.get_uniform_timestamp(timestamp)
            self.timestamp = self.creation_time

        if quantity and self.quantity != quantity:
            self.quantity = quantity
            changed = True

        if unrealised_pnl and self.unrealised_pnl != unrealised_pnl:
            self.unrealised_pnl = unrealised_pnl
            changed = True

        if leverage and self.leverage != leverage:
            self.leverage = leverage
            changed = True

        if entry_price and self.entry_price != entry_price:
            self.entry_price = entry_price

        if mark_price and self.mark_price != mark_price:
            self.mark_price = mark_price

        if liquidation_price and self.liquidation_price != liquidation_price:
            self.liquidation_price = liquidation_price

        if is_open and self.is_open != is_open:
            self.is_open = is_open
            changed = True

        return changed
