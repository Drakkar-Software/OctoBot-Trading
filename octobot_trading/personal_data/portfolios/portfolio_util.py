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
import decimal
import octobot_trading.personal_data.portfolios.asset as asset
import octobot_trading.constants as constants
import octobot_trading.enums as enums
import octobot_commons.constants as commons_constants
import octobot_commons.logging as commons_logging
import octobot_commons.symbol_util as symbol_util
import numpy as numpy


def parse_decimal_portfolio(portfolio):
    decimal_portfolio = {}
    for symbol, symbol_balance in portfolio.items():
        if isinstance(symbol_balance, dict):
            decimal_portfolio[symbol] = {}
            portfolio_to_fill = decimal_portfolio[symbol]
            for balance_type, balance_val in symbol_balance.items():
                if isinstance(balance_val, (int, float, decimal.Decimal)):
                    portfolio_to_fill[balance_type] = decimal.Decimal(str(balance_val))
    return decimal_portfolio


def parse_decimal_config_portfolio(portfolio):
    return {
        symbol: decimal.Decimal(str(symbol_balance))
        for symbol, symbol_balance in portfolio.items()
    }


def portfolio_to_float(portfolio):
    float_portfolio = {}
    for symbol, symbol_balance in portfolio.items():
        if isinstance(symbol_balance, asset.Asset):
            float_portfolio[symbol] = {
                commons_constants.PORTFOLIO_AVAILABLE: float(symbol_balance.available),
                commons_constants.PORTFOLIO_TOTAL: float(symbol_balance.total)
            }
    return float_portfolio


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
                value_currency = symbol_util.split_symbol(draw_down_pair)[0]
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
            commons_logging.get_logger(__name__).exception(e, True, f"Error when computing draw down: {e}")
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
