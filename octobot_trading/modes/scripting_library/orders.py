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

import octobot_commons.symbol_util as symbol_util
import octobot_commons.constants as common_constants
import octobot_trading.enums as trading_enums
import octobot_trading.personal_data as trading_personal_data
import octobot_trading.constants as trading_constants


async def market(
    trader,
    side=None,
    symbol=None,
    amount=None,
    total_balance_percent=None,
    available_balance_percent=None,
    position=None,
    position_percent=None,
    amount_position_percent=None,
    tag=None
):
    await _create_order_instance(
        trader,
        side,
        symbol,
        amount,
        total_balance_percent=total_balance_percent,
        available_balance_percent=available_balance_percent,
        position=position,
        position_percent=position_percent,
        amount_position_percent=amount_position_percent,
        order_type=trading_enums.TraderOrderType.SELL_MARKET if side == "sell" else trading_enums.TraderOrderType.BUY_MARKET,
        tag=tag,
    )


async def limit(
    trader,
    price=None,
    side=None,
    symbol=None,
    amount=None,
    total_balance_percent=None,
    available_balance_percent=None,
    position=None,
    position_percent=None,
    amount_position_percent=None,
    tag=None,
):
    await _create_order_instance(
        trader,
        side,
        symbol,
        amount,
        total_balance_percent=total_balance_percent,
        available_balance_percent=available_balance_percent,
        position=position,
        position_percent=position_percent,
        amount_position_percent=amount_position_percent,
        order_type=trading_enums.TraderOrderType.SELL_LIMIT if side == "sell" else trading_enums.TraderOrderType.BUY_LIMIT,
        price=price,
        tag=tag,
    )


async def trailling_market(
    trader,
    side=None,
    symbol=None,
    amount=None,
    total_balance_percent=None,
    available_balance_percent=None,
    position=None,
    position_percent=None,
    amount_position_percent=None,
    min_offset_percent=None,
    max_offset_percent=None,
    slippage_limit=None,
    postonly=False,
    tag=None,
):
    await _create_order_instance(
        trader,
        side,
        symbol,
        amount,
        total_balance_percent=total_balance_percent,
        available_balance_percent=available_balance_percent,
        position=position,
        position_percent=position_percent,
        amount_position_percent=amount_position_percent,
        order_type=trading_enums.TraderOrderType.TRAILING_STOP,
        min_offset_percent=min_offset_percent,
        max_offset_percent=max_offset_percent,
        tag=tag,
    )


async def stop(
    trader,
    side=None,
    symbol=None,
    amount=None,
    total_balance_percent=None,
    available_balance_percent=None,
    position=None,
    position_percent=None,
    amount_position_percent=None,
    min_offset_percent=None,
    max_offset_percent=None,
    slippage_limit=None,
    post_only=False,
    tag=None,
):
    await _create_order_instance(
        trader,
        side,
        symbol,
        amount,
        total_balance_percent=total_balance_percent,
        available_balance_percent=available_balance_percent,
        position=position,
        position_percent=position_percent,
        amount_position_percent=amount_position_percent,
        order_type=trading_enums.TraderOrderType.TRAILING_STOP,
        min_offset_percent=min_offset_percent,
        max_offset_percent=max_offset_percent,
        tag=tag,
    )


async def _create_order_instance(
    trader,
    side=None,
    symbol=None,
    amount=None,
    total_balance_percent=None,
    available_balance_percent=None,
    position=None,
    position_percent=None,
    amount_position_percent=None,
    order_type=None,
    price=None,
    min_offset_percent=None,
    max_offset_percent=None,
    reduce_only=False,    #Todo
    post_only=False,    #Todo
    tag=None    #Todo
):
    # 1. create order instance
    current_symbol_holding, current_market_holding, market_quantity, current_price, symbol_market = \
        await trading_personal_data.get_pre_order_data(trader.exchange_manager,
                                                       symbol=symbol,
                                                       timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT)
    order_quantity = amount
    if available_balance_percent is not None:
        order_quantity = _get_amount_from_percent(available_balance_percent, side, current_symbol_holding,
                                                  market_quantity)
    if total_balance_percent is not None:
        order_quantity = _get_amount_from_total_balance(total_balance_percent, side, current_symbol_holding,
                                                        trader, current_price)
    if order_quantity is None:
        raise RuntimeError("No provided quantity to create order.")
    if order_quantity == 0:
        raise RuntimeError("Computed quantity for order is 0.")
    orders = []
    for order_quantity, order_price in trading_personal_data.decimal_check_and_adapt_order_details_if_necessary(
            order_quantity,
            price if price else current_price,
            symbol_market):
        created_order = trading_personal_data.create_order_instance(
            trader=trader,
            order_type=order_type,
            symbol=symbol,
            current_price=current_price,
            quantity=order_quantity,
            price=price)
        if min_offset_percent is not None:
            await created_order.set_trailing_percent(min_offset_percent)
        # 2. submit it to trader
        created_order = await trader.create_order(created_order)
        orders.append(created_order)
    return orders


def _get_amount_from_percent(amount, side, current_symbol_holding, market_quantity):
    if side == "sell":
        return current_symbol_holding * amount / 100
    return market_quantity * amount / 100


def _get_amount_from_total_balance(amount, side, symbol, trader, price):
    currency, market = symbol_util.split_symbol(symbol)
    currency_to_use = currency if side == "sell" else market
    total_amount = trader.exchange_manager.exchange_personal_data.portfolio_manager.portfolio.get_currency_portfolio(
        currency_to_use,
        common_constants.PORTFOLIO_TOTAL
    )
    if side == "sell":
        return total_amount * amount / 100
    return total_amount / price * amount / 100


def _get_amount_from_position(target_position_size, current_symbol_holding, market_quantity):
    current_position_size = 100 # TODO

    target_position_size - current_position_size

    if target_position_size > 0:
        # long
        if current_position_size > 0:
            difference = target_position_size - current_position_size
        else:
            difference = target_position_size + abs(current_position_size)
    if target_position_size < 0:
        # shot
        if current_position_size < 0:
            difference = abs(target_position_size - current_position_size)
        else:
            # sell
            difference = abs(target_position_size) + current_position_size

    # idea: neg: sell, positive: buy
    return difference
