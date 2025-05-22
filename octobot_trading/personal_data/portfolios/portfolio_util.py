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
import copy
import decimal
import typing

import octobot_trading.personal_data.portfolios.asset as asset
import octobot_trading.personal_data.portfolios.assets
import octobot_trading.personal_data.orders.order as order_import
import octobot_trading.personal_data.orders.order_util as order_util
import octobot_trading.personal_data.portfolios.sub_portfolio_data as sub_portfolio_data
import octobot_trading.constants as constants
import octobot_trading.enums as enums
import octobot_trading.errors as errors

import octobot_commons.constants as commons_constants
import octobot_commons.logging as commons_logging
import octobot_commons.symbols as symbol_util

import numpy as numpy


def parse_decimal_portfolio(portfolio, as_decimal=True):
    decimal_portfolio = {}
    for symbol, symbol_balance in portfolio.items():
        if isinstance(symbol_balance, dict):
            decimal_portfolio[symbol] = {}
            portfolio_to_fill = decimal_portfolio[symbol]
            for balance_type, balance_val in symbol_balance.items():
                if isinstance(balance_val, (int, float, decimal.Decimal)):
                    portfolio_to_fill[balance_type] = decimal.Decimal(str(balance_val)) \
                        if as_decimal else float(balance_val)
    return decimal_portfolio


def parse_decimal_config_portfolio(portfolio):
    return {
        symbol: {
            k: decimal.Decimal(str(v))
            for k, v in symbol_balance.items()
        } if isinstance(symbol_balance, dict) else decimal.Decimal(str(symbol_balance))
        for symbol, symbol_balance in portfolio.items()
    }


def filter_empty_values(portfolio):
    return {
        symbol: value
        for symbol, value in portfolio.items()
        if value[commons_constants.PORTFOLIO_TOTAL] > 0
    }


def portfolio_to_float(portfolio, use_wallet_balance_on_futures=False):
    float_portfolio = {}
    for symbol, symbol_balance in portfolio.items():
        if (
            isinstance(symbol_balance, octobot_trading.personal_data.portfolios.assets.FutureAsset)
            and use_wallet_balance_on_futures
        ):
            float_portfolio[symbol] = {
                commons_constants.PORTFOLIO_AVAILABLE: float(symbol_balance.available),
                commons_constants.PORTFOLIO_TOTAL: float(symbol_balance.wallet_balance)
            }
        elif isinstance(symbol_balance, asset.Asset):
            float_portfolio[symbol] = {
                commons_constants.PORTFOLIO_AVAILABLE: float(symbol_balance.available),
                commons_constants.PORTFOLIO_TOTAL: float(symbol_balance.total)
            }
    return float_portfolio


def format_dict_portfolio_values(
    portfolio: dict[str, dict[str, typing.Union[float, decimal.Decimal]]], as_decimal: bool
) -> dict[str, dict[str, typing.Union[float, decimal.Decimal]]]:
    return {
        asset_name: {
            key: decimal.Decimal(str(val)) if as_decimal else float(val)
            for key, val in asset_content.items()
        }
        for asset_name, asset_content in portfolio.items()
    }


def get_draw_down(exchange_manager):
    """
    Draw down is the lowest portfolio value in % ever reached during a run
    :return: the Draw down value
    """
    draw_down = constants.ZERO
    if exchange_manager.is_future:
        try:
            value_currency = exchange_manager.exchange_personal_data.portfolio_manager.reference_market
            draw_down_pair = exchange_manager.exchange_config.traded_symbol_pairs[0]
            if exchange_manager.exchange_personal_data.positions_manager.get_symbol_position(
                draw_down_pair,
                enums.PositionSide.BOTH
            ).symbol_contract.is_inverse_contract():
                value_currency = symbol_util.parse_symbol(draw_down_pair).base
            if exchange_manager.exchange_personal_data.portfolio_manager.portfolio_value_holder.origin_portfolio \
                    is None:
                return constants.ZERO
            origin_value = exchange_manager.exchange_personal_data.portfolio_manager.portfolio_value_holder \
                .origin_portfolio.portfolio[value_currency].total
            portfolio_history = [origin_value]
            for transaction in exchange_manager.exchange_personal_data.transactions_manager.transactions.values():
                current_pnl = transaction.quantity if hasattr(transaction, "quantity") else transaction.realised_pnl
                portfolio_history.append(portfolio_history[-1] + current_pnl)

                current_draw_down = constants.ONE_HUNDRED - \
                    (portfolio_history[-1] / (max(portfolio_history) / constants.ONE_HUNDRED))

                draw_down = current_draw_down if current_draw_down > draw_down else draw_down
        except Exception as e:
            commons_logging.get_logger(__name__).warning(f"Error when computing draw down: {e}")
    return draw_down


async def get_coefficient_of_determination_data(transactions, start_balance,
                                                use_high_instead_of_end_balance=True,
                                                x_as_trade_count=True):
    if transactions:
        # get realized portfolio history

        pnl_history = [start_balance]
        pnl_history_times = []
        for transaction in transactions:
            current_pnl = None
            if hasattr(transaction, "quantity"):
                current_pnl = float(transaction.quantity)
                pnl_history_times.append(transaction.creation_time)
            elif hasattr(transaction, 'realised_pnl'):
                current_pnl = float(transaction.realised_pnl)
                pnl_history_times.append(transaction.creation_time)
            elif isinstance(transaction, dict):
                if transaction["quantity"]:
                    current_pnl = transaction["quantity"]
                    pnl_history_times.append(transaction["x"])
                elif transaction['realised_pnl']:
                    current_pnl = transaction['realised_pnl']
                    pnl_history_times.append(transaction["x"])

            if current_pnl is not None:
                pnl_history.append(pnl_history[-1] + current_pnl)

        if pnl_history_times:

            pnl_history_for_every_candle = None
            # either use trade to trade basis or candle to candle basis
            if x_as_trade_count is True:
                start_time = pnl_history_times[0]
                pnl_history_times.insert(0, start_time)
                end_time = pnl_history_times[-1]
                data_length = len(pnl_history)

            else:  # calculate pnl history for every candle
                raise NotImplementedError("x_as_trade_count=False is not implemented")
            # calculate best case data (exponential growth)
            end_balance = pnl_history[-1]

            if start_balance > end_balance:
                # if we end up with a negative balance we can't compute this
                return None, None, None, None, None

            if use_high_instead_of_end_balance:
                end_value = max(pnl_history)
            else:  # use the end balance
                end_value = end_balance

            def get_ideal_value(linear_growth, adj1, adj2):
                return ((linear_growth + adj1) ** pw) * adj2

            x = [start_time, end_time]
            y = [start_balance, end_value]

            pw = 15
            A = numpy.exp(numpy.log(y[0] / y[1]) / pw)
            a = (x[0] - x[1] * A) / (A - 1)
            b = y[0] / (x[0] + a) ** pw

            linear_growth = numpy.linspace(start_time, end_time, data_length)
            best_case = get_ideal_value(linear_growth, a, b)
            pnl_data = pnl_history_for_every_candle or pnl_history
            return list(best_case), pnl_data, start_balance, end_balance, pnl_history_times
    return None, None, None, None, None


async def get_coefficient_of_determination(exchange_manager, use_high_instead_of_end_balance=True):
    """
    Calculates proximity to the best case growth for the current run (best growth being associated to an exponential
    curve). The closer the actual result, the higher the coefficient_of_determination (R squared) will be.
    Return 0 if we end up with less money that we had to begin with
    :param use_high_instead_of_end_balance: best case exponential growth based on end balance or highest balance
    """
    coefficient_of_determination = 0
    if exchange_manager.exchange_personal_data.portfolio_manager is None or \
            exchange_manager.exchange_personal_data.portfolio_manager.portfolio_value_holder.origin_portfolio is None:
        return 0
    # get data the data necessary to compute the coefficient_of_determination
    origin_portfolio = portfolio_to_float(
        exchange_manager.exchange_personal_data.portfolio_manager.portfolio_value_holder.origin_portfolio.portfolio
    )
    start_balance = origin_portfolio[
        exchange_manager.exchange_personal_data.portfolio_manager.reference_market][commons_constants.PORTFOLIO_TOTAL]

    best_case, pnl_data, start_balance, _, _ \
        = await get_coefficient_of_determination_data(transactions=exchange_manager.exchange_personal_data.
                                                      transactions_manager.transactions.values(),
                                                      start_balance=start_balance,
                                                      use_high_instead_of_end_balance=use_high_instead_of_end_balance)

    if pnl_data:
        # calculate r²
        corr_matrix = numpy.corrcoef(best_case, pnl_data)
        corr = corr_matrix[0, 1]
        coefficient_of_determination = corr ** 2

    return round(coefficient_of_determination, 3)


def get_asset_price_from_converter_or_tickers(
    exchange_manager, to_convert_asset: str, target_asset: str, symbol: str, tickers: dict
):
    # 1. try with converter
    try:
        price = exchange_manager.exchange_personal_data.portfolio_manager. \
            portfolio_value_holder.value_converter.evaluate_value(
                to_convert_asset, constants.ONE, raise_error=True,
                target_currency=target_asset, init_price_fetchers=False
            )
        if price == constants.ZERO:
            raise errors.MissingPriceDataError
    except errors.MissingPriceDataError:
        # 2. try with tickers
        try:
            price = decimal.Decimal(str(
                tickers[symbol][enums.ExchangeConstantsTickersColumns.CLOSE.value]
                or tickers[symbol][enums.ExchangeConstantsTickersColumns.PREVIOUS_CLOSE.value]
            ))
        except KeyError:
            price = None
    return price


def resolve_sub_portfolios(
    master_portfolio: sub_portfolio_data.SubPortfolioData,
    sub_portfolios: list[sub_portfolio_data.SubPortfolioData],
    allowed_filling_assets: list[str],
    forbidden_filling_assets: list[str],
    market_prices: dict[str, float],
) -> (sub_portfolio_data.SubPortfolioData, list[sub_portfolio_data.SubPortfolioData]):
    resolved_portfolios = []
    remaining_master_portfolio = copy.deepcopy(master_portfolio)
    for sub_portfolio in sorted(sub_portfolios, key=lambda x: x.priority_key):
        resolved_portfolio = _resolve_sub_portfolio(
            remaining_master_portfolio, sub_portfolio, allowed_filling_assets, forbidden_filling_assets, market_prices
        )
        resolved_portfolios.append(resolved_portfolio)
    return remaining_master_portfolio, resolved_portfolios


def _resolve_sub_portfolio(
    remaining_master_portfolio: sub_portfolio_data.SubPortfolioData,
    sub_portfolio: sub_portfolio_data.SubPortfolioData,
    allowed_filling_assets: list[str],
    forbidden_filling_assets: list[str],
    market_prices: dict[str, float],
) -> sub_portfolio_data.SubPortfolioData:
    resolved_content = {}
    funds_deltas = {}
    missing_funds = {}
    missing_amount_by_asset = {}
    forecasted_sub_portfolio_content = sub_portfolio.get_content_after_deltas()
    for asset_name, holdings in forecasted_sub_portfolio_content.items():
        missing_amount_in_asset = _resolve_sub_portfolio_asset(
            asset_name, holdings, remaining_master_portfolio, resolved_content,
            sub_portfolio.locked_funds_by_asset.get(asset_name, constants.ZERO), forbidden_filling_assets
        )
        if missing_amount_in_asset > constants.ZERO:
            missing_amount_by_asset[asset_name] = missing_amount_in_asset
    # now that assets have been allocated, try to compensate missing assets
    for asset_name, missing_amount_in_asset in missing_amount_by_asset.items():
        _fill_missing_assets_from_allowed_filling_assets(
            asset_name, allowed_filling_assets, market_prices,
            remaining_master_portfolio, missing_amount_in_asset,
            resolved_content, funds_deltas, missing_funds
        )

    return sub_portfolio_data.SubPortfolioData(
        sub_portfolio.bot_id,
        sub_portfolio.portfolio_id,
        sub_portfolio.priority_key,
        resolved_content,
        sub_portfolio.unit,
        funds_deltas,
        missing_funds,
    )


def _resolve_sub_portfolio_asset(
    asset_name: str,
    holdings: dict[str, decimal.Decimal],
    remaining_master_portfolio: sub_portfolio_data.SubPortfolioData,
    resolved_content: dict[str, dict[str, decimal.Decimal]],
    locked_funds: decimal.Decimal,
    forbidden_filling_assets: list[str]
) -> decimal.Decimal:
    required_total_amount = holdings[commons_constants.PORTFOLIO_TOTAL]
    required_available_amount = holdings[commons_constants.PORTFOLIO_TOTAL] - locked_funds
    missing_amount_in_asset = constants.ZERO
    if asset_name in remaining_master_portfolio.content and asset_name not in forbidden_filling_assets:
        remaining_master_holding = remaining_master_portfolio.content[asset_name]
        # available = total - locked_funds
        remaining_total = remaining_master_holding[commons_constants.PORTFOLIO_TOTAL]
        remaining_available = remaining_master_holding[commons_constants.PORTFOLIO_AVAILABLE]
        allowed_missing_ratio_multiplier = constants.ONE - constants.SUB_PORTFOLIO_ALLOWED_MISSING_RATIO
        if remaining_total < locked_funds * allowed_missing_ratio_multiplier:
            # should never happen, log it in case it does
            commons_logging.get_logger(__name__).error(
                f"Unexpected missing locked {asset_name} funds in total portfolio {remaining_total=} {locked_funds=}"
            )
        # As orders are still open, their funds must be locked. Therefore, only consider available funds
        if remaining_available >= required_available_amount * allowed_missing_ratio_multiplier:
            if remaining_total < required_total_amount * allowed_missing_ratio_multiplier:
                # should never happen, log it in case it does
                commons_logging.get_logger(__name__).error(
                    f"Unexpected missing total {asset_name} value in portfolio: ensure order funds really locked"
                )
            sub_portfolio_total_amount = min(remaining_total, required_total_amount)
            # Do not use remaining_available or remaining_available here to avoid side effects due to locked fees
            # on some exchanges and not on others. Only compute from total holdings.
            # ex: coinbase locks 101 USDC to buy for 100 USDC + 1 USDC fee,
            # binance will just lock 100 and given less of the bought asset
            sub_portfolio_available_amount = sub_portfolio_total_amount - locked_funds
            # assets are available in master portfolio: reduce it from master
            if asset_name in resolved_content:
                resolved_content[asset_name][commons_constants.PORTFOLIO_TOTAL] += sub_portfolio_total_amount
                resolved_content[asset_name][commons_constants.PORTFOLIO_AVAILABLE] += sub_portfolio_available_amount
            else:
                resolved_content[asset_name] = {
                    commons_constants.PORTFOLIO_TOTAL: sub_portfolio_total_amount,
                    commons_constants.PORTFOLIO_AVAILABLE: sub_portfolio_available_amount,
                }
            remaining_master_portfolio.content[asset_name][commons_constants.PORTFOLIO_TOTAL] -= sub_portfolio_total_amount
            # don't make remaining available negative
            removed_portfolio_available_amount = min(remaining_available, sub_portfolio_available_amount)
            remaining_master_portfolio.content[asset_name][commons_constants.PORTFOLIO_AVAILABLE] -= removed_portfolio_available_amount
        else:
            # As orders are still open, their funds must be locked. Therefore, only consider available funds
            # Not enough assets in master portfolio
            usable_total = min(remaining_total, remaining_available + locked_funds)
            if asset_name in resolved_content:
                resolved_content[asset_name][commons_constants.PORTFOLIO_TOTAL] += usable_total
                resolved_content[asset_name][commons_constants.PORTFOLIO_AVAILABLE] += remaining_available
            else:
                resolved_content[asset_name] = {
                    commons_constants.PORTFOLIO_TOTAL: usable_total,
                    commons_constants.PORTFOLIO_AVAILABLE: remaining_available,
                }
            missing_amount_in_asset = abs(remaining_available - required_available_amount)
            remaining_master_portfolio.content[asset_name][commons_constants.PORTFOLIO_TOTAL] -= usable_total
            remaining_master_portfolio.content[asset_name][commons_constants.PORTFOLIO_AVAILABLE] -= remaining_available
    else:
        if locked_funds > constants.ZERO:
            # should never happen, log it in case it does
            commons_logging.get_logger(__name__).error(
                f"Unexpected missing {asset_name} value in portfolio but {locked_funds=}"
            )
        resolved_content[asset_name] = {
            commons_constants.PORTFOLIO_TOTAL: constants.ZERO,
            commons_constants.PORTFOLIO_AVAILABLE: constants.ZERO,
        }
        # asset not in master portfolio (anymore):
        missing_amount_in_asset = required_available_amount
    return missing_amount_in_asset


def _fill_missing_assets_from_allowed_filling_assets(
    asset_name, allowed_filling_assets, market_prices,
    remaining_master_portfolio, missing_amount_in_asset, resolved_content, funds_deltas, missing_funds
):
    # missing funds: try to get it from allowed assets
    for filling_asset, price in _iterate_filling_assets(
        asset_name, allowed_filling_assets, market_prices
    ):
        if filling_asset in remaining_master_portfolio.content and price != constants.ZERO:
            # use available funds only here to avoid taking funds locked in orders
            available_funds_in_filling_asset = remaining_master_portfolio.content[filling_asset][
                commons_constants.PORTFOLIO_AVAILABLE
            ]
            ideal_funds_to_add_in_filling_asset = missing_amount_in_asset * price
            if available_funds_in_filling_asset >= ideal_funds_to_add_in_filling_asset:
                # use a part of available filling asset to compensate missing amount in sub portfolio
                funds_to_add_in_filling_asset = ideal_funds_to_add_in_filling_asset
                taken_filling_asset = ideal_funds_to_add_in_filling_asset
                missing_amount_in_asset = constants.ZERO
            else:
                # use all available filling asset to compensate missing amount in sub portfolio
                funds_to_add_in_filling_asset = available_funds_in_filling_asset
                taken_filling_asset = available_funds_in_filling_asset
                missing_amount_in_asset = missing_amount_in_asset - (funds_to_add_in_filling_asset / price)
            if filling_asset in resolved_content:
                resolved_content[filling_asset][commons_constants.PORTFOLIO_TOTAL] += (
                    funds_to_add_in_filling_asset
                )
                resolved_content[filling_asset][commons_constants.PORTFOLIO_AVAILABLE] += (
                    funds_to_add_in_filling_asset
                )
            else:
                resolved_content[filling_asset] = {
                    commons_constants.PORTFOLIO_TOTAL: funds_to_add_in_filling_asset,
                    commons_constants.PORTFOLIO_AVAILABLE: funds_to_add_in_filling_asset,
                }
            if filling_asset in funds_deltas:
                funds_deltas[filling_asset][commons_constants.PORTFOLIO_TOTAL] += funds_to_add_in_filling_asset
                funds_deltas[filling_asset][commons_constants.PORTFOLIO_AVAILABLE] += funds_to_add_in_filling_asset
            elif funds_to_add_in_filling_asset != constants.ZERO:
                # only add delta when delta is not 0
                funds_deltas[filling_asset] = {
                    commons_constants.PORTFOLIO_TOTAL: funds_to_add_in_filling_asset,
                    commons_constants.PORTFOLIO_AVAILABLE: funds_to_add_in_filling_asset
                }
            remaining_master_portfolio.content[filling_asset][commons_constants.PORTFOLIO_AVAILABLE] -= (
                taken_filling_asset
            )
            remaining_master_portfolio.content[filling_asset][commons_constants.PORTFOLIO_TOTAL] -= (
                taken_filling_asset
            )
        if missing_amount_in_asset == constants.ZERO:
            return constants.ZERO
    if missing_amount_in_asset > constants.ZERO:
        # can't compensate for missing funds
        if asset_name in missing_funds:
            missing_funds[asset_name] += missing_amount_in_asset
        else:
            missing_funds[asset_name] = missing_amount_in_asset
    return missing_amount_in_asset


def _iterate_filling_assets(
    asset_name: str,
    allowed_filling_assets: list[str],
    tickers: dict[str, float],
):
    for allowed_filling_asset in allowed_filling_assets:
        symbol = symbol_util.merge_currencies(asset_name, allowed_filling_asset)
        if symbol in tickers:
            try:
                yield allowed_filling_asset, decimal.Decimal(str(tickers[symbol]))
            except decimal.DecimalException as err:
                commons_logging.get_logger(__name__).warning(
                    f"Error when reading {symbol} price: \"{tickers[symbol]}\": {err}"
                )
        else:
            reversed_symbol = symbol_util.merge_currencies(allowed_filling_asset, asset_name)
            if reversed_symbol in tickers and tickers[reversed_symbol]:
                yield allowed_filling_asset, constants.ONE / decimal.Decimal(str(tickers[reversed_symbol]))

def get_portfolio_filled_orders_deltas(
    previous_portfolio_content: dict[str, dict[str, decimal.Decimal]],
    updated_portfolio_content: dict[str, dict[str, decimal.Decimal]],
    filled_orders: list[order_import.Order]
) -> (dict[str, dict[str, decimal.Decimal]], dict[str, dict[str, decimal.Decimal]]):
    orders_asset_deltas, expected_fee_related_deltas, possible_fees_asset_deltas = get_assets_delta_from_orders(filled_orders)
    portfolios_asset_deltas = _get_assets_delta_from_portfolio(previous_portfolio_content, updated_portfolio_content)
    # return portfolio asset deltas that can approximately be explained by given orders
    orders_linked_deltas = {}
    ignored_deltas = {}
    for asset_name, holdings_delta in portfolios_asset_deltas.items():
        if asset_name not in orders_asset_deltas:
            # this delta is not due to these orders: skip it
            continue
        order_asset_delta = orders_asset_deltas[asset_name]
        holding_total = holdings_delta[commons_constants.PORTFOLIO_TOTAL]
        min_allowed_equivalent_total_holding = (
            holding_total * (constants.ONE - constants.SUB_PORTFOLIO_ALLOWED_DELTA_RATIO)
        )
        max_allowed_equivalent_total_holding = (
            holding_total * (constants.ONE + constants.SUB_PORTFOLIO_ALLOWED_DELTA_RATIO)
        )
        if (
            order_asset_delta * min_allowed_equivalent_total_holding < 0
            and (order_asset_delta + possible_fees_asset_deltas.get(asset_name, constants.ZERO))
                * min_allowed_equivalent_total_holding < 0
        ):
            # different sign: incompatible, this is unexpected
            ignored_deltas[asset_name] = holdings_delta
        elif (
            # approx same value
            abs(min_allowed_equivalent_total_holding)
            < abs(order_asset_delta)
            < abs(max_allowed_equivalent_total_holding)
        ):
            # similar delta (+/- fees)
            # this delta is due to these orders: add it
            orders_linked_deltas[asset_name] = holdings_delta
        elif asset_name in expected_fee_related_deltas and (
            abs(expected_fee_related_deltas[asset_name]) > abs(holdings_delta[commons_constants.PORTFOLIO_AVAILABLE])
        ):
            # paid fees are higher than holding delta: mostly paid fees, validate this delta
            orders_linked_deltas[asset_name] = holdings_delta
        elif (
            # try while taking expected and lower than expected fees into account
            asset_name in expected_fee_related_deltas and (
                any(
                    abs(min_allowed_equivalent_total_holding)
                    # fees bring back the order delta into the expected portfolio delta window
                    < abs(order_asset_delta + expected_fee)
                    < abs(max_allowed_equivalent_total_holding)
                    for expected_fee in (
                        # try with smaller fees in case user is paying less fees (when having large volume)
                        # test from 10% up to 100% fees
                        expected_fee_related_deltas[asset_name] * decimal.Decimal(multiplier / 10)
                        for multiplier in range(1, 11)
                    )
                )
            )
        ):
            # similar delta considering fees
            # this delta is due to these orders: add it
            orders_linked_deltas[asset_name] = holdings_delta
        elif abs(order_asset_delta) > abs(max_allowed_equivalent_total_holding):
            # last chance: try with potential fees, in case the expected fee currency was wrong
            if (
                # try while taking possible fees into account
                asset_name in possible_fees_asset_deltas and (
                    abs(min_allowed_equivalent_total_holding)
                    # fees bring back the order delta into the expected portfolio delta window
                    < abs(order_asset_delta + possible_fees_asset_deltas[asset_name])
                    < abs(max_allowed_equivalent_total_holding)
                )
            ):
                orders_linked_deltas[asset_name] = holdings_delta
            else:
                # too little in portfolio delta to be from those orders
                # As potential fees have already been taken into account, THIS IS UNEXPECTED.
                # Add it to ignored_deltas
                ignored_deltas[asset_name] = holdings_delta
        elif abs(min_allowed_equivalent_total_holding) > abs(order_asset_delta):
            # too much in portfolio delta: only take what is linked to the orders deltas
            # => updates both total and available
            # Should very rarely happen as it might reduce the total portfolio if done when unecessary
            commons_logging.get_logger(__name__).warning(
                f"Too large portfolio {asset_name} delta: {holdings_delta}, reducing to order delta: {order_asset_delta}"
            )
            orders_linked_deltas[asset_name] = {
                key: order_asset_delta
                for key in holdings_delta
            }
    for asset_name, order_delta in orders_asset_deltas.items():
        can_have_no_delta = (
            (order_delta == constants.ZERO)
            or (order_delta + possible_fees_asset_deltas.get(asset_name, constants.ZERO)) == constants.ZERO
            or (order_delta - possible_fees_asset_deltas.get(asset_name, constants.ZERO)) == constants.ZERO
        )
        if asset_name not in portfolios_asset_deltas and not can_have_no_delta:
            # asset not in portfolio delta, this is unexpected, register it in ignored deltas
            ignored_deltas[asset_name] = {
                commons_constants.PORTFOLIO_TOTAL: order_delta,
                commons_constants.PORTFOLIO_AVAILABLE: order_delta
            }
    return orders_linked_deltas, ignored_deltas


def _get_assets_delta_from_portfolio(
    previous_portfolio_content: dict,
    updated_portfolio_content: dict,
) ->  dict[str, dict[str, decimal.Decimal]]:
    asset_deltas = {}
    for asset_name in set(previous_portfolio_content).union(updated_portfolio_content):
        if previous_portfolio_content.get(asset_name) != updated_portfolio_content.get(asset_name):
            if asset_name not in previous_portfolio_content:
                # asset has been added
                asset_deltas[asset_name] = updated_portfolio_content[asset_name]
            elif asset_name not in updated_portfolio_content:
                # asset has been removed
                asset_deltas[asset_name] = {key: -val for key, val in previous_portfolio_content[asset_name].items()}
            else:
                # asset was already here
                asset_deltas[asset_name] = {}
                for key, updated_value in updated_portfolio_content[asset_name].items():
                    asset_deltas[asset_name][key] = updated_value - previous_portfolio_content[asset_name][key]
    return asset_deltas


def get_assets_delta_from_orders(orders: list[order_import.Order]) -> (
    dict[str, decimal.Decimal], dict[str, decimal.Decimal], dict[str, decimal.Decimal]
):
    asset_deltas = {}
    expected_fee_related_deltas = {}
    possible_fee_related_deltas = {}
    for order in orders:
        base, quote = symbol_util.parse_symbol(order.symbol).base_and_quote()
        # order "expected" related deltas
        added_unit_and_amount = (
            (base, order.origin_quantity)
            if order.side is enums.TradeOrderSide.BUY else (quote, order.total_cost)
        )
        removed_unit_and_amount = (
            (quote, order.total_cost)
            if order.side is enums.TradeOrderSide.BUY else (base, order.origin_quantity)
        )
        for unit_and_amount, multiplier in zip(
            (added_unit_and_amount, removed_unit_and_amount),
            (1, -1)
        ):
            if unit_and_amount[0] not in asset_deltas:
                asset_deltas[unit_and_amount[0]] = unit_and_amount[1] * multiplier
            else:
                asset_deltas[unit_and_amount[0]] += unit_and_amount[1] * multiplier
        # order "probable" related deltas (account for worse case fees)
        expected_forecasted_fees = order.get_computed_fee(use_origin_quantity_and_price=True)
        possible_forecasted_fees = _get_other_asset_forecasted_fees(order, expected_forecasted_fees)
        for fee_asset in (base, quote):
            for fee in (expected_forecasted_fees, possible_forecasted_fees):
                is_expected_fee = fee is expected_forecasted_fees
                if asset_amount := order_util.get_fees_for_currency(fee, fee_asset):
                    for delta_counter in (expected_fee_related_deltas, possible_fee_related_deltas):
                        if delta_counter is expected_fee_related_deltas and not is_expected_fee:
                            # when updating expected_fee_related_deltas, only account for expected fees
                            continue
                        if fee_asset not in delta_counter:
                            delta_counter[fee_asset] = -asset_amount
                        else:
                            delta_counter[fee_asset] += -asset_amount
    return asset_deltas, expected_fee_related_deltas, possible_fee_related_deltas

def _get_other_asset_forecasted_fees(order: order_import.Order, forecasted_fees: dict) -> dict:
    base, quote = symbol_util.parse_symbol(order.symbol).base_and_quote()
    other_fee = copy.deepcopy(forecasted_fees)
    if base_fee := order_util.get_fees_for_currency(forecasted_fees, base):
        other_fee[enums.FeePropertyColumns.CURRENCY.value] = quote
        other_fee[enums.FeePropertyColumns.COST.value] = base_fee * order.origin_price
    elif quote_fee := order_util.get_fees_for_currency(forecasted_fees, quote):
        other_fee[enums.FeePropertyColumns.CURRENCY.value] = base
        other_fee[enums.FeePropertyColumns.COST.value] = quote_fee / order.origin_price
    return other_fee
