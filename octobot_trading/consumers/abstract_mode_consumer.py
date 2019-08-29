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

from copy import deepcopy

from octobot_commons.constants import PORTFOLIO_TOTAL
from octobot_commons.logging.logging_util import get_logger
from octobot_commons.symbol_util import split_symbol

from octobot_trading.channels.exchange_channel import ExchangeChannelInternalConsumer
from octobot_trading.constants import ORDER_CREATION_LAST_TRADES_TO_USE
from octobot_trading.data.portfolio import Portfolio
from octobot_trading.data.sub_portfolio import SubPortfolio
from octobot_trading.enums import ExchangeConstantsMarketStatusColumns as Ecmsc, EvaluatorStates
from octobot_trading.util.initializable import Initializable


class AbstractTradingModeConsumer(ExchangeChannelInternalConsumer):
    def __init__(self, trading_mode):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.trading_mode = trading_mode

    async def perform(self, eval_note, symbol, exchange_manager, trader, portfolio, state):
        raise NotImplementedError("perform not implemented")

    @staticmethod
    async def get_holdings_ratio(trader, portfolio, currency):
        pf_copy = deepcopy(portfolio.get_portfolio())
        pf_value = await trader.get_trades_manager().update_portfolio_current_value(pf_copy)
        currency_holdings = Portfolio.get_currency_from_given_portfolio(pf_copy, currency,
                                                                        portfolio_type=PORTFOLIO_TOTAL)
        currency_value = await trader.get_trades_manager().evaluate_value(currency, currency_holdings)
        return currency_value / pf_value if pf_value else 0

    @staticmethod
    def get_number_of_traded_assets(trader):
        return len(trader.get_trades_manager().origin_crypto_currencies_values)

    @staticmethod
    # Can be overwritten
    async def can_create_order(symbol, exchange, state, portfolio):
        currency, market = split_symbol(symbol)

        # get symbol min amount when creating order
        symbol_limit = exchange.get_market_status(symbol)[Ecmsc.LIMITS.value]
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

    @staticmethod
    async def get_pre_order_data(exchange, symbol, portfolio):
        last_prices = await exchange.execute_request_with_retry(exchange.get_recent_trades(symbol))

        used_last_prices = last_prices[-ORDER_CREATION_LAST_TRADES_TO_USE:]  # TODO ticker

        reference_sum = sum([float(last_price["price"]) for last_price in used_last_prices])

        reference = reference_sum / len(used_last_prices)

        currency, market = split_symbol(symbol)

        current_symbol_holding = portfolio.get_currency_portfolio(currency)
        current_market_quantity = portfolio.get_currency_portfolio(market)

        market_quantity = current_market_quantity / reference

        price = reference
        symbol_market = exchange.get_market_status(symbol, with_fixer=False)

        return current_symbol_holding, current_market_quantity, market_quantity, price, symbol_market


class AbstractTradingModeConsumerWithBot(AbstractTradingModeConsumer, Initializable):
    def __init__(self, callback, trading_mode, trader, sub_portfolio_percent):
        AbstractTradingModeConsumer.__init__(self, callback, trading_mode)
        Initializable.__init__(self)
        self.trader = trader
        self.parent_portfolio = self.trader.get_portfolio()
        self.sub_portfolio = SubPortfolio(self.trading_mode.config, self.trader, self.parent_portfolio,
                                          sub_portfolio_percent)

    async def initialize_impl(self):
        await self.sub_portfolio.initialize()

    def create_new_order(self, eval_note, symbol, exchange, trader, portfolio, state):
        raise NotImplementedError("create_new_order not implemented")

    # Can be overwritten
    async def can_create_order(self, symbol, exchange, state, portfolio):
        return await super().can_create_order(symbol, exchange, state, self.get_portfolio())

    # force portfolio update
    def get_portfolio(self, force_update=False):
        if force_update:
            self.sub_portfolio.update_from_parent()
        return self.sub_portfolio
