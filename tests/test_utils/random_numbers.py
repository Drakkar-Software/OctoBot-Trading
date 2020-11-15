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
from random import randrange, uniform

from octobot_commons.enums import PriceIndexes
from octobot_trading.enums import ExchangeConstantsOrderColumns as ECOC

MAX_PRICE = 10e7
MAX_QUANTITY = 10e7
MAX_FUNDING_RATE = 100
MAX_TIMESTAMP = 2000000000


def random_timestamp(min_value=0, max_value=MAX_TIMESTAMP):
    return randrange(min_value, max_value)


def random_price(min_value=0, max_value=None):
    return uniform(min_value, max_value if max_value is not None else MAX_PRICE)


def random_prices(min_value=0, count=2):
    return [random_price(min_value=min_value) for _ in range(count)]


def random_quantity(min_value=0, max_value=MAX_QUANTITY):
    return uniform(min_value, max_value)


def random_quantities(min_value=0, count=2):
    return [random_quantity(min_value=min_value) for _ in range(count)]


def random_price_list(size=2) -> list:
    return [random_price() for _ in range(size)]


def random_funding_rate(min_value=0):
    return uniform(min_value, MAX_FUNDING_RATE)


def random_order_book_side(min_value=0, count=2):
    return [list(pair) for pair in zip(random_prices(min_value=min_value, count=count),
                                       random_quantities(min_value=min_value, count=count))]


def random_candle_tuple():
    return random_price(), random_price(), random_price(), random_price(), random_timestamp()


def random_candle() -> dict:
    return {
        PriceIndexes.IND_PRICE_CLOSE.value: random_price(),
        PriceIndexes.IND_PRICE_OPEN.value: random_price(),
        PriceIndexes.IND_PRICE_HIGH.value: random_price(),
        PriceIndexes.IND_PRICE_LOW.value: random_price(),
        PriceIndexes.IND_PRICE_VOL.value: random_quantity(),
        PriceIndexes.IND_PRICE_TIME.value: random_timestamp()
    }


def random_kline() -> list:
    kline = [0] * len(PriceIndexes)
    kline[PriceIndexes.IND_PRICE_CLOSE.value] = random_price()
    kline[PriceIndexes.IND_PRICE_OPEN.value] = random_price()
    kline[PriceIndexes.IND_PRICE_HIGH.value] = random_price()
    kline[PriceIndexes.IND_PRICE_LOW.value] = random_price()
    kline[PriceIndexes.IND_PRICE_VOL.value] = random_quantity()
    kline[PriceIndexes.IND_PRICE_TIME.value] = random_timestamp()
    return kline


def random_recent_trade(price=None, timestamp=None) -> dict:
    return {
        ECOC.PRICE.value: price if price is not None else random_price(),
        ECOC.AMOUNT.value: random_quantity(),
        ECOC.COST.value: random_quantity(),
        ECOC.TIMESTAMP.value: timestamp if timestamp is not None else random_quantity(),
    }


def random_recent_trades(count=2) -> list:
    return [random_recent_trade() for _ in range(count)]
