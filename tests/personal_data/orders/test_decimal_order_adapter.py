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
import math
import pytest
import decimal

from octobot_trading.enums import ExchangeConstantsMarketStatusColumns as Ecmsc
import octobot_trading.personal_data as personal_data
from tests import event_loop

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_decimal_adapt_price():
    # will use symbol market
    symbol_market = {Ecmsc.PRECISION.value: {Ecmsc.PRECISION_PRICE.value: 4}}
    assert personal_data.decimal_adapt_price(symbol_market, decimal.Decimal(str(0.0001))) == decimal.Decimal(
        str(0.0001))
    assert personal_data.decimal_adapt_price(symbol_market, decimal.Decimal(str(0.00015))) == decimal.Decimal(
        str(0.0001))
    assert personal_data.decimal_adapt_price(symbol_market, decimal.Decimal(str(0.005))) == decimal.Decimal(str(0.005))
    assert personal_data.decimal_adapt_price(symbol_market, decimal.Decimal(str(1))) == decimal.Decimal(str(1))

    assert personal_data.decimal_adapt_price(symbol_market, decimal.Decimal(str(56.5128597145))) == decimal.Decimal(
        str(56.5128))
    assert personal_data.decimal_adapt_price(symbol_market,
                                             decimal.Decimal(str(1251.0000014576121234854513))) == decimal.Decimal(
        str(1251.0000))

    # will use default (CURRENCY_DEFAULT_MAX_PRICE_DIGITS)
    symbol_market = {Ecmsc.PRECISION.value: {}}
    assert personal_data.decimal_adapt_price(symbol_market, decimal.Decimal(str(0.0001))) == decimal.Decimal(
        str(0.0001))
    assert personal_data.decimal_adapt_price(symbol_market, decimal.Decimal(str(0.00015))) == decimal.Decimal(
        str(0.00015))
    assert personal_data.decimal_adapt_price(symbol_market, decimal.Decimal(str(0.005))) == decimal.Decimal(str(0.005))
    assert personal_data.decimal_adapt_price(symbol_market, decimal.Decimal(str(1))) == decimal.Decimal(
        str(1.0000000000000000000000001))
    assert personal_data.decimal_adapt_price(symbol_market, decimal.Decimal(str(1))) == decimal.Decimal(str(1))

    assert personal_data.decimal_adapt_price(symbol_market, decimal.Decimal(str(56.5128597145))) == decimal.Decimal(
        str(56.51285971))
    assert personal_data.decimal_adapt_price(symbol_market,
                                             decimal.Decimal(str(1251.0000014576121234854513))) == decimal.Decimal(
        str(1251.00000145))
    assert personal_data.decimal_adapt_price(symbol_market,
                                             decimal.Decimal(str(1251.0000014576121234854513)),
                                             True) == decimal.Decimal(
        str(1251.00000145))
    assert personal_data.decimal_adapt_price(symbol_market,
                                             decimal.Decimal(str(1251.0000014576121234854513)),
                                             False) == decimal.Decimal(
        str(1251.00000146))
    assert personal_data.decimal_adapt_price(symbol_market,
                                             decimal.Decimal(str(1251.000001451)),
                                             True) == decimal.Decimal(
        str(1251.00000145))
    assert personal_data.decimal_adapt_price(symbol_market,
                                             decimal.Decimal(str(1251.000001451)),
                                             False) == decimal.Decimal(
        str(1251.00000146))


async def test_decimal_check_and_adapt_order_details_if_necessary():
    symbol_market = {
        Ecmsc.LIMITS.value: {
            Ecmsc.LIMITS_AMOUNT.value: {
                Ecmsc.LIMITS_AMOUNT_MIN.value: 0.5,
                Ecmsc.LIMITS_AMOUNT_MAX.value: 100,
            },
            Ecmsc.LIMITS_COST.value: {
                Ecmsc.LIMITS_COST_MIN.value: 1,
                Ecmsc.LIMITS_COST_MAX.value: 200
            },
            Ecmsc.LIMITS_PRICE.value: {
                Ecmsc.LIMITS_PRICE_MIN.value: 0.5,
                Ecmsc.LIMITS_PRICE_MAX.value: 50
            },
        },
        Ecmsc.PRECISION.value: {
            Ecmsc.PRECISION_PRICE.value: 8,
            Ecmsc.PRECISION_AMOUNT.value: 8
        }
    }

    invalid_cost_symbol_market = {
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
        },
        Ecmsc.PRECISION.value: {
            Ecmsc.PRECISION_PRICE.value: 8,
            Ecmsc.PRECISION_AMOUNT.value: 8
        }
    }

    # correct min
    quantity = decimal.Decimal(str(0.5))
    price = decimal.Decimal(str(2))
    assert personal_data.decimal_check_and_adapt_order_details_if_necessary(quantity, price, symbol_market) == [
        (quantity, price)]

    # correct max
    quantity = decimal.Decimal(str(100))
    price = decimal.Decimal(str(2))
    assert personal_data.decimal_check_and_adapt_order_details_if_necessary(quantity, price, symbol_market) == [
        (quantity, price)]

    # correct
    quantity = decimal.Decimal(str(10))
    price = decimal.Decimal(str(0.6))
    assert personal_data.decimal_check_and_adapt_order_details_if_necessary(quantity, price, symbol_market) == [
        (quantity, price)]

    # correct
    quantity = decimal.Decimal(str(3))
    price = decimal.Decimal(str(49.9))
    assert personal_data.decimal_check_and_adapt_order_details_if_necessary(quantity, price, symbol_market) == [
        (quantity, price)]

    # invalid price > but valid cost
    quantity = decimal.Decimal(str(1))
    price = decimal.Decimal(str(100))
    assert personal_data.decimal_check_and_adapt_order_details_if_necessary(quantity, price, symbol_market) == [
        (quantity, price)]

    # invalid price < but valid cost
    quantity = decimal.Decimal(str(10))
    price = decimal.Decimal(str(0.1))
    assert personal_data.decimal_check_and_adapt_order_details_if_necessary(quantity, price, symbol_market) == [
        (quantity, price)]

    # invalid price > and invalid cost from exchange => use price => invalid
    quantity = decimal.Decimal(str(1))
    price = decimal.Decimal(str(100))
    assert personal_data.decimal_check_and_adapt_order_details_if_necessary(quantity, price,
                                                                            invalid_cost_symbol_market) == []

    # invalid price < and invalid cost from exchange => use price => invalid
    quantity = decimal.Decimal(str(1))
    price = decimal.Decimal(str(0.1))
    assert personal_data.decimal_check_and_adapt_order_details_if_necessary(quantity, price,
                                                                            invalid_cost_symbol_market) == []

    # invalid cost <
    quantity = decimal.Decimal(str(0.5))
    price = decimal.Decimal(str(1))
    assert personal_data.decimal_check_and_adapt_order_details_if_necessary(quantity, price, symbol_market) == []

    # invalid cost >
    quantity = decimal.Decimal(str(10))
    price = decimal.Decimal(str(49))
    assert personal_data.decimal_check_and_adapt_order_details_if_necessary(quantity, price, symbol_market) == [
        (decimal.Decimal(str(1.83673469)), decimal.Decimal(str(49))),
        (decimal.Decimal(str(4.08163265)), decimal.Decimal(str(49))),
        (decimal.Decimal(str(4.08163265)), decimal.Decimal(str(49)))]

    # high cost but no max cost => valid
    quantity = decimal.Decimal(str(10))
    price = decimal.Decimal(str(49))
    assert personal_data.decimal_check_and_adapt_order_details_if_necessary(quantity, price, symbol_market) == [
        (decimal.Decimal(str(1.83673469)), decimal.Decimal(str(49))),
        (decimal.Decimal(str(4.08163265)), decimal.Decimal(str(49))),
        (decimal.Decimal(str(4.08163265)), decimal.Decimal(str(49)))]

    # invalid cost with invalid price >=
    quantity = decimal.Decimal(str(10))
    price = decimal.Decimal(str(50))
    assert personal_data.decimal_check_and_adapt_order_details_if_necessary(quantity, price, symbol_market) == [
        (decimal.Decimal(str(2)), decimal.Decimal(str(50))), (decimal.Decimal(str(4)), decimal.Decimal(str(50))),
        (decimal.Decimal(str(4)), decimal.Decimal(str(50)))]

    # invalid cost with invalid price > and invalid cost from exchange => use price => invalid
    quantity = decimal.Decimal(str(10))
    price = decimal.Decimal(str(51))
    assert personal_data.decimal_check_and_adapt_order_details_if_necessary(quantity, price,
                                                                            invalid_cost_symbol_market) == []

    # invalid amount >
    quantity = decimal.Decimal(str(200))
    price = decimal.Decimal(str(5))
    assert personal_data.decimal_check_and_adapt_order_details_if_necessary(quantity, price, symbol_market) == [
        (decimal.Decimal(str(40.0)), decimal.Decimal(str(5))), (decimal.Decimal(str(40.0)), decimal.Decimal(str(5))),
        (decimal.Decimal(str(40.0)), decimal.Decimal(str(5))), (decimal.Decimal(str(40.0)), decimal.Decimal(str(5))),
        (decimal.Decimal(str(40.0)), decimal.Decimal(str(5)))]

    # invalid amount <
    quantity = decimal.Decimal(str(0.4))
    price = decimal.Decimal(str(5))
    assert personal_data.decimal_check_and_adapt_order_details_if_necessary(quantity, price, symbol_market) == []

    symbol_market = {
        Ecmsc.LIMITS.value: {
            Ecmsc.LIMITS_AMOUNT.value: {
                Ecmsc.LIMITS_AMOUNT_MIN.value: 0.0000005,
                Ecmsc.LIMITS_AMOUNT_MAX.value: 100,
            },
            Ecmsc.LIMITS_COST.value: {
                Ecmsc.LIMITS_COST_MIN.value: 0.00000001,
                Ecmsc.LIMITS_COST_MAX.value: 10
            },
            Ecmsc.LIMITS_PRICE.value: {
                Ecmsc.LIMITS_PRICE_MIN.value: 0.000005,
                Ecmsc.LIMITS_PRICE_MAX.value: 50
            },
        },
        Ecmsc.PRECISION.value: {
            Ecmsc.PRECISION_PRICE.value: 8,
            Ecmsc.PRECISION_AMOUNT.value: 8
        }
    }

    # correct quantity
    # to test _adapt_order_quantity_because_quantity
    quantity = decimal.Decimal(str(5000))
    price = decimal.Decimal(str(0.001))
    expected = [(decimal.Decimal(str(100.0)), decimal.Decimal(str(0.001)))] * 50
    assert personal_data.decimal_check_and_adapt_order_details_if_necessary(quantity, price, symbol_market) == expected

    # price = 0 => no order
    quantity = decimal.Decimal(str(10))
    price = decimal.Decimal(str(0))
    assert personal_data.decimal_check_and_adapt_order_details_if_necessary(quantity, price, symbol_market) == []

    symbol_market_without_max = {
        Ecmsc.LIMITS.value: {
            Ecmsc.LIMITS_AMOUNT.value: {
                Ecmsc.LIMITS_AMOUNT_MIN.value: 0.0000005,
                Ecmsc.LIMITS_AMOUNT_MAX.value: None,
            },
            Ecmsc.LIMITS_COST.value: {
                Ecmsc.LIMITS_COST_MIN.value: 0.00000001,
                Ecmsc.LIMITS_COST_MAX.value: None
            },
            Ecmsc.LIMITS_PRICE.value: {
                Ecmsc.LIMITS_PRICE_MIN.value: 0.000005,
                Ecmsc.LIMITS_PRICE_MAX.value: None
            },
        },
        Ecmsc.PRECISION.value: {
            Ecmsc.PRECISION_PRICE.value: 8,
            Ecmsc.PRECISION_AMOUNT.value: 8
        }
    }

    # high cost but no max cost => no split
    quantity = decimal.Decimal(str(10))
    price = decimal.Decimal(str(49))
    assert personal_data.decimal_check_and_adapt_order_details_if_necessary(quantity, price,
                                                                            symbol_market_without_max) == [
               (decimal.Decimal(str(10)), decimal.Decimal(str(49)))]

    # high quantity but no max quantity => no split
    quantity = decimal.Decimal(str(10000000))
    price = decimal.Decimal(str(49))
    assert personal_data.decimal_check_and_adapt_order_details_if_necessary(quantity, price,
                                                                            symbol_market_without_max) == \
           [(decimal.Decimal(str(10000000)), decimal.Decimal(str(49)))]

    # high price but no max price => no split
    quantity = decimal.Decimal(str(10))
    price = decimal.Decimal(str(4900000))
    assert personal_data.decimal_check_and_adapt_order_details_if_necessary(quantity, price,
                                                                            symbol_market_without_max) == [
               (decimal.Decimal(str(10)), decimal.Decimal(str(4900000)))]


async def test_split_orders():
    symbol_market = {
        Ecmsc.LIMITS.value: {
            Ecmsc.LIMITS_AMOUNT.value: {
                Ecmsc.LIMITS_AMOUNT_MIN.value: 1,
                Ecmsc.LIMITS_AMOUNT_MAX.value: 100,
            },
            Ecmsc.LIMITS_COST.value: {
                Ecmsc.LIMITS_COST_MIN.value: 1,
                Ecmsc.LIMITS_COST_MAX.value: 30
            },
            Ecmsc.LIMITS_PRICE.value: {
                Ecmsc.LIMITS_PRICE_MIN.value: 0.001,
                Ecmsc.LIMITS_PRICE_MAX.value: 1000
            },
        },
        Ecmsc.PRECISION.value: {
            Ecmsc.PRECISION_PRICE.value: 1,
            Ecmsc.PRECISION_AMOUNT.value: 1
        }
    }

    symbol_market_without_max = {
        Ecmsc.LIMITS.value: {
            Ecmsc.LIMITS_AMOUNT.value: {
                Ecmsc.LIMITS_AMOUNT_MIN.value: 1,
                Ecmsc.LIMITS_AMOUNT_MAX.value: None,
            },
            Ecmsc.LIMITS_COST.value: {
                Ecmsc.LIMITS_COST_MIN.value: 1,
                Ecmsc.LIMITS_COST_MAX.value: None
            },
            Ecmsc.LIMITS_PRICE.value: {
                Ecmsc.LIMITS_PRICE_MIN.value: 1,
                Ecmsc.LIMITS_PRICE_MAX.value: None
            },
        },
        Ecmsc.PRECISION.value: {
            Ecmsc.PRECISION_PRICE.value: 1,
            Ecmsc.PRECISION_AMOUNT.value: 1
        }
    }
    max_cost = symbol_market[Ecmsc.LIMITS.value][Ecmsc.LIMITS_COST.value][Ecmsc.LIMITS_COST_MAX.value]
    max_quantity = symbol_market[Ecmsc.LIMITS.value][Ecmsc.LIMITS_AMOUNT.value][Ecmsc.LIMITS_AMOUNT_MAX.value]

    # normal situation, split because of cost
    total_price = decimal.Decimal(str(100))
    valid_quantity = decimal.Decimal(str(5))
    price = decimal.Decimal(str(20))
    assert personal_data.decimal_split_orders(total_price, max_cost, valid_quantity,
                                              max_quantity, price, valid_quantity, symbol_market) \
           == [(decimal.Decimal(str(0.5)), decimal.Decimal(str(20)))] + [
               (decimal.Decimal(str(1.5)), decimal.Decimal(str(20)))] * 3

    # normal situation, split because of quantity
    total_price = decimal.Decimal(str(5.0255))
    valid_quantity = decimal.Decimal(str(502.55))
    price = decimal.Decimal(str(0.01))
    assert personal_data.decimal_split_orders(total_price, max_cost, valid_quantity,
                                              max_quantity, price, valid_quantity, symbol_market) \
           == [(decimal.Decimal(str(2.5)), decimal.Decimal(str(0.01)))] + [
               (decimal.Decimal(str(100)), decimal.Decimal(str(0.01)))] * 5

    # missing info situation, split because of cost
    max_quantity = None
    total_price = decimal.Decimal(str(100))
    valid_quantity = decimal.Decimal(str(5))
    price = decimal.Decimal(str(20))
    assert personal_data.decimal_split_orders(total_price, max_cost, valid_quantity,
                                              max_quantity, price, valid_quantity, symbol_market_without_max) \
           == [(decimal.Decimal(str(0.5)), decimal.Decimal(str(20)))] + [
               (decimal.Decimal(str(1.5)), decimal.Decimal(str(20)))] * 3

    # missing info situation, split because of quantity
    max_quantity = symbol_market[Ecmsc.LIMITS.value][Ecmsc.LIMITS_AMOUNT.value][Ecmsc.LIMITS_AMOUNT_MAX.value]
    max_cost = None
    total_price = decimal.Decimal(str(5.0255))
    valid_quantity = decimal.Decimal(str(502.55))
    price = decimal.Decimal(str(0.01))
    assert personal_data.decimal_split_orders(total_price, max_cost, valid_quantity,
                                              max_quantity, price, valid_quantity, symbol_market_without_max) \
           == [(decimal.Decimal(str(2.5)), decimal.Decimal(str(0.01)))] + [
               (decimal.Decimal(str(100)), decimal.Decimal(str(0.01)))] * 5

    # missing info situation, can't split
    max_quantity = None
    max_cost = None
    total_price = decimal.Decimal(str(5.0255))
    valid_quantity = decimal.Decimal(str(502.55))
    price = decimal.Decimal(str(0.01))
    with pytest.raises(RuntimeError):
        assert personal_data.decimal_split_orders(total_price, max_cost, valid_quantity,
                                                  max_quantity, price, valid_quantity, symbol_market_without_max)


async def test_adapt_quantity():
    # will use symbol market
    symbol_market = {Ecmsc.PRECISION.value: {Ecmsc.PRECISION_AMOUNT.value: 4}}
    assert personal_data.decimal_adapt_quantity(symbol_market, decimal.Decimal(str(0.0001))) == decimal.Decimal(
        str(0.0001))
    assert personal_data.decimal_adapt_quantity(symbol_market, decimal.Decimal(str(0.00015))) == decimal.Decimal(
        str(0.0001))
    assert personal_data.decimal_adapt_quantity(symbol_market, decimal.Decimal(str(0.005))) == decimal.Decimal(
        str(0.005))
    assert personal_data.decimal_adapt_quantity(symbol_market, decimal.Decimal(str(1))) == decimal.Decimal(
        str(1.0000000000000000000000001))
    assert personal_data.decimal_adapt_quantity(symbol_market, decimal.Decimal(str(1))) == decimal.Decimal(str(1))

    assert personal_data.decimal_adapt_quantity(symbol_market, decimal.Decimal(str(56.5128597145))) == decimal.Decimal(
        str(56.5128))
    assert personal_data.decimal_adapt_quantity(symbol_market,
                                                decimal.Decimal(str(1251.0000014576121234854513))) == decimal.Decimal(
        str(1251.0000))
    assert personal_data.decimal_adapt_quantity(symbol_market,
                                                decimal.Decimal(str(1251.0000014576121234854513)),
                                                True) == decimal.Decimal(
        str(1251.0000))
    assert personal_data.decimal_adapt_quantity(symbol_market,
                                                decimal.Decimal(str(1251.0000014576121234854513)),
                                                False) == decimal.Decimal(
        str(1251.0001))

    # will use default (0)
    symbol_market = {Ecmsc.PRECISION.value: {}}
    assert personal_data.decimal_adapt_quantity(symbol_market, decimal.Decimal(str(0.0001))) == decimal.Decimal(str(0))
    assert personal_data.decimal_adapt_quantity(symbol_market, decimal.Decimal(str(0.00015))) == decimal.Decimal(str(0))
    assert personal_data.decimal_adapt_quantity(symbol_market, decimal.Decimal(str(0.005))) == decimal.Decimal(str(0))
    assert personal_data.decimal_adapt_quantity(symbol_market, decimal.Decimal(str(1))) == decimal.Decimal(
        str(1.0000000000000000000000001))
    assert personal_data.decimal_adapt_quantity(symbol_market, decimal.Decimal(str(1))) == decimal.Decimal(str(1))

    assert personal_data.decimal_adapt_quantity(symbol_market, decimal.Decimal(str(56.5128597145))) == decimal.Decimal(
        str(56))
    assert personal_data.decimal_adapt_quantity(symbol_market,
                                                decimal.Decimal(str(1251.0000014576121234854513))) == decimal.Decimal(
        str(1251))


async def test_decimal_trunc_with_n_decimal_digits():
    assert personal_data.decimal_trunc_with_n_decimal_digits(decimal.Decimal(1.00000000001), 10) == decimal.Decimal(1)
    assert personal_data.decimal_trunc_with_n_decimal_digits(decimal.Decimal("1.01"), 1, True) == decimal.Decimal(1)
    assert personal_data.decimal_trunc_with_n_decimal_digits(decimal.Decimal("1.01"), 1, False) \
        == decimal.Decimal("1.1")
    assert float(personal_data.decimal_trunc_with_n_decimal_digits(decimal.Decimal(1.00000000001), 10)) == 1
    assert float(personal_data.decimal_trunc_with_n_decimal_digits(decimal.Decimal(1.00000000001), 11)) == 1.00000000001
    assert float(personal_data.decimal_trunc_with_n_decimal_digits(decimal.Decimal(578.000145000156), 3)) == 578
    assert float(personal_data.decimal_trunc_with_n_decimal_digits(decimal.Decimal(578.000145000156), 4)) == 578.0001
    assert float(personal_data.decimal_trunc_with_n_decimal_digits(decimal.Decimal(578.000145000156), 7)) == 578.000145
    assert float(
        personal_data.decimal_trunc_with_n_decimal_digits(decimal.Decimal(11111111111111578.000145000156), 7)) == \
           11111111111111578.000145
    assert float(personal_data.decimal_trunc_with_n_decimal_digits(decimal.Decimal(578.000145000156), 9)) == 578.000145
    assert float(
        personal_data.decimal_trunc_with_n_decimal_digits(decimal.Decimal(578.000145000156), 10)) == 578.0001450001
    # warning here, in python, float(578.000145000156) is not a finite number, therefore its decimal representation
    # is rounded to 578.000145000155. Use str in constructor to get the accurate representation (see next assert)
    assert float(personal_data.decimal_trunc_with_n_decimal_digits(decimal.Decimal(578.000145000156), 12)) == \
           578.000145000155
    assert float(personal_data.decimal_trunc_with_n_decimal_digits(decimal.Decimal("578.000145000156"), 12)) == \
           578.000145000156
    assert float(
        personal_data.decimal_trunc_with_n_decimal_digits(decimal.Decimal(11111111111111578.000145000156), 12)) == \
           11111111111111578.000145000156
    assert math.isnan(personal_data.decimal_trunc_with_n_decimal_digits(decimal.Decimal(math.nan), 12))
