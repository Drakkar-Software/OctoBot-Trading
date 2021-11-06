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
import octobot_trading.constants as constants
import octobot_trading.personal_data.portfolios.asset as asset_class


class FutureAsset(asset_class.Asset):
    def __init__(self, name, available, total,
                 equity=constants.ZERO,
                 initial_margin=constants.ZERO,
                 margin_balance=constants.ZERO,
                 maintenance_margin=constants.ZERO,
                 position_initial_margin=constants.ZERO,
                 unrealised_pnl=constants.ZERO):
        super().__init__(name, available, total)
        # Account equity = margin Balance + Unrealised PNL
        self.equity = equity

        # Unrealised profit and loss
        self.unrealised_pnl = unrealised_pnl

        # total initial margin required with current mark price
        self.initial_margin = initial_margin

        # Margin balance
        self.margin_balance = margin_balance

        # maintenance margin required
        self.maintenance_margin = maintenance_margin

        # initial margin required for positions with current mark price
        self.position_initial_margin = position_initial_margin

    def __str__(self):
        return super().__str__() + " | " \
                                   f"Equity: {float(self.equity)} | " \
                                   f"Initial Margin: {float(self.initial_margin)} | " \
                                   f"Margin Balance: {float(self.margin_balance)} | " \
                                   f"Maintenance Margin: {float(self.maintenance_margin)} | " \
                                   f"Position Initial Margin: {float(self.position_initial_margin)}"

    def __eq__(self, other):
        if isinstance(other, FutureAsset):
            return self.available == other.available and self.total == other.total and \
                   self.equity == other.equity and self.maintenance_margin == other.maintenance_margin and \
                   self.initial_margin == other.initial_margin and self.margin_balance == other.margin_balance and \
                   self.position_initial_margin == other.position_initial_margin
        return False

    def update(self, available=constants.ZERO, total=constants.ZERO,
               initial_margin=constants.ZERO, margin_balance=constants.ZERO, maintenance_margin=constants.ZERO,
               position_initial_margin=constants.ZERO, unrealised_pnl=constants.ZERO):
        """
        Update asset portfolio
        :param available: the available delta
        :param total: the total delta
        :param initial_margin: the total delta
        :param margin_balance: the total delta
        :param maintenance_margin: the total delta
        :param position_initial_margin: the position_initial_margin delta
        :param unrealised_pnl: the unrealised_pnl delta
        :return: True if updated
        """
        if available == constants.ZERO and total == constants.ZERO and margin_balance == constants.ZERO:
            return False
        self.available += self._ensure_update_validity(self.available, available)
        self.total += self._ensure_update_validity(self.total, total)
        self.initial_margin += self._ensure_update_validity(self.initial_margin, initial_margin)
        self.margin_balance += self._ensure_update_validity(self.margin_balance, margin_balance)
        self.position_initial_margin += self._ensure_update_validity(self.position_initial_margin,
                                                                     position_initial_margin)
        self.maintenance_margin += self._ensure_update_validity(self.maintenance_margin, maintenance_margin)
        self.unrealised_pnl += self._ensure_update_validity(self.unrealised_pnl, unrealised_pnl)
        self._update_equity()
        return True

    def set(self, available=constants.ZERO, total=constants.ZERO,
            initial_margin=constants.ZERO, margin_balance=constants.ZERO, maintenance_margin=constants.ZERO,
            position_initial_margin=constants.ZERO, unrealised_pnl=constants.ZERO):
        """
        Set available, total, initial_margin, margin_balance, position_initial_margin and maintenance_margin
        values for portfolio asset
        :param available: the available value
        :param total: the total value
        :param initial_margin: the total value
        :param margin_balance: the total value
        :param maintenance_margin: the total value
        :param position_initial_margin: the position_initial_margin value
        :param unrealised_pnl: the unrealised_pnl value
        :return: True if updated
        """
        if available == self.available and total == self.total and margin_balance == self.margin_balance:
            return False
        self.available = available
        self.total = total
        self.initial_margin = initial_margin
        self.margin_balance = margin_balance
        self.position_initial_margin = position_initial_margin
        self.maintenance_margin = maintenance_margin
        self.unrealised_pnl = unrealised_pnl
        self._update_equity()
        return True

    def _update_equity(self):
        """
        Update equity value
        Account equity = margin Balance + Unrealised PNL
        """
        self.equity = self.margin_balance + self.unrealised_pnl

    def reset(self):
        """
        Reset asset portfolio to zero
        """
        self.set(available=constants.ZERO, total=constants.ZERO,
                 initial_margin=constants.ZERO, margin_balance=constants.ZERO, unrealised_pnl=constants.ZERO,
                 maintenance_margin=constants.ZERO, position_initial_margin=constants.ZERO)
