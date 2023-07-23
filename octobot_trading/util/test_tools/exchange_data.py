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


@dataclasses.dataclass
class ExchangeAuthDetails:
    api_key: str = ""
    api_secret: str = ""
    api_password: str = ""
    exchange_type: str = ""
    sandboxed: bool = False
    encrypted: str = ""


@dataclasses.dataclass
class ExchangeDetails:
    name: str = ""


@dataclasses.dataclass
class MarketDetails:
    id: str
    symbol: str
    info: dict
    time_frame: str
    close: list[float]
    open: list[float]
    high: list[float]
    low: list[float]
    volume: list[float]
    time: list[float]


@dataclasses.dataclass
class OrdersDetails:
    open_orders: list[dict] = None
    missing_orders: list[dict] = None

    def __post_init__(self):
        if self.open_orders is None:
            self.open_orders = []
        if self.missing_orders is None:
            self.missing_orders = []


@dataclasses.dataclass
class PortfolioDetails:
    initial_value: float = 0
    content: dict = None
    asset_values: dict = None

    def __post_init__(self):
        if self.content is None:
            self.content = {}
        if self.asset_values is None:
            self.asset_values = {}


@dataclasses.dataclass
class ExchangeData(minimizable_dataclass.MinimizableDataclass):
    auth_details: ExchangeAuthDetails
    exchange_details: ExchangeDetails
    markets: list[MarketDetails] = None
    portfolio_details: PortfolioDetails = None
    orders_details: OrdersDetails = None
    trades: list[dict] = None

    # pylint: disable=E1134
    def __post_init__(self):
        if isinstance(self.auth_details, dict):
            self.auth_details = ExchangeAuthDetails(**self.auth_details)
        if isinstance(self.exchange_details, dict):
            self.exchange_details = ExchangeDetails(**self.exchange_details)
        if self.markets is None:
            self.markets = []
        elif self.markets and isinstance(self.markets[0], dict):
            self.markets = [MarketDetails(**market) for market in self.markets] if self.markets else []
        if not isinstance(self.portfolio_details, PortfolioDetails):
            self.portfolio_details = PortfolioDetails(**self.portfolio_details) if \
                self.portfolio_details else PortfolioDetails()
        if not isinstance(self.orders_details, OrdersDetails):
            self.orders_details = OrdersDetails(**self.orders_details) if self.orders_details else OrdersDetails()
        if self.trades is None:
            self.trades = []

    def get_price(self, symbol):
        for market in self.markets:
            if market.symbol == symbol:
                return market.close[-1]
        raise KeyError(symbol)
