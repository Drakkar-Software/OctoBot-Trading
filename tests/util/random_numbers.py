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

MAX_PRICE = 10e7
MAX_QUANTITY = 10e7
MAX_FUNDING_RATE = 100


def random_timestamp(min_value=0):
    return randrange(min_value, 2000000000)


def random_price(min_value=0):
    return uniform(min_value, MAX_PRICE)


def random_quantity(min_value=0):
    return uniform(min_value, MAX_QUANTITY)


def random_price_list(size=2) -> list:
    return [random_price() for _ in range(size)]


def random_funding_rate(min_value=0):
    return uniform(min_value, MAX_FUNDING_RATE)


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
