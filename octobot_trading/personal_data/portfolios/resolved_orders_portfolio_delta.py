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

import octobot_trading.constants as constants
import octobot_trading.personal_data.orders.order as order_import


@dataclasses.dataclass
class ResolvedOrdersPortoflioDelta:
    explained_orders_deltas: dict[str, dict[str, decimal.Decimal]] = dataclasses.field(default_factory=dict)
    unexplained_orders_deltas: dict[str, dict[str, decimal.Decimal]] = dataclasses.field(default_factory=dict)
    inferred_filled_orders: list[order_import.Order] = dataclasses.field(default_factory=list)
    inferred_cancelled_orders: list[order_import.Order] = dataclasses.field(default_factory=list)


    def is_more_probable_than(self, other: 'ResolvedOrdersPortoflioDelta') -> bool:
        """
        More probable means that:
            - the number of explained orders deltas is higher
            - the number of unexplained orders deltas is lower
        """
        if (
            self.unexplained_orders_deltas == other.unexplained_orders_deltas 
            and self.explained_orders_deltas == other.explained_orders_deltas
        ):
            # same deltas: not more probable
            return False
        if len(self.explained_orders_deltas) > len(other.explained_orders_deltas):
            # self has more explained orders deltas: it is more probable
            return True
        if len(self.explained_orders_deltas) < len(other.explained_orders_deltas):
            # self has less explained orders deltas: it is less probable
            return False
        # self is more probable if it has less unexplained orders deltas
        return len(self.unexplained_orders_deltas) < len(other.unexplained_orders_deltas)


    def has_inferred_orders(self) -> bool:
        return bool(self.inferred_filled_orders or self.inferred_cancelled_orders)

    def merge_order_deltas(self, other: 'ResolvedOrdersPortoflioDelta') -> 'ResolvedOrdersPortoflioDelta':
        return ResolvedOrdersPortoflioDelta(
            explained_orders_deltas=_merge_deltas(
                self.explained_orders_deltas, other.explained_orders_deltas
            ),
            unexplained_orders_deltas=_merge_deltas(
                self.unexplained_orders_deltas, other.unexplained_orders_deltas
            ),
            inferred_filled_orders=self.inferred_filled_orders,
            inferred_cancelled_orders=self.inferred_cancelled_orders,
        )


def _merge_deltas(
    deltas_a: dict[str, dict[str, decimal.Decimal]], deltas_b: dict[str, dict[str, decimal.Decimal]]
) -> dict[str, dict[str, decimal.Decimal]]:
    merged = {
        asset_name: _merge_delta_values(deltas_a, deltas_b, asset_name)
        for asset_name in set(deltas_a).union(set(deltas_b))
    }
    # remove empty deltas
    merged = {
        asset_name: deltas
        for asset_name, deltas in merged.items()
        if any(value != constants.ZERO for value in deltas.values())
    }
    return merged


def _merge_delta_values(
    deltas_a: dict[str, dict[str, decimal.Decimal]], deltas_b: dict[str, dict[str, decimal.Decimal]], asset_name: str
) -> dict[str, decimal.Decimal]:
    if asset_name in deltas_a and asset_name in deltas_b:
        return {
            key: deltas_a[asset_name][key] + deltas_b[asset_name][key]
            for key in deltas_a[asset_name]
        }
    if asset_name in deltas_a:
        return deltas_a[asset_name]
    return deltas_b[asset_name]
