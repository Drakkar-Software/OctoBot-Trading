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
import dataclasses
import decimal

import octobot_trading.personal_data.orders.order as order_import


@dataclasses.dataclass
class ResolvedOrdersPortoflioDelta:
    explained_orders_deltas: dict[str, decimal.Decimal] = dataclasses.field(default_factory=dict)
    unexplained_orders_deltas: dict[str, dict[str, decimal.Decimal]] = dataclasses.field(default_factory=dict)
    inferred_filled_orders: list[order_import.Order] = dataclasses.field(default_factory=list)
    inferred_cancelled_orders: list[order_import.Order] = dataclasses.field(default_factory=list)


    def is_more_probable_than(self, other: 'ResolvedOrdersPortoflioDelta') -> bool:
        """
        More probable means that the number or value of unexplained orders deltas is lower.
        """
        if len(self.explained_orders_deltas) > len(other.explained_orders_deltas):
            # self has more explained orders deltas: it is more probable
            return True
        if len(self.explained_orders_deltas) < len(other.explained_orders_deltas):
            # self has less explained orders deltas: it is less probable
            return False
        for asset_name, asset_deltas in self.unexplained_orders_deltas.items():
            if asset_name not in other.unexplained_orders_deltas:
                # self has unexplained orders deltas that other does not: skip it
                continue
            for key, delta in asset_deltas.items():
                if key not in other.unexplained_orders_deltas[asset_name]:
                    # missing key in other: should not happen
                    raise KeyError(f"missing key {key} in other.unexplained_orders_deltas[{asset_name}]")
                if other.unexplained_orders_deltas[asset_name][key] > delta:
                    # other has unexplained orders deltas that self does not: it is less probable
                    return False
                    # todo compare with value if can be found in orders
        # self and other have the same number of unexplained orders deltas: but self does not have larger unexplained order deltas. 
        # Self is more probable
        return True


    def has_inferred_orders(self) -> bool:
        return bool(self.inferred_filled_orders or self.inferred_cancelled_orders)
