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


import octobot_commons.minimizable_dataclass as minimizable_dataclass
import octobot_commons.updatable_dataclass as updatable_dataclass


@dataclasses.dataclass
class ExchangeAuthDetails(updatable_dataclass.UpdatableDataclass):
    api_key: str = ""
    api_secret: str = ""
    api_password: str = ""
    exchange_type: str = ""
    sandboxed: bool = False
    encrypted: str = ""


@dataclasses.dataclass
class ExchangeDetails(updatable_dataclass.UpdatableDataclass):
    name: str = ""


@dataclasses.dataclass
class MarketDetails(updatable_dataclass.UpdatableDataclass):
    id: str = ""
    symbol: str = ""
    info: dict = dataclasses.field(default_factory=dict)
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
class OrdersDetails(updatable_dataclass.UpdatableDataclass):
    open_orders: list[dict] = dataclasses.field(default_factory=list)
    missing_orders: list[dict] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class PortfolioDetails(updatable_dataclass.UpdatableDataclass):
    initial_value: float = 0
    content: dict = dataclasses.field(default_factory=dict)
    asset_values: dict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class ExchangeData(minimizable_dataclass.MinimizableDataclass, updatable_dataclass.UpdatableDataclass):
    auth_details: ExchangeAuthDetails = None
    exchange_details: ExchangeDetails = None
    markets: list[MarketDetails] = dataclasses.field(default_factory=list)
    portfolio_details: PortfolioDetails = None
    orders_details: OrdersDetails = None
    trades: list[dict] = dataclasses.field(default_factory=list)

    # pylint: disable=E1134
    def __post_init__(self):
        if not isinstance(self.auth_details, ExchangeAuthDetails):
            self.auth_details = ExchangeAuthDetails(**self.auth_details) if \
                self.auth_details else ExchangeAuthDetails()
        if not isinstance(self.exchange_details, ExchangeDetails):
            self.exchange_details = ExchangeDetails(**self.exchange_details) if \
                self.exchange_details else ExchangeDetails()
        if self.markets and isinstance(self.markets[0], dict):
            self.markets = [MarketDetails(**market) for market in self.markets] if self.markets else []
        if not isinstance(self.portfolio_details, PortfolioDetails):
            self.portfolio_details = PortfolioDetails(**self.portfolio_details) if \
                self.portfolio_details else PortfolioDetails()
        if not isinstance(self.orders_details, OrdersDetails):
            self.orders_details = OrdersDetails(**self.orders_details) if self.orders_details else OrdersDetails()

    def get_price(self, symbol):
        for market in self.markets:
            if market.symbol == symbol:
                return market.close[-1]
        raise KeyError(symbol)
