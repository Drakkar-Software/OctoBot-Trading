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
import typing

import octobot_commons.dataclasses
import octobot_trading.exchanges


@dataclasses.dataclass
class IncompatibleAssetDetails(
    octobot_commons.dataclasses.FlexibleDataclass, octobot_commons.dataclasses.UpdatableDataclass
):
    symbol: str = ""
    updated_at: float = 0


@dataclasses.dataclass
class ExchangeAuthDetails(octobot_commons.dataclasses.FlexibleDataclass, octobot_commons.dataclasses.UpdatableDataclass):
    api_key: str = ""
    api_secret: str = ""
    api_password: str = ""
    access_token: str = ""
    exchange_type: str = ""
    sandboxed: bool = False
    broker_enabled: bool = False
    encrypted: str = ""
    exchange_account_id: typing.Union[str, None] = None
    incompatible_assets: typing.Union[list[IncompatibleAssetDetails], None] = dataclasses.field(default_factory=list)

    # pylint: disable=E1134
    def __post_init__(self):
        if self.incompatible_assets and isinstance(self.incompatible_assets[0], dict):
            self.incompatible_assets = (
                [IncompatibleAssetDetails.from_dict(asset) for asset in self.incompatible_assets]
                if self.incompatible_assets else []
            )


@dataclasses.dataclass
class ExchangeDetails(octobot_commons.dataclasses.FlexibleDataclass, octobot_commons.dataclasses.UpdatableDataclass):
    name: str = ""


@dataclasses.dataclass
class MarketDetails(octobot_commons.dataclasses.FlexibleDataclass, octobot_commons.dataclasses.UpdatableDataclass):
    id: str = ""
    symbol: str = ""
    details: octobot_trading.exchanges.SymbolDetails = \
        dataclasses.field(default_factory=octobot_trading.exchanges.SymbolDetails)
    time_frame: str = ""
    close: list[float] = dataclasses.field(default_factory=list)
    open: list[float] = dataclasses.field(default_factory=list)
    high: list[float] = dataclasses.field(default_factory=list)
    low: list[float] = dataclasses.field(default_factory=list)
    volume: list[float] = dataclasses.field(default_factory=list)
    time: list[float] = dataclasses.field(default_factory=list)

    def has_full_candles(self):
        return self.close and self.open and self.high and self.low and self.time


@dataclasses.dataclass
class OrdersDetails(octobot_commons.dataclasses.FlexibleDataclass, octobot_commons.dataclasses.UpdatableDataclass):
    open_orders: list[dict] = dataclasses.field(default_factory=list)
    missing_orders: list[dict] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class PortfolioDetails(octobot_commons.dataclasses.FlexibleDataclass, octobot_commons.dataclasses.UpdatableDataclass):
    initial_value: float = 0
    content: dict = dataclasses.field(default_factory=dict)
    asset_values: dict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class ExchangeData(octobot_commons.dataclasses.MinimizableDataclass, octobot_commons.dataclasses.UpdatableDataclass):
    auth_details: ExchangeAuthDetails = dataclasses.field(default_factory=ExchangeAuthDetails)
    exchange_details: ExchangeDetails = dataclasses.field(default_factory=ExchangeDetails)
    markets: list[MarketDetails] = dataclasses.field(default_factory=list)
    portfolio_details: PortfolioDetails = dataclasses.field(default_factory=PortfolioDetails)
    orders_details: OrdersDetails = dataclasses.field(default_factory=OrdersDetails)
    trades: list[dict] = dataclasses.field(default_factory=list)

    # pylint: disable=E1134
    def __post_init__(self):
        if self.markets and isinstance(self.markets[0], dict):
            self.markets = [MarketDetails.from_dict(market) for market in self.markets] if self.markets else []

    def get_price(self, symbol):
        for market in self.markets:
            if market.symbol == symbol:
                return market.close[-1]
        raise KeyError(symbol)
