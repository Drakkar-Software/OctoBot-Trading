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
import octobot_commons.constants as common_constants

import octobot_trading.constants as constants
import octobot_trading.errors as errors


class Asset:
    def __init__(self, name, available, total):
        self.name = name

        self.available = available
        self.total = total

    def __str__(self):
        return f"{self.__class__.__name__}: {self.name} | " \
               f"Available: {float(self.available)} | " \
               f"Total: {float(self.total)}"

    def __eq__(self, other):
        raise NotImplementedError("__eq__ is not implemented")

    def update(self, **kwargs):
        """
        Update asset portfolio
        :return: True if updated
        """
        raise NotImplementedError("update is not implemented")

    def set(self, **kwargs):
        """
        Set portfolio asset
        :return: True if updated
        """
        raise NotImplementedError("set is not implemented")

    def restore_available(self):
        """
        Balance available value with total
        """
        self.available = self.total

    def reset(self):
        """
        Reset asset portfolio to zero
        """
        raise NotImplementedError("reset is not implemented")

    def to_dict(self):
        """
        :return: asset to dictionary
        """
        return {
            common_constants.PORTFOLIO_AVAILABLE: self.available,
            common_constants.PORTFOLIO_TOTAL: self.total
        }

    def _ensure_update_validity(self, origin_quantity, update_quantity):
        """
        Ensure that the portfolio final value is not negative.
        Raise a PortfolioNegativeValueError if the final value is negative
        :param origin_quantity: the original currency value
        :param update_quantity: the update value
        :return: the updated quantity
        """
        if origin_quantity + update_quantity < constants.ZERO:
            raise errors.PortfolioNegativeValueError(f"Trying to update {self.name} with {update_quantity} "
                                                     f"but quantity was {origin_quantity}")
        return update_quantity

    def _ensure_not_negative(self, new_value, replacement_value=constants.ZERO):
        """
        Ensure that the new asset value is not negative
        When new value is negative return replacement_value
        :param new_value: the value to check
        :param replacement_value: the replacement value when new value is negative
        :return: the new value if not negative else the replacement value
        """
        if new_value > constants.ZERO:
            return new_value
        return replacement_value
