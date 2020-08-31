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
from octobot_trading.constants import OHLCV_CHANNEL, RECENT_TRADES_CHANNEL, TICKER_CHANNEL, ORDER_BOOK_CHANNEL, \
    KLINE_CHANNEL, MARK_PRICE_CHANNEL
from octobot_trading.producers.balance_updater import BalanceProfitabilityUpdater
from octobot_trading.producers.simulator.positions_updater_simulator import PositionsUpdaterSimulator
from octobot_trading.producers.simulator.orders_updater_simulator import OrdersUpdaterSimulator
from octobot_trading.producers.simulator.prices_updater_simulator import MarkPriceUpdaterSimulator
from octobot_trading.producers.simulator.ticker_updater_simulator import TickerUpdaterSimulator
from octobot_trading.producers.simulator.kline_updater_simulator import KlineUpdaterSimulator
from octobot_trading.producers.simulator.recent_trade_updater_simulator import RecentTradeUpdaterSimulator
from octobot_trading.producers.simulator.order_book_updater_simulator import OrderBookUpdaterSimulator
from octobot_trading.producers.simulator.ohlcv_updater_simulator import OHLCVUpdaterSimulator
from octobot_backtesting.enums import ExchangeDataTables

UNAUTHENTICATED_UPDATER_SIMULATOR_PRODUCERS = {
    OHLCV_CHANNEL: OHLCVUpdaterSimulator,
    ORDER_BOOK_CHANNEL: OrderBookUpdaterSimulator,
    RECENT_TRADES_CHANNEL: RecentTradeUpdaterSimulator,
    TICKER_CHANNEL: TickerUpdaterSimulator,
    KLINE_CHANNEL:  KlineUpdaterSimulator,
    MARK_PRICE_CHANNEL: MarkPriceUpdaterSimulator
}

AUTHENTICATED_UPDATER_SIMULATOR_PRODUCERS = [
    OrdersUpdaterSimulator,
    BalanceProfitabilityUpdater,
    PositionsUpdaterSimulator
]

# Required data to run updater (requires at least one per list)
SIMULATOR_PRODUCERS_TO_POSSIBLE_DATA_TYPE = {
    OHLCV_CHANNEL: [ExchangeDataTables.OHLCV],
    ORDER_BOOK_CHANNEL: [ExchangeDataTables.ORDER_BOOK],
    RECENT_TRADES_CHANNEL: [ExchangeDataTables.RECENT_TRADES, ExchangeDataTables.OHLCV],
    TICKER_CHANNEL: [ExchangeDataTables.TICKER, ExchangeDataTables.OHLCV],
    KLINE_CHANNEL: [ExchangeDataTables.KLINE]
}

# Required data to run real data updater (requires each per list)
SIMULATOR_PRODUCERS_TO_REAL_DATA_TYPE = {
    OHLCV_CHANNEL: [ExchangeDataTables.OHLCV],
    ORDER_BOOK_CHANNEL: [ExchangeDataTables.ORDER_BOOK],
    RECENT_TRADES_CHANNEL: [ExchangeDataTables.RECENT_TRADES],
    TICKER_CHANNEL: [ExchangeDataTables.TICKER],
    KLINE_CHANNEL: [ExchangeDataTables.KLINE],
}
