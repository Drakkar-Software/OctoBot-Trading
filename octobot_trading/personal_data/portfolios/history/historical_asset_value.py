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
import copy


class HistoricalAssetValue:
    """
    HistoricalAssetValue stores the portfolio value at a given time in multiple currencies
    """
    TIMESTAMP_KEY = "t"
    VALUES_KEY = "v"

    def __init__(self, timestamp, value_by_currency):
        self._timestamp = timestamp
        self._value_by_currency = copy.copy(value_by_currency)

    def __contains__(self, item):
        return item in self._value_by_currency

    def get(self, currency):
        return self._value_by_currency[currency]

    def set(self, currency, value):
        self._value_by_currency[currency] = value

    def update(self, value_by_currency):
        # update exiting values and add new ones
        if self._value_by_currency == value_by_currency:
            return False
        self._value_by_currency.update(value_by_currency)
        return True

    def get_currencies(self):
        return self._value_by_currency.keys()

    def get_timestamp(self):
        return self._timestamp

    def to_dict(self):
        return {
            self.TIMESTAMP_KEY: self._timestamp,
            self.VALUES_KEY: {currency: float(value) for currency, value in self._value_by_currency.items()}
        }
