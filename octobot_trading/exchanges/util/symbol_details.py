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


import octobot_commons.updatable_dataclass as updatable_dataclass


@dataclasses.dataclass
class CCXTDetails(updatable_dataclass.UpdatableDataclass):
    info: dict = dataclasses.field(default_factory=dict)
    parsed: dict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class SymbolDetails(updatable_dataclass.UpdatableDataclass):
    ccxt: CCXTDetails = CCXTDetails()

    # pylint: disable=E1134
    def __post_init__(self):
        if not isinstance(self.ccxt, CCXTDetails):
            self.ccxt = CCXTDetails(**self.ccxt) if self.ccxt else CCXTDetails()
