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
import decimal
import contextlib

import octobot_commons.symbol_util as symbol_util
import octobot_commons.constants as commons_constants
import octobot_commons.logging as logging
import octobot_commons.timestamp_util as timestamp_util
import octobot_trading.constants as constants
import octobot_trading.enums as enums
import octobot_trading.errors as errors
import octobot_trading.exchanges.util.exchange_market_status_fixer as exchange_market_status_fixer
from octobot_trading.enums import ExchangeConstantsMarketStatusColumns as Ecmsc


LOGGER_NAME = "order_util"


def is_valid(element, key):
    """
    Checks is the element is valid with the market status fixer
    :param element:
    :param key:
    :return:
    """
    return key in element and exchange_market_status_fixer.is_ms_valid(element[key])


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
            logging.get_logger(LOGGER_NAME).error("Invalid min_cost from exchange")
        return False
    return True


async def get_up_to_date_price(exchange_manager, symbol: str, timeout: int = None, base_error: str = None):
    exchange_time = exchange_manager.exchange.get_exchange_current_time()
    base_error = base_error or f"Can't get the necessary price data to create a new order on the " \
                               f"{timestamp_util.convert_timestamp_to_datetime(exchange_time)} " \
                               f"(timestamp: {exchange_time}):"
    try:
        mark_price = await exchange_manager.exchange_symbols_data.get_exchange_symbol_data(symbol) \
            .prices_manager.get_mark_price(timeout=timeout)
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError(f"{base_error} mark price is not available")
    except errors.UnreachableExchange as e:
        raise errors.UnreachableExchange(f"{base_error} exchange is unreachable") from e
    return decimal.Decimal(str(mark_price))


async def get_pre_order_data(exchange_manager, symbol: str, timeout: int = None,
                             portfolio_type=commons_constants.PORTFOLIO_AVAILABLE):
    mark_price = await get_up_to_date_price(exchange_manager, symbol, timeout=timeout)
    symbol_market = exchange_manager.exchange.get_market_status(symbol, with_fixer=False)

    currency, market = symbol_util.split_symbol(symbol)
    portfolio = exchange_manager.exchange_personal_data.portfolio_manager.portfolio
    currency_available = portfolio.get_currency_portfolio(currency).available \
        if portfolio_type == commons_constants.PORTFOLIO_AVAILABLE else portfolio.get_currency_portfolio(currency).total
    market_available = portfolio.get_currency_portfolio(market).available \
        if portfolio_type == commons_constants.PORTFOLIO_AVAILABLE else portfolio.get_currency_portfolio(market).total

    if exchange_manager.is_future:
        pair_future_contract = exchange_manager.exchange.get_pair_future_contract(symbol)
        if pair_future_contract.is_inverse_contract():
            currency_available *= pair_future_contract.current_leverage
            market_quantity = market_available = currency_available
        else:
            market_available *= pair_future_contract.current_leverage / mark_price
            market_quantity = currency_available = market_available
    elif exchange_manager.is_margin:
        market_quantity = constants.ZERO  # TODO
    else:
        market_quantity = market_available / mark_price if mark_price else constants.ZERO
    return currency_available, market_available, market_quantity, mark_price, symbol_market


def get_futures_max_order_size(exchange_manager, symbol, side, current_price, reduce_only,
                               current_symbol_holding, market_quantity):
    # use position margin when trading futures and reducing the position
    current_position = exchange_manager.exchange_personal_data.positions_manager.get_symbol_position(
        symbol,
        enums.PositionSide.BOTH
    )
    # ensure max position order size is taken into account
    new_position_side = current_position.side
    if new_position_side is enums.PositionSide.UNKNOWN:
        new_position_side = enums.PositionSide.LONG if side is enums.TradeOrderSide.BUY \
            else enums.PositionSide.SHORT

    contract_current_symbol_holding = current_symbol_holding
    contract_market_quantity = market_quantity
    if current_position.symbol_contract.is_inverse_contract():
        # use USD (in BTC/USD) for order sizes on inverse, convert BTC values into USD ones
        contract_current_symbol_holding = current_symbol_holding * current_price
        contract_market_quantity = market_quantity * current_price
    if side is enums.TradeOrderSide.SELL and current_position.is_long():
        # can also sell the position size in long
        contract_current_symbol_holding = current_position.size if reduce_only \
            else contract_current_symbol_holding + current_position.size
    elif side is enums.TradeOrderSide.BUY and current_position.is_short():
        # can also buy the position size in short
        contract_market_quantity = abs(current_position.size) if reduce_only \
            else contract_market_quantity + abs(current_position.size)
    if (new_position_side is enums.PositionSide.LONG and side is enums.TradeOrderSide.BUY) \
            or (new_position_side is enums.PositionSide.SHORT and
                side is enums.TradeOrderSide.SELL):
        quantity = market_quantity if current_position.symbol_contract.is_inverse_contract() \
            else market_quantity * current_price
        unleveraged_quantity = quantity / current_position.symbol_contract.current_leverage
        max_position_increased_order_quantity = get_max_order_quantity_for_price(
            current_position, unleveraged_quantity, current_price, new_position_side, symbol
        )
        # increasing position: always use the same currency
        return max_position_increased_order_quantity, True
    return contract_market_quantity if side is enums.TradeOrderSide.BUY else contract_current_symbol_holding, False


def get_max_order_quantity_for_price(position, available_quantity, price, side, symbol):
    """
    Returns the maximum order quantity in market or currency for given total usable funds, price and side.
    This amount is not the total usable funds as it also requires to keep the position's open order fees
    as well as the potential position liquidation fees in portfolio. Those fees are computed by
    get_two_way_taker_fee_for_quantity_and_price
    :param position: the position to compute quantity for
    :param available_quantity: the maximum amount of currency/market to allocate to the position (without leverage)
    :param price: the target entry price of the position
    :param side: the side of the position
    :param side: the symbol of the position
    :return: the computed leveraged maximum entry quantity
    """
    # use position.symbol_contract.current_leverage as quantity to simulate a 1 unit quantity (x leverage)
    two_way_fees = position.get_two_way_taker_fee_for_quantity_and_price(position.symbol_contract.current_leverage,
                                                                         price, side, symbol)
    if position.symbol_contract.is_inverse_contract():
        # Returns the maximum order quantity in market.
        return position.symbol_contract.current_leverage * available_quantity / \
            (two_way_fees + constants.ONE / price)
    # Returns the maximum order quantity in currency.
    return position.symbol_contract.current_leverage * available_quantity / \
        (two_way_fees + price)


def total_fees_from_order_dict(order_dict, currency):
    return get_fees_for_currency(order_dict[enums.ExchangeConstantsOrderColumns.FEE.value], currency)


def get_fees_for_currency(fee, currency):
    if fee and fee[enums.FeePropertyColumns.CURRENCY.value] == currency:
        return decimal.Decimal(str(fee[enums.FeePropertyColumns.COST.value]))
    return constants.ZERO


def parse_raw_fees(raw_fees):
    fees = raw_fees
    if fees and enums.ExchangeConstantsOrderColumns.COST.value in fees:
        raw_fees[enums.ExchangeConstantsOrderColumns.COST.value] = \
            decimal.Decimal(str(raw_fees[enums.ExchangeConstantsOrderColumns.COST.value]))
    return fees


def parse_order_status(raw_order):
    try:
        return enums.OrderStatus(raw_order[enums.ExchangeConstantsOrderColumns.STATUS.value])
    except KeyError:
        return KeyError("Could not parse new order status")


def parse_is_cancelled(raw_order):
    return parse_order_status(raw_order) in {enums.OrderStatus.CANCELED, enums.OrderStatus.CLOSED}


def get_pnl_transaction_source_from_order(order):
    if order.order_type in [enums.TraderOrderType.SELL_MARKET, enums.TraderOrderType.BUY_MARKET,
                            enums.TraderOrderType.TAKE_PROFIT]:
        return enums.PNLTransactionSource.MARKET_ORDER
    if order.order_type in [enums.TraderOrderType.SELL_LIMIT, enums.TraderOrderType.BUY_LIMIT,
                            enums.TraderOrderType.TAKE_PROFIT_LIMIT]:
        return enums.PNLTransactionSource.LIMIT_ORDER
    if is_stop_order(order.order_type):
        return enums.PNLTransactionSource.STOP_ORDER
    return enums.PNLTransactionSource.UNKNOWN


def is_stop_order(order_type):
    return order_type in [enums.TraderOrderType.STOP_LOSS, enums.TraderOrderType.STOP_LOSS_LIMIT,
                          enums.TraderOrderType.TRAILING_STOP, enums.TraderOrderType.TRAILING_STOP_LIMIT]


async def create_as_chained_order(order):
    order.is_waiting_for_chained_trigger = False
    if not order.trader.simulate and order.has_been_bundled:
        # exchange should have created it already, it is either already fetched or
        # will automatically be fetched at the next update
        # warning: not handling instantly filled bundled orders as there is no easy way to do this
        # TODO: figure out instantly filled bundled orders
        if not await _apply_pending_order_on_existing_orders(order):
            # register it as pending creation order for it to be found and update when fetched
            order.exchange_manager.exchange_personal_data.orders_manager.register_pending_creation_order(order)
    else:
        # set created now to consider creation failures as created as well (the caller can always retry later on)
        order.status = enums.OrderStatus.OPEN
        # set uninitialized to allow second initialization from create_order
        order.is_initialized = False
        await order.trader.create_order(
            order,
            loaded=False,
            params=order.exchange_creation_params,
            **order.trader_creation_kwargs
        )


def is_associated_pending_order(pending_order, created_order):
    return created_order.symbol == pending_order.symbol and \
           created_order.origin_quantity == pending_order.origin_quantity and \
           created_order.origin_price == pending_order.origin_price and \
           created_order.__class__ is pending_order.__class__ and \
           created_order.trader is pending_order.trader


async def apply_pending_order_from_created_order(pending_order, created_order, to_be_initialized):
    await pending_order.update_from_order(created_order)
    if to_be_initialized:
        pending_order.is_initialized = False
    logging.get_logger(LOGGER_NAME).debug(f"Updated pending order: {pending_order} using {created_order}")


async def _apply_pending_order_on_existing_orders(pending_order):
    for created_order in pending_order.exchange_manager.exchange_personal_data.orders_manager.get_open_orders(
            symbol=pending_order.symbol):
        if is_associated_pending_order(pending_order, created_order) and created_order.order_group is None:
            await apply_pending_order_from_created_order(pending_order, created_order, False)
            pending_order.exchange_manager.exchange_personal_data.orders_manager.replace_order(created_order.order_id,
                                                                                               pending_order)
            created_order.clear()
            return True
    return False


@contextlib.asynccontextmanager
async def ensure_orders_relevancy(order=None, position=None):
    exchange_manager = order.exchange_manager if position is None else position.exchange_manager
    # part used in futures trading only
    if exchange_manager.exchange_personal_data.positions_manager.positions:
        position = position or exchange_manager.exchange_personal_data.positions_manager.get_order_position(order)
        pre_update_position_side = position.side
        is_pre_update_position_idle = position.is_idle()
        yield
        if not is_pre_update_position_idle and \
           (position.side != pre_update_position_side or position.is_idle()):
            # when position side is changing (from a non-idle position) or is going back to idle,
            # then associated reduce only orders must be closed
            await _cancel_reduce_only_orders_on_position_reset(exchange_manager, position.symbol)
    else:
        # as a context manager, yield is mandatory
        yield


async def _cancel_reduce_only_orders_on_position_reset(exchange_manager, symbol):
    for order in list(exchange_manager.exchange_personal_data.orders_manager.get_open_orders(symbol)):
        # reduce only order are automatically cancelled on exchanges, only cancel simulated orders
        if (exchange_manager.is_trader_simulated or order.is_self_managed()) \
                and order.is_open() and order.reduce_only:
            await order.trader.cancel_order(order)
            if order.order_group:
                await order.order_group.on_cancel(order)


def get_order_quantity_currency(exchange_manager, symbol, side):
    try:
        base, quote = symbol_util.split_symbol(symbol)
    except ValueError:
        # symbol that can't be split
        return None
    if exchange_manager.is_future:
        position = exchange_manager.exchange_personal_data.positions_manager.get_symbol_position(
            symbol, side
        )
        return quote if position.symbol_contract.is_inverse_contract() else base
    # always base in spot
    return base
