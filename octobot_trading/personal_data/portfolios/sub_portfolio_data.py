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
import dataclasses
import decimal
import typing

import octobot_commons.logging as commons_logging
import octobot_commons.constants as commons_constants
import octobot_trading.personal_data as personal_data
import octobot_trading.constants as constants


@dataclasses.dataclass
class SubPortfolioData:
    bot_id: typing.Optional[str]
    portfolio_id: typing.Optional[str]
    priority_key: float
    content: dict[str, dict[str, decimal.Decimal]]  # current content of the sub-portfolio
    unit: typing.Optional[str]
    # deltas to be applied on top of the current content of the sub-portfolio from get_content_after_deltas()
    funds_deltas: dict[str, dict[str, decimal.Decimal]] = dataclasses.field(default_factory=dict)
    # funds that are missing from this portfolio. Populated after portfolio has been resolved
    missing_funds: dict[str, decimal.Decimal] = dataclasses.field(default_factory=dict)

    # funds that are locked (maybe in orders) from this portfolio
    locked_funds_by_asset: dict[str, decimal.Decimal] = dataclasses.field(default_factory=dict)


    def get_content_after_deltas(self) -> dict[str, dict[str, decimal.Decimal]]:
        """
        Computes the updated portfolio from delta available and total
        """
        updated_content = copy.deepcopy(self.content)
        for asset, delta_values in self.funds_deltas.items():
            if asset in updated_content:
                updated_content[asset][commons_constants.PORTFOLIO_TOTAL] += (
                    delta_values[commons_constants.PORTFOLIO_TOTAL]
                )
                updated_content[asset][commons_constants.PORTFOLIO_AVAILABLE] += (
                    delta_values[commons_constants.PORTFOLIO_AVAILABLE]
                )
            else:
                updated_content[asset] = {
                    commons_constants.PORTFOLIO_TOTAL: delta_values[commons_constants.PORTFOLIO_TOTAL],
                    commons_constants.PORTFOLIO_AVAILABLE: delta_values[commons_constants.PORTFOLIO_AVAILABLE],
                }
            for key in (commons_constants.PORTFOLIO_TOTAL, commons_constants.PORTFOLIO_AVAILABLE):
                if updated_content[asset][key] < constants.ZERO:
                    commons_logging.get_logger(__name__).warning(
                        f"{asset} portfolio {key} value: {updated_content[asset][key]} is < 0. Replacing with zero."
                    )
                    updated_content[asset][key] = constants.ZERO
        return updated_content

    def get_content_from_total_deltas_and_locked_funds(self) -> dict[str, dict[str, decimal.Decimal]]:
        """
        Only uses PORTFOLIO_TOTAL deltas and computes available values from locked_funds_by_asset
        """
        updated_content = copy.deepcopy(self.content)
        for asset, delta_values in self.funds_deltas.items():
            if asset in updated_content:
                updated_content[asset][commons_constants.PORTFOLIO_TOTAL] += (
                    delta_values[commons_constants.PORTFOLIO_TOTAL]
                )
            else:
                updated_content[asset] = {
                    commons_constants.PORTFOLIO_TOTAL: delta_values[commons_constants.PORTFOLIO_TOTAL]
                }
        for asset, values in updated_content.items():
            locked_funds = self.locked_funds_by_asset.get(asset, constants.ZERO)
            if locked_funds > values[commons_constants.PORTFOLIO_TOTAL]:
                commons_logging.get_logger(__name__).error(
                    f"Unexpected: negative {asset} available value after applying {locked_funds} locked funds to {values}"
                )
            values[commons_constants.PORTFOLIO_AVAILABLE] = values[commons_constants.PORTFOLIO_TOTAL] - locked_funds
        return updated_content

    def is_similar_to(self, other) -> bool:
        return (
            other
            and personal_data.filter_empty_values(self.content) == personal_data.filter_empty_values(other.content)
        )
