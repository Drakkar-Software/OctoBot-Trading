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
from octobot_trading.producers.balance_updater import BalanceProfitabilityUpdater
from octobot_trading.producers.simulator.positions_updater_simulator import PositionsUpdaterSimulator
from octobot_trading.producers.simulator.orders_updater_simulator import CloseOrdersUpdaterSimulator, \
    OpenOrdersUpdaterSimulator
from octobot_trading.producers.simulator.ticker_updater_simulator import TickerUpdaterSimulator
from octobot_trading.producers.simulator.kline_updater_simulator import KlineUpdaterSimulator
from octobot_trading.producers.simulator.recent_trade_updater_simulator import RecentTradeUpdaterSimulator
from octobot_trading.producers.simulator.order_book_updater_simulator import OrderBookUpdaterSimulator
from octobot_trading.producers.simulator.ohlcv_updater_simulator import OHLCVUpdaterSimulator

UNAUTHENTICATED_UPDATER_SIMULATOR_PRODUCERS = [OHLCVUpdaterSimulator, OrderBookUpdaterSimulator,
                                               RecentTradeUpdaterSimulator, TickerUpdaterSimulator,
                                               KlineUpdaterSimulator]

# TODO PositionsUpdaterSimulator
AUTHENTICATED_UPDATER_SIMULATOR_PRODUCERS = [CloseOrdersUpdaterSimulator, OpenOrdersUpdaterSimulator,
                                             BalanceProfitabilityUpdater]
