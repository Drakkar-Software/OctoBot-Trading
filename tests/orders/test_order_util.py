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
from octobot_trading.enums import ExchangeConstantsMarketStatusColumns as Ecmsc
from octobot_trading.orders.order_util import get_min_max_amounts


def test_get_min_max_amounts():
    # normal values
    symbol_market = {
        Ecmsc.LIMITS.value: {
            Ecmsc.LIMITS_AMOUNT.value: {
                Ecmsc.LIMITS_AMOUNT_MIN.value: 0.5,
                Ecmsc.LIMITS_AMOUNT_MAX.value: 100,
            },
            Ecmsc.LIMITS_COST.value: {
                Ecmsc.LIMITS_COST_MIN.value: None,
                Ecmsc.LIMITS_COST_MAX.value: None
            },
            Ecmsc.LIMITS_PRICE.value: {
                Ecmsc.LIMITS_PRICE_MIN.value: 0.5,
                Ecmsc.LIMITS_PRICE_MAX.value: 50
            },
        }
    }
    min_quantity, max_quantity, min_cost, max_cost, min_price, max_price = get_min_max_amounts(symbol_market)
    assert min_quantity == 0.5
    assert max_quantity == 100
    assert min_cost is None
    assert max_cost is None
    assert min_price == 0.5
    assert max_price == 50

    # missing all values
    min_quantity, max_quantity, min_cost, max_cost, min_price, max_price = get_min_max_amounts({})
    assert min_quantity is None
    assert max_quantity is None
    assert min_cost is None
    assert max_cost is None
    assert min_price is None
    assert max_price is None

    # missing all values: asign default
    min_quantity, max_quantity, min_cost, max_cost, min_price, max_price = get_min_max_amounts({}, "xyz")
    assert min_quantity == "xyz"
    assert max_quantity == "xyz"
    assert min_cost == "xyz"
    assert max_cost == "xyz"
    assert min_price == "xyz"
    assert max_price == "xyz"

    # missing values: assign default

    symbol_market = {
        Ecmsc.LIMITS.value: {
            Ecmsc.LIMITS_AMOUNT.value: {
                Ecmsc.LIMITS_AMOUNT_MIN.value: 0.5,
                Ecmsc.LIMITS_AMOUNT_MAX.value: 100,
            },
            Ecmsc.LIMITS_COST.value: {
                Ecmsc.LIMITS_COST_MIN.value: None,
                Ecmsc.LIMITS_COST_MAX.value: None
            }
        }
    }
    min_quantity, max_quantity, min_cost, max_cost, min_price, max_price = get_min_max_amounts(symbol_market, "xyz")
    assert min_quantity == 0.5
    assert max_quantity == 100
    assert min_cost == "xyz"  # None is not a valid value => assign default
    assert max_cost == "xyz"  # None is not a valid value => assign default
    assert min_price == "xyz"
    assert max_price == "xyz"