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

import octobot_trading.constants as constants
import octobot_trading.errors as errors
import octobot_trading.personal_data.orders.order_util as order_util
import octobot_commons.symbols as symbols


class TradePnl:
    def __init__(self, entries, closes):
        self.entries = entries
        self.closes = closes

    def get_entry_time(self) -> float:
        try:
            return min(
                entry.executed_time
                for entry in self.entries
            )
        except ValueError as err:
            raise errors.IncompletePNLError from err

    def get_close_time(self) -> float:
        try:
            return max(
                close.executed_time
                for close in self.closes
            )
        except ValueError as err:
            raise errors.IncompletePNLError from err

    def get_total_entry_quantity(self) -> decimal.Decimal:
        return sum(
            entry.executed_quantity
            for entry in self.entries
        ) or constants.ZERO

    def get_total_close_quantity(self) -> decimal.Decimal:
        return sum(
            close.executed_quantity
            for close in self.closes
        ) or constants.ZERO

    def get_entry_price(self) -> decimal.Decimal:
        try:
            return sum(
                entry.executed_price
                for entry in self.entries
            ) / len(self.entries)
        except ZeroDivisionError as err:
            raise errors.IncompletePNLError from err

    def get_close_price(self) -> decimal.Decimal:
        try:
            return sum(
                close.executed_price
                for close in self.closes
            ) / len(self.closes)
        except ZeroDivisionError as err:
            raise errors.IncompletePNLError from err

    def get_closed_entry_value(self) -> decimal.Decimal:
        return self.get_entry_price() * self.get_closed_pnl_quantity()

    def get_closed_close_value(self) -> decimal.Decimal:
        return self.get_close_price() * self.get_closed_pnl_quantity()

    def get_closed_pnl_quantity(self):
        return min(self.get_total_close_quantity(), self.get_total_entry_quantity())

    def _get_fees(self, trade) -> decimal.Decimal:
        if not trade.fee:
            return constants.ZERO
        symbol = symbols.parse_symbol(trade.symbol)
        # return fees denominated in quote
        fees = order_util.get_fees_for_currency(trade.fee, symbol.quote)
        return fees \
            + order_util.get_fees_for_currency(trade.fee, symbol.base) * trade.executed_price

    def get_total_paid_fees(self) -> decimal.Decimal:
        return sum(
            self._get_fees(trade)
            for trade in (*self.entries, *self.closes)
        ) or constants.ZERO

    def get_profits(self) -> (decimal.Decimal, decimal.Decimal):
        """
        :return: the pnl profits as flat value and percent
        """
        close_holdings = self.get_closed_close_value() - self.get_total_paid_fees()
        entry_holdings = self.get_closed_entry_value()
        return (
            close_holdings - entry_holdings,
            (close_holdings * constants.ONE_HUNDRED / entry_holdings) - constants.ONE_HUNDRED
        )
