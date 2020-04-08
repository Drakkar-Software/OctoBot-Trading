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
from octobot_commons.logging.logging_util import get_logger
from octobot_commons.symbol_util import split_symbol

from octobot_trading.channels.mode import ModeChannelConsumer
from octobot_trading.enums import ExchangeConstantsMarketStatusColumns as Ecmsc, EvaluatorStates


class AbstractTradingModeConsumer(ModeChannelConsumer):
    def __init__(self, trading_mode):
        super().__init__()
        self.trading_mode = trading_mode
        self.exchange_manager = trading_mode.exchange_manager

    def flush(self):
        self.trading_mode = None
        self.exchange_manager = None

    async def internal_callback(self, **kwargs):
        raise NotImplementedError("internal_callback is not implemented")

    # Can be overwritten
    async def can_create_order(self, symbol, state):
        currency, market = split_symbol(symbol)
        portfolio = self.exchange_manager.exchange_personal_data.portfolio_manager

        # get symbol min amount when creating order
        symbol_limit = self.exchange_manager.exchange.get_market_status(symbol)[Ecmsc.LIMITS.value]
        symbol_min_amount = symbol_limit[Ecmsc.LIMITS_AMOUNT.value][Ecmsc.LIMITS_AMOUNT_MIN.value]
        order_min_amount = symbol_limit[Ecmsc.LIMITS_COST.value][Ecmsc.LIMITS_COST_MIN.value]

        if symbol_min_amount is None:
            symbol_min_amount = 0

        # short cases => sell => need this currency
        if state == EvaluatorStates.VERY_SHORT or state == EvaluatorStates.SHORT:
            return portfolio.get_currency_portfolio(currency) > symbol_min_amount

        # long cases => buy => need money(aka other currency in the pair) to buy this currency
        elif state == EvaluatorStates.LONG or state == EvaluatorStates.VERY_LONG:
            return portfolio.get_currency_portfolio(market) > order_min_amount

        # other cases like neutral state or unfulfilled previous conditions
        return False

    async def get_holdings_ratio(self, currency):
        return await self.exchange_manager.exchange_personal_data.portfolio_manager.portfolio_profitability \
            .holdings_ratio(currency)

    def get_number_of_traded_assets(self):
        return len(self.exchange_manager.exchange_personal_data.portfolio_manager.portfolio_profitability
                   .origin_crypto_currencies_values)


def check_factor(min_val, max_val, factor):
    """
    Checks if factor is min_val < factor < max_val
    :param min_val:
    :param max_val:
    :param factor:
    :return:
    """
    if factor > max_val:
        return max_val
    if factor < min_val:
        return min_val
    return factor
