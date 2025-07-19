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

import octobot_commons.logging as commons_logging
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

    def is_fully_explained(self) -> bool:
        # explained delta & no unexplained delta: this is the most probable combination: stop here
        return bool(self.explained_orders_deltas and not self.unexplained_orders_deltas)

    def adds_explanations(self) -> bool:
        return bool(self.explained_orders_deltas)

    def merge_order_deltas(self, other: 'ResolvedOrdersPortoflioDelta', reference_deltas: dict[str, dict[str, decimal.Decimal]]) -> 'ResolvedOrdersPortoflioDelta':
        merged_explained_deltas = _merge_deltas(self.explained_orders_deltas, other.explained_orders_deltas, cumulate_deltas=True)
        remaining_unexplained_deltas = _compute_unexplained_deltas_from_explained_deltas(
            reference_deltas, merged_explained_deltas
        )
        return ResolvedOrdersPortoflioDelta(
            explained_orders_deltas=merged_explained_deltas,
            unexplained_orders_deltas=remaining_unexplained_deltas,
            inferred_filled_orders=self.inferred_filled_orders,
            inferred_cancelled_orders=self.inferred_cancelled_orders,
        )

    def ensure_max_delta_and_clear_partial_deltas(self, reference_deltas: dict[str, dict[str, decimal.Decimal]]):
        _ensure_maximum_deltas(self.explained_orders_deltas, reference_deltas)
        self.unexplained_orders_deltas = _compute_unexplained_deltas_from_explained_deltas(
            self.explained_orders_deltas, reference_deltas
        )
        # remove explained deltas that are also in unexplained deltas
        for asset_name in self.explained_orders_deltas:
            if asset_name in self.unexplained_orders_deltas:
                commons_logging.get_logger("ResolvedOrdersPortoflioDelta").info(
                    f"Ignoring {asset_name} unexplained delta {self.unexplained_orders_deltas[asset_name]} as it is partially explained by order deltas as {self.explained_orders_deltas[asset_name]}."
                )
                self.unexplained_orders_deltas.pop(asset_name)


def _merge_deltas(
    deltas_a: dict[str, dict[str, decimal.Decimal]], deltas_b: dict[str, dict[str, decimal.Decimal]], cumulate_deltas: bool
) -> dict[str, dict[str, decimal.Decimal]]:
    merged = {
        asset_name: _merge_delta_values(deltas_a, deltas_b, asset_name, cumulate_deltas)
        for asset_name in set(deltas_a).union(set(deltas_b))
    }
    # remove empty deltas
    return _filter_empty_deltas(merged)


def _compute_unexplained_deltas_from_explained_deltas(
    explained_deltas: dict[str, dict[str, decimal.Decimal]],
    reference_deltas: dict[str, dict[str, decimal.Decimal]],
) -> dict[str, dict[str, decimal.Decimal]]:
    return _merge_deltas(reference_deltas, explained_deltas, cumulate_deltas=False)


def _ensure_maximum_deltas(
    deltas: dict[str, dict[str, decimal.Decimal]],
    reference_deltas: dict[str, dict[str, decimal.Decimal]],
):
    for asset_name, values in deltas.items():
        if asset_name in reference_deltas:
            for key, value in values.items():
                if abs(value) > abs(reference_deltas[asset_name][key]):
                    # value can't be higher than reference delta: align it to reference delta
                    commons_logging.get_logger("ResolvedOrdersPortoflioDelta").warning(
                        f"Asset {asset_name} {key} order delta is higher than reference delta: {reference_deltas[asset_name][key]}. Aligning it to reference delta ({values=})."
                    )
                    deltas[asset_name][key] = reference_deltas[asset_name][key]
        else:
            commons_logging.get_logger("ResolvedOrdersPortoflioDelta").error(
                f"Asset {asset_name} is not in reference deltas: {reference_deltas}. Removing it from deltas ({values=})."
            )
            del deltas[asset_name]


def _filter_empty_deltas(deltas: dict[str, dict[str, decimal.Decimal]]) -> dict[str, dict[str, decimal.Decimal]]:
    return {
        asset_name: deltas
        for asset_name, deltas in deltas.items()
        if any(value != constants.ZERO for value in deltas.values())
    }


def _merge_delta_values(
    deltas_a: dict[str, dict[str, decimal.Decimal]], 
    deltas_b: dict[str, dict[str, decimal.Decimal]], 
    asset_name: str, 
    cumulate_deltas: bool
) -> dict[str, decimal.Decimal]:
    if asset_name in deltas_a and asset_name in deltas_b:
        return {
            key: deltas_a[asset_name][key] + (deltas_b[asset_name][key] if cumulate_deltas else -deltas_b[asset_name][key])
            for key in deltas_a[asset_name]
        }
    if asset_name in deltas_a:
        return deltas_a[asset_name]
    if cumulate_deltas:
        return deltas_b[asset_name]
    return {
        key: -deltas_b[asset_name][key]
        for key in deltas_b[asset_name]
    }
