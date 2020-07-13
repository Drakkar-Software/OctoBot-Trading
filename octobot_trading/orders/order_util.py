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
import asyncio

from octobot_commons.symbol_util import split_symbol
from octobot_commons.logging.logging_util import get_logger
from octobot_trading.enums import ExchangeConstantsMarketStatusColumns as Ecmsc, ExchangeConstantsOrderColumns, \
    FeePropertyColumns, OrderStatus
from octobot_trading.exchanges.util.exchange_market_status_fixer import is_ms_valid


def is_valid(element, key):
    """
    Checks is the element is valid with the market status fixer
    :param element:
    :param key:
    :return:
    """
    return key in element and is_ms_valid(element[key])


def get_min_max_amounts(symbol_market, default_value=None):
    """
    Returns the min and max quantity, cost and price according to the specified market
    :param symbol_market:
    :param default_value:
    :return:
    """
    min_quantity = max_quantity = min_cost = max_cost = min_price = max_price = default_value
    if Ecmsc.LIMITS.value in symbol_market:
        symbol_market_limits = symbol_market[Ecmsc.LIMITS.value]

        if Ecmsc.LIMITS_AMOUNT.value in symbol_market_limits:
            limit_amount = symbol_market_limits[Ecmsc.LIMITS_AMOUNT.value]
            if is_valid(limit_amount, Ecmsc.LIMITS_AMOUNT_MIN.value) \
                    or is_valid(limit_amount, Ecmsc.LIMITS_AMOUNT_MAX.value):
                min_quantity = limit_amount.get(Ecmsc.LIMITS_AMOUNT_MIN.value, default_value)
                max_quantity = limit_amount.get(Ecmsc.LIMITS_AMOUNT_MAX.value, default_value)

        # case 2: use cost and price
        if Ecmsc.LIMITS_COST.value in symbol_market_limits:
            limit_cost = symbol_market_limits[Ecmsc.LIMITS_COST.value]
            if is_valid(limit_cost, Ecmsc.LIMITS_COST_MIN.value) \
                    or is_valid(limit_cost, Ecmsc.LIMITS_COST_MAX.value):
                min_cost = limit_cost.get(Ecmsc.LIMITS_COST_MIN.value, default_value)
                max_cost = limit_cost.get(Ecmsc.LIMITS_COST_MAX.value, default_value)

        # case 2: use quantity and price
        if Ecmsc.LIMITS_PRICE.value in symbol_market_limits:
            limit_price = symbol_market_limits[Ecmsc.LIMITS_PRICE.value]
            if is_valid(limit_price, Ecmsc.LIMITS_PRICE_MIN.value) \
                    or is_valid(limit_price, Ecmsc.LIMITS_PRICE_MAX.value):
                min_price = limit_price.get(Ecmsc.LIMITS_PRICE_MIN.value, default_value)
                max_price = limit_price.get(Ecmsc.LIMITS_PRICE_MAX.value, default_value)

    return min_quantity, max_quantity, min_cost, max_cost, min_price, max_price


def check_cost(total_order_price, min_cost):
    """
    Checks and adapts the quantity and price of the order to ensure it's exchange compliant:
    - are the quantity and price of the order compliant with the exchange's number of digits requirement
        => otherwise quantity will be truncated accordingly
    - is the quantity valid
    - are the order total price and quantity superior or equal to the exchange's minimum order requirement
        => otherwise order is impossible => returns empty list
    - if total cost data are unavailable:
    - is the price of the currency compliant with the exchange's price interval for this currency
        => otherwise order is impossible => returns empty list
    - are the order total price and quantity inferior or equal to the exchange's maximum order requirement
        => otherwise order is impossible as is => split order into smaller ones and returns the list
    => returns the quantity and price list of possible order(s)
    - if exchange symbol data are not enough
        => try fixing exchange data using ExchangeMarketStatusFixer are start again (once only)
    """
    if total_order_price < min_cost:
        if min_cost is None:
            get_logger().error("Invalid min_cost from exchange")
        return False
    return True


async def get_pre_order_data(exchange_manager, symbol: str, timeout: int = None):
    try:
        mark_price = await exchange_manager.exchange_symbols_data.get_exchange_symbol_data(symbol) \
            .prices_manager.get_mark_price(timeout=timeout)
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError("Mark price is not available")

    currency, market = split_symbol(symbol)

    current_symbol_holding = exchange_manager.exchange_personal_data.portfolio_manager.portfolio\
        .get_currency_portfolio(currency)
    current_market_quantity = exchange_manager.exchange_personal_data.portfolio_manager.portfolio\
        .get_currency_portfolio(market)

    market_quantity = current_market_quantity / mark_price

    symbol_market = exchange_manager.exchange.get_market_status(symbol, with_fixer=False)

    return current_symbol_holding, current_market_quantity, market_quantity, mark_price, symbol_market


def total_fees_from_order_dict(order_dict, currency):
    return get_fees_for_currency(order_dict[ExchangeConstantsOrderColumns.FEE.value], currency)


def get_fees_for_currency(fee, currency):
    if fee and fee[FeePropertyColumns.CURRENCY.value] == currency:
        return fee[FeePropertyColumns.COST.value]
    return 0


def parse_order_status(raw_order):
    try:
        return OrderStatus(raw_order[ExchangeConstantsOrderColumns.STATUS.value])
    except KeyError:
        return KeyError("Could not parse new order status")


def parse_is_closed(raw_order):
    return parse_order_status(raw_order) in {OrderStatus.CANCELED, OrderStatus.CLOSED}


def parse_is_cancelled(raw_order):
    return parse_order_status(raw_order) in {OrderStatus.CANCELED, OrderStatus.CLOSED}
