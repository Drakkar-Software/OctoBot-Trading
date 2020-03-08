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

from octobot_trading.constants import CONFIG_SIMULATOR, \
    CONFIG_STARTING_PORTFOLIO, CURRENT_PORTFOLIO_STRING
from octobot_trading.data.margin_portfolio import MarginPortfolio
from octobot_trading.data.portfolio import Portfolio
from octobot_trading.data.portfolio_profitability import PortfolioProfitabilty
from octobot_trading.util.initializable import Initializable


class PortfolioManager(Initializable):
    def __init__(self, config, trader, exchange_manager):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.config, self.trader, self.exchange_manager = config, trader, exchange_manager

        self.portfolio = None
        self.portfolio_profitability = None
        self.reference_market = None

    async def initialize_impl(self):
        await self.__reset_portfolio()

    async def __reset_portfolio(self):
        if self.exchange_manager.is_margin:
            self.portfolio = MarginPortfolio(self.exchange_manager.get_exchange_name(), self.trader.simulate)
        else:
            self.portfolio = Portfolio(self.exchange_manager.get_exchange_name(), self.trader.simulate)
        await self.__load_portfolio()

        self.portfolio_profitability = PortfolioProfitabilty(self.config, self.trader, self, self.exchange_manager)
        self.reference_market = self.portfolio_profitability.reference_market

    async def handle_balance_update(self, balance) -> bool:
        if self.trader.is_enabled:
            return await self.portfolio.update_portfolio_from_balance(balance)
        return False

    async def handle_balance_update_from_order(self, order):
        if self.trader.is_enabled and self.trader.simulate:
            await self.portfolio.update_portfolio_from_order(order)
            return True
        return False

    # Load simulated portfolio from config if required
    async def __load_portfolio(self):
        if self.trader.is_enabled:
            if self.trader.simulate:
                await self.__set_starting_simulated_portfolio()
            self.logger.info(f"{CURRENT_PORTFOLIO_STRING} {self.portfolio.portfolio}")

    async def __set_starting_simulated_portfolio(self):
        # load new portfolio from config settings
        portfolio_amount_dict = self.config[CONFIG_SIMULATOR][CONFIG_STARTING_PORTFOLIO]

        try:
            await self.handle_balance_update(self.portfolio.get_portfolio_from_amount_dict(portfolio_amount_dict))
        except Exception as e:
            self.logger.exception(e, True, f"Error when loading trading history, will reset history. ({e})")
            self.trader.get_previous_state_manager.reset_trading_history()
            await self.handle_balance_update(self.portfolio.get_portfolio_from_amount_dict(
                self.config[CONFIG_SIMULATOR][CONFIG_STARTING_PORTFOLIO]))
