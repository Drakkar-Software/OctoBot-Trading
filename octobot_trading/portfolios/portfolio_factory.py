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
from octobot_trading.portfolios.types.future_portfolio import FuturePortfolio
from octobot_trading.portfolios.types.margin_portfolio import MarginPortfolio
from octobot_trading.portfolios.types.spot_portfolio import SpotPortfolio


def create_portfolio_from_exchange_manager(exchange_manager):
    """
    Create a portfolio from an exchange manager
    :param exchange_manager: the exchange manager related to the new portfolio instance
    :return: the created portfolio instance
    """
    if exchange_manager.is_future:
        return FuturePortfolio(exchange_manager.get_exchange_name(), exchange_manager.trader.simulate)
    if exchange_manager.is_margin:
        return MarginPortfolio(exchange_manager.get_exchange_name(), exchange_manager.trader.simulate)
    return SpotPortfolio(exchange_manager.get_exchange_name(), exchange_manager.trader.simulate)
