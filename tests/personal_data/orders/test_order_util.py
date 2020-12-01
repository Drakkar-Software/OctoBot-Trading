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
import octobot_trading.enums as enums
import octobot_trading.personal_data as personal_data


def test_get_min_max_amounts():
    # normal values
    symbol_market = {
        enums.ExchangeConstantsMarketStatusColumns.LIMITS.value: {
            enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT_MIN.value: 0.5,
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT_MAX.value: 100,
            },
            enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST_MIN.value: None,
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST_MAX.value: None
            },
            enums.ExchangeConstantsMarketStatusColumns.LIMITS_PRICE.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_PRICE_MIN.value: 0.5,
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_PRICE_MAX.value: 50
            },
        }
    }
    min_quantity, max_quantity, min_cost, max_cost, min_price, max_price = personal_data.get_min_max_amounts(
        symbol_market)
    assert min_quantity == 0.5
    assert max_quantity == 100
    assert min_cost is None
    assert max_cost is None
    assert min_price == 0.5
    assert max_price == 50

    # missing all values
    min_quantity, max_quantity, min_cost, max_cost, min_price, max_price = personal_data.get_min_max_amounts({})
    assert min_quantity is None
    assert max_quantity is None
    assert min_cost is None
    assert max_cost is None
    assert min_price is None
    assert max_price is None

    # missing all values: asign default
    min_quantity, max_quantity, min_cost, max_cost, min_price, max_price = personal_data.get_min_max_amounts({}, "xyz")
    assert min_quantity == "xyz"
    assert max_quantity == "xyz"
    assert min_cost == "xyz"
    assert max_cost == "xyz"
    assert min_price == "xyz"
    assert max_price == "xyz"

    # missing values: assign default

    symbol_market = {
        enums.ExchangeConstantsMarketStatusColumns.LIMITS.value: {
            enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT_MIN.value: 0.5,
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT_MAX.value: 100,
            },
            enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST_MIN.value: None,
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST_MAX.value: None
            }
        }
    }
    min_quantity, max_quantity, min_cost, max_cost, min_price, max_price = personal_data.get_min_max_amounts(symbol_market, "xyz")
    assert min_quantity == 0.5
    assert max_quantity == 100
    assert min_cost == "xyz"  # None is not a valid value => assign default
    assert max_cost == "xyz"  # None is not a valid value => assign default
    assert min_price == "xyz"
    assert max_price == "xyz"


def test_get_fees_for_currency():
    fee1 = {
        enums.FeePropertyColumns.CURRENCY.value: "BTC",
        enums.FeePropertyColumns.COST.value: 1
    }
    assert personal_data.get_fees_for_currency(fee1, "BTC") == 1
    assert personal_data.get_fees_for_currency(fee1, "BTC1") == 0

    fee2 = {
        enums.FeePropertyColumns.CURRENCY.value: "BTC",
        enums.FeePropertyColumns.COST.value: 0
    }
    assert personal_data.get_fees_for_currency(fee2, "BTC") == 0
    assert personal_data.get_fees_for_currency(fee2, "BTC1") == 0

    assert personal_data.get_fees_for_currency({}, "BTC") == 0
    assert personal_data.get_fees_for_currency(None, "BTC") == 0
