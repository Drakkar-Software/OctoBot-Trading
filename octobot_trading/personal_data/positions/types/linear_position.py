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
import octobot_trading.personal_data.positions.position as position_class


class LinearPosition(position_class.Position):
    def update_value(self):
        """
        Notional value = CONTRACT_QUANTITY * MARK_PRICE
        """
        self.value = self.quantity * self.mark_price

    def update_pnl(self):
        """
        LONG_PNL = CONTRACT_QUANTITY x [MARK_PRICE - ENTRY_PRICE]
        SHORT_PNL = CONTRACT_QUANTITY x [ENTRY_PRICE - MARK_PRICE]
        """
        try:
            if self.is_long():
                self.unrealised_pnl = self.quantity * (self.mark_price - self.entry_price)
            elif self.is_short():
                self.unrealised_pnl = -self.quantity * (self.entry_price - self.mark_price)
            else:
                self.unrealised_pnl = constants.ZERO
            self.on_pnl_update()
        except (decimal.DivisionByZero, decimal.InvalidOperation):
            self.unrealised_pnl = constants.ZERO

    def update_initial_margin(self):
        """
        Updates position initial margin = (Position quantity x entry price) / leverage
        """
        try:
            self.initial_margin = (self.quantity * self.entry_price) / self.symbol_contract.current_leverage
            self._update_margin()
        except (decimal.DivisionByZero, decimal.InvalidOperation):
            self.initial_margin = constants.ZERO

    def calculate_maintenance_margin(self):
        """
        :return: Maintenance margin = Position quantity x entry price x Maintenance margin rate
        """
        return self.quantity * self.entry_price * self.get_maintenance_margin_rate()

    def update_isolated_liquidation_price(self):
        """
        Updates isolated position liquidation price
        LONG LIQUIDATION PRICE = ENTRY_PRICE * (1 - Initial Margin Rate + MAINTENANCE_MARGIN_RATE)
        SHORT LIQUIDATION PRICE = ENTRY_PRICE * (1 + Initial Margin Rate - MAINTENANCE_MARGIN_RATE)
        - Long : - Extra Margin Added/ Contract Size
        - Short : + Extra Margin Added/ Contract Size
        """
        try:
            if self.is_long():
                self.liquidation_price = self.entry_price * (
                        constants.ONE - self.get_initial_margin_rate() + self.calculate_maintenance_margin())
            elif self.is_short():
                self.liquidation_price = self.entry_price * (
                        constants.ONE + self.get_initial_margin_rate() - self.calculate_maintenance_margin())
            else:
                self.liquidation_price = constants.ZERO
            self.update_fee_to_close()
        except (decimal.DivisionByZero, decimal.InvalidOperation):
            self.liquidation_price = constants.ZERO

    def get_bankruptcy_price(self, with_mark_price=False):
        """
        :param with_mark_price: if price should be mark price instead of entry price
        :return: Bankruptcy Price
        Long position = Entry Price x (1 - Initial Margin Rate)
        Short position = Entry Price × (1 + Initial Margin Rate)
        """
        if self.is_long():
            return self.mark_price \
                if with_mark_price else self.entry_price * (constants.ONE - self.get_initial_margin_rate())
        elif self.is_short():
            return self.mark_price \
                if with_mark_price else self.entry_price * (constants.ONE + self.get_initial_margin_rate())
        return constants.ZERO

    def get_fee_to_open(self):
        """
        :return: Fee to open = (Quantity * Mark Price) x Taker fee
        """
        return self.quantity * self.mark_price * self.get_taker_fee()

    def get_order_cost(self):
        """
        :return: Order Cost = Initial Margin + Two-Way Taker Fee
        """
        return self.initial_margin + self.get_two_way_taker_fee()

    def update_fee_to_close(self):
        """
        :return: Fee to close = (Quantity * Bankruptcy Price derived from mark price) x Taker fee
        """
        self.fee_to_close = self.quantity * self.get_bankruptcy_price(with_mark_price=True) * self.get_taker_fee()

    def update_average_entry_price(self, update_size, update_price):
        """
        Average entry price = total contract value in market / total quantity of contracts
        Total contract value in market = [(Current position quantity * Current position entry price)
                                          + (Update quantity * Update price)]
        """
        total_contract_value = self.size + update_size
        self.entry_price = ((self.size * self.entry_price + update_size * update_price) /
                            (total_contract_value if total_contract_value != constants.ZERO else constants.ONE))
        if self.entry_price < constants.ZERO:
            self.entry_price = constants.ZERO
