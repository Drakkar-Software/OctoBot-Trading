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
                 initial_margin=constants.ZERO,
                 wallet_balance=constants.ZERO,
                 maintenance_margin=constants.ZERO,
                 position_margin=constants.ZERO,
                 order_margin=constants.ZERO,
                 unrealised_pnl=constants.ZERO):
        """
        Future Asset
        :param name: the asset name
        :param available: the margin available (wallet balance - used margin)
        :param total: the margin balance (wallet balance + unrealised PNL)
        :param initial_margin: the total initial margin required with current mark price
        :param wallet_balance: the wallet balance
        :param maintenance_margin: the maintenance margin required
        :param position_margin: margin required for positions with current mark price
        :param order_margin: margin required for open orders with current mark price
        :param unrealised_pnl: the unrealised profit and loss
        """
        super().__init__(name, available, total)
        # Unrealised profit and loss
        self.unrealised_pnl = unrealised_pnl

        # total initial margin required with current mark price
        self.initial_margin = initial_margin

        # The Wallet balance. When using Cross Margin, the number minus the unclosed loss is the real wallet balance.
        self.wallet_balance = wallet_balance if wallet_balance != constants.ZERO else total

        # maintenance margin required
        self.maintenance_margin = maintenance_margin

        # margin required for positions with current mark price
        self.position_margin = position_margin

        # margin required for open orders with current mark price
        self.order_margin = order_margin

    def __str__(self):
        return super().__str__() + " | " \
                                   f"Initial Margin: {float(self.initial_margin)} | " \
                                   f"Wallet Balance: {float(self.wallet_balance)} | " \
                                   f"Maintenance Margin: {float(self.maintenance_margin)} | " \
                                   f"Unrealized PNL: {float(self.unrealised_pnl)} | " \
                                   f"Order Margin: {float(self.order_margin)} | " \
                                   f"Position Margin: {float(self.position_margin)}"

    def __eq__(self, other):
        if isinstance(other, FutureAsset):
            return self.available == other.available and self.total == other.total and \
                   self.maintenance_margin == other.maintenance_margin and self.initial_margin == other.initial_margin \
                   and self.wallet_balance == other.wallet_balance and \
                   self.position_margin == other.position_margin and self.order_margin == other.order_margin
        return False

    def update(self, available=constants.ZERO, total=constants.ZERO,
               initial_margin=constants.ZERO, wallet_balance=constants.ZERO, maintenance_margin=constants.ZERO,
               position_margin=constants.ZERO, order_margin=constants.ZERO, unrealised_pnl=constants.ZERO):
        """
        Update asset portfolio
        :param available: the available margin balance delta
        :param total: the margin balance delta
        :param initial_margin: the initial margin delta
        :param wallet_balance: the wallet balance delta
        :param maintenance_margin: the maintenance margin delta
        :param position_margin: the position margin delta
        :param order_margin: the order margin delta
        :param unrealised_pnl: the unrealised pnl delta
        :return: True if updated
        """
        if available == constants.ZERO and total == constants.ZERO and wallet_balance == constants.ZERO:
            return False
        self.available += self._ensure_update_validity(self.available, available)
        self.initial_margin += self._ensure_update_validity(self.initial_margin, initial_margin)
        self.position_margin += self._ensure_update_validity(self.position_margin, position_margin)
        self.order_margin += self._ensure_update_validity(self.order_margin, order_margin)
        self.maintenance_margin += self._ensure_update_validity(self.maintenance_margin, maintenance_margin)
        self.unrealised_pnl += self._ensure_update_validity(self.unrealised_pnl, unrealised_pnl)
        self.wallet_balance += self._ensure_update_validity(self.wallet_balance, wallet_balance)
        self.total += self._ensure_update_validity(self.total, total) \
            if total != constants.ZERO else self.wallet_balance + self.unrealised_pnl
        return True

    def set(self, available=constants.ZERO, total=constants.ZERO,
            initial_margin=constants.ZERO, wallet_balance=constants.ZERO, maintenance_margin=constants.ZERO,
            position_margin=constants.ZERO, order_margin=constants.ZERO, unrealised_pnl=constants.ZERO):
        """
        Set available, total, initial_margin, wallet_balance, position_margin and maintenance_margin
        values for portfolio asset
        :param available: the available margin balance value
        :param total: the margin balance value
        :param initial_margin: the initial margin value
        :param wallet_balance: the wallet balance value
        :param maintenance_margin: the maintenance margin value
        :param position_margin: the position margin value
        :param order_margin: the order margin value
        :param unrealised_pnl: the unrealised pnl value
        :return: True if updated
        """
        if available == self.available and total == self.total and wallet_balance == self.wallet_balance:
            return False
        self.available = available
        self.initial_margin = initial_margin
        self.position_margin = position_margin
        self.order_margin = order_margin
        self.maintenance_margin = maintenance_margin
        self.unrealised_pnl = unrealised_pnl
        self.wallet_balance = wallet_balance
        self.total = total if total != constants.ZERO else self.wallet_balance + self.unrealised_pnl
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
                 initial_margin=constants.ZERO, wallet_balance=constants.ZERO, unrealised_pnl=constants.ZERO,
                 maintenance_margin=constants.ZERO, order_margin=constants.ZERO, position_margin=constants.ZERO)
