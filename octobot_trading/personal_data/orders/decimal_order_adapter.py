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
import decimal

import octobot_trading.constants as constants
import octobot_trading.exchanges as exchanges
import octobot_trading.personal_data as personal_data
from octobot_trading.enums import ExchangeConstantsMarketStatusColumns as Ecmsc


def decimal_adapt_price(symbol_market, price):
    maximal_price_digits = symbol_market[Ecmsc.PRECISION.value].get(
                                                Ecmsc.PRECISION_PRICE.value,
                                                constants.CURRENCY_DEFAULT_MAX_PRICE_DIGITS)
    return decimal_trunc_with_n_decimal_digits(price, maximal_price_digits)


def decimal_adapt_quantity(symbol_market, quantity):
    maximal_volume_digits = symbol_market[Ecmsc.PRECISION.value].get(
                                                 Ecmsc.PRECISION_AMOUNT.value, 0)
    return decimal_trunc_with_n_decimal_digits(quantity, maximal_volume_digits)


def decimal_trunc_with_n_decimal_digits(value, digits):  # TODO migrate to commons
    try:
        # decimal.Decimal can add unnecessary complexity in numbers, only use it when necessary
        if len(str(value).split(".")[-1]) > digits:
            if digits > constants.ZERO:
                return value.quantize(decimal.Decimal(f".{'0' * digits}"), rounding=decimal.ROUND_DOWN)
            else:
                return value // constants.ONE
        return value
    except (ValueError, decimal.InvalidOperation):
        return value


def decimal_adapt_order_quantity_because_quantity(limiting_value, max_value, quantity_to_adapt, price, symbol_market):
    orders = []
    nb_full_orders = limiting_value // max_value
    rest_order_quantity = limiting_value % max_value
    after_rest_quantity_to_adapt = quantity_to_adapt

    if rest_order_quantity > constants.ZERO:
        after_rest_quantity_to_adapt -= rest_order_quantity
        valid_last_order_quantity = decimal_adapt_quantity(symbol_market, rest_order_quantity)
        orders.append((valid_last_order_quantity, price))

    other_orders_quantity = (after_rest_quantity_to_adapt + max_value) / (nb_full_orders + constants.ONE)
    valid_other_orders_quantity = decimal_adapt_quantity(symbol_market, other_orders_quantity)
    orders += [(valid_other_orders_quantity, price)] * int(nb_full_orders)
    return orders


def decimal_adapt_order_quantity_because_price(limiting_value, max_value, price, symbol_market):
    orders = []
    nb_full_orders = limiting_value // max_value
    rest_order_cost = limiting_value % max_value
    if rest_order_cost > constants.ZERO:
        valid_last_order_quantity = decimal_adapt_quantity(symbol_market, rest_order_cost / price)
        orders.append((valid_last_order_quantity, price))

    other_orders_quantity = max_value / price
    valid_other_orders_quantity = decimal_adapt_quantity(symbol_market, other_orders_quantity)
    orders += [(valid_other_orders_quantity, price)] * int(nb_full_orders)
    return orders


def decimal_split_orders(total_order_price, max_cost, valid_quantity, max_quantity, price, quantity, symbol_market):
    """
    Splits too big orders into multiple ones according to the max_cost and max_quantity
    :param total_order_price:
    :param max_cost:
    :param valid_quantity:
    :param max_quantity:
    :param price:
    :param quantity:
    :param symbol_market:
    :return:
    """
    if max_cost is None and max_quantity is None:
        raise RuntimeError("Impossible to split orders with max_cost and max_quantity undefined.")
    nb_orders_according_to_cost = None
    nb_orders_according_to_quantity = None
    if max_cost:
        nb_orders_according_to_cost = total_order_price / max_cost

    if max_quantity:
        nb_orders_according_to_quantity = valid_quantity / max_quantity

    if nb_orders_according_to_cost is None:
        # can only split using quantity
        return decimal_adapt_order_quantity_because_quantity(valid_quantity, max_quantity,
                                                             quantity, price, symbol_market)
    elif nb_orders_according_to_quantity is None:
        # can only split using price
        return decimal_adapt_order_quantity_because_price(total_order_price, max_cost, price, symbol_market)
    else:
        if nb_orders_according_to_cost > nb_orders_according_to_quantity:
            return decimal_adapt_order_quantity_because_price(total_order_price, max_cost, price, symbol_market)
        return decimal_adapt_order_quantity_because_quantity(valid_quantity, max_quantity,
                                                             quantity, price, symbol_market)


def decimal_check_and_adapt_order_details_if_necessary(quantity, price, symbol_market, fixed_symbol_data = False):
    """
    Checks if order attributes are valid and try to fix it if not
    :param quantity:
    :param price:
    :param symbol_market:
    :param fixed_symbol_data:
    :return:
    """
    if quantity.is_nan() or price.is_nan() or price == constants.ZERO:
        return []

    symbol_market_limits = symbol_market[Ecmsc.LIMITS.value]

    limit_amount = symbol_market_limits[Ecmsc.LIMITS_AMOUNT.value]
    limit_cost = symbol_market_limits[Ecmsc.LIMITS_COST.value]
    limit_price = symbol_market_limits[Ecmsc.LIMITS_PRICE.value]

    # case 1: try with data directly from exchange
    if personal_data.is_valid(limit_amount, Ecmsc.LIMITS_AMOUNT_MIN.value):
        min_quantity = decimal.Decimal(str(limit_amount.get(Ecmsc.LIMITS_AMOUNT_MIN.value, math.nan)))
        max_quantity = None
        # not all symbol data have a max quantity
        if personal_data.is_valid(limit_amount, Ecmsc.LIMITS_AMOUNT_MAX.value):
            max_quantity = decimal.Decimal(str(limit_amount.get(Ecmsc.LIMITS_AMOUNT_MAX.value, math.nan)))

        # adapt digits if necessary
        valid_quantity = decimal_adapt_quantity(symbol_market, quantity)
        valid_price = decimal_adapt_price(symbol_market, price)

        total_order_price = valid_quantity * valid_price

        if valid_quantity < min_quantity:
            # invalid order
            return []

        # case 1.1: use only quantity and cost
        if personal_data.is_valid(limit_cost, Ecmsc.LIMITS_COST_MIN.value):
            min_cost = decimal.Decimal(str(limit_cost.get(Ecmsc.LIMITS_COST_MIN.value, math.nan)))
            max_cost = None
            # not all symbol data have a max cost
            if personal_data.is_valid(limit_cost, Ecmsc.LIMITS_COST_MAX.value):
                max_cost = decimal.Decimal(str(limit_cost.get(Ecmsc.LIMITS_COST_MAX.value, math.nan)))

            # check total_order_price not < min_cost
            if not personal_data.check_cost(float(total_order_price), min_cost):
                return []

            # check total_order_price not > max_cost and valid_quantity not > max_quantity
            elif (max_cost is not None and total_order_price > max_cost) or \
                    (max_quantity is not None and valid_quantity > max_quantity):
                # split quantity into smaller orders
                return decimal_split_orders(total_order_price, max_cost, valid_quantity,
                                            max_quantity, valid_price, quantity, symbol_market)

            else:
                # valid order that can be handled by the exchange
                return [(valid_quantity, valid_price)]

        # case 1.2: use only quantity and price
        elif personal_data.is_valid(limit_price, Ecmsc.LIMITS_PRICE_MIN.value):
            min_price = decimal.Decimal(str(limit_price.get(Ecmsc.LIMITS_PRICE_MIN.value, math.nan)))
            max_price = None
            # not all symbol data have a max price
            if personal_data.is_valid(limit_price, Ecmsc.LIMITS_PRICE_MAX.value):
                max_price = decimal.Decimal(str(limit_price.get(Ecmsc.LIMITS_PRICE_MAX.value, math.nan)))

            if (max_price is not None and (max_price <= valid_price)) or valid_price <= min_price:
                # invalid order
                return []

            # check total_order_price not > max_cost and valid_quantity not > max_quantity
            elif max_quantity is not None and valid_quantity > max_quantity:
                # split quantity into smaller orders
                return decimal_adapt_order_quantity_because_quantity(valid_quantity, max_quantity,
                                                                     quantity, valid_price, symbol_market)
            else:
                # valid order that can be handled wy the exchange
                return [(valid_quantity, valid_price)]

    if not fixed_symbol_data:
        # case 2: try fixing data from exchanges
        fixed_data = exchanges.ExchangeMarketStatusFixer(symbol_market, float(price)).market_status
        return decimal_check_and_adapt_order_details_if_necessary(quantity, price, fixed_data,
                                                                  fixed_symbol_data=True)
    else:
        # impossible to check if order is valid: refuse it
        return []


def decimal_add_dusts_to_quantity_if_necessary(quantity, price, symbol_market, current_symbol_holding):
    """
    Adds remaining quantity to the order if the remaining quantity is too small
    :param quantity:
    :param price:
    :param symbol_market:
    :param current_symbol_holding:
    :return:
    """
    if price == constants.ZERO:
        return quantity

    remaining_portfolio_amount = decimal.Decimal("{1:.{0}f}".format(constants.CURRENCY_DEFAULT_MAX_PRICE_DIGITS,
                                                                    current_symbol_holding - quantity))
    remaining_max_total_order_price = remaining_portfolio_amount * price

    symbol_market_limits = symbol_market[Ecmsc.LIMITS.value]

    limit_amount = symbol_market_limits[Ecmsc.LIMITS_AMOUNT.value]
    limit_cost = symbol_market_limits[Ecmsc.LIMITS_COST.value]

    if not (personal_data.is_valid(limit_amount, Ecmsc.LIMITS_AMOUNT_MIN.value) and
            personal_data.is_valid(limit_cost, Ecmsc.LIMITS_COST_MIN.value)):
        fixed_market_status = exchanges.ExchangeMarketStatusFixer(symbol_market, price).market_status
        limit_amount = fixed_market_status[Ecmsc.LIMITS.value][Ecmsc.LIMITS_AMOUNT.value]
        limit_cost = fixed_market_status[Ecmsc.LIMITS.value][Ecmsc.LIMITS_COST.value]

    min_quantity = limit_amount.get(Ecmsc.LIMITS_AMOUNT_MIN.value, math.nan)
    min_cost = limit_cost.get(Ecmsc.LIMITS_COST_MIN.value, math.nan)

    # check with 40% more than remaining total not to require huge market moves to sell this asset
    min_cost_to_consider = decimal.Decimal(str(min_cost)) * decimal.Decimal(str(1.4))
    min_quantity_to_consider = decimal.Decimal(str(min_quantity)) * decimal.Decimal(str(1.4))

    if remaining_max_total_order_price < min_cost_to_consider \
            or remaining_portfolio_amount < min_quantity_to_consider:
        return current_symbol_holding
    else:
        return quantity
