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

from octobot_trading.producers import abstract_mode_producer
from octobot_trading.producers import balance_updater
from octobot_trading.producers import funding_updater
from octobot_trading.producers import kline_updater
from octobot_trading.producers import ohlcv_updater
from octobot_trading.producers import order_book_updater
from octobot_trading.producers import orders_updater
from octobot_trading.producers import positions_updater
from octobot_trading.producers import prices_updater
from octobot_trading.producers import recent_trade_updater
from octobot_trading.producers import simulator
from octobot_trading.producers import ticker_updater
from octobot_trading.producers import trades_updater

from octobot_trading.producers.abstract_mode_producer import (AbstractTradingModeProducer, )
from octobot_trading.producers.balance_updater import (BalanceProfitabilityUpdater,
                                                       BalanceUpdater, )
from octobot_trading.producers.funding_updater import (FundingUpdater, )
from octobot_trading.producers.kline_updater import (KlineUpdater, )
from octobot_trading.producers.ohlcv_updater import (OHLCVUpdater, )
from octobot_trading.producers.order_book_updater import (OrderBookUpdater, )
from octobot_trading.producers.orders_updater import (OrdersUpdater, )
from octobot_trading.producers.positions_updater import (PositionsUpdater, )
from octobot_trading.producers.prices_updater import (MarkPriceUpdater, )
from octobot_trading.producers.recent_trade_updater import (RecentTradeUpdater, )
from octobot_trading.producers.simulator import (BalanceProfitabilityUpdaterSimulator,
                                                 BalanceUpdaterSimulator,
                                                 FundingUpdaterSimulator,
                                                 KlineUpdaterSimulator,
                                                 MarkPriceUpdaterSimulator,
                                                 OHLCVUpdaterSimulator,
                                                 OrderBookUpdaterSimulator,
                                                 OrdersUpdaterSimulator,
                                                 PositionsUpdaterSimulator,
                                                 RecentTradeUpdaterSimulator,
                                                 TickerUpdaterSimulator,
                                                 balance_updater_simulator,
                                                 funding_updater_simulator,
                                                 kline_updater_simulator,
                                                 ohlcv_updater_simulator,
                                                 order_book_updater_simulator,
                                                 orders_updater_simulator,
                                                 positions_updater_simulator,
                                                 prices_updater_simulator,
                                                 recent_trade_updater_simulator,
                                                 simulator_updater_utils,
                                                 ticker_updater_simulator,
                                                 SIMULATOR_PRODUCERS_TO_POSSIBLE_DATA_TYPE,
                                                 SIMULATOR_PRODUCERS_TO_REAL_DATA_TYPE,
                                                 stop_and_pause, )
from octobot_trading.producers.ticker_updater import (TickerUpdater, )
from octobot_trading.producers.trades_updater import (TradesUpdater, )


class MissingOrderException(Exception):
    def __init__(self, order_id):
        self.order_id = order_id


AUTHENTICATED_UPDATER_PRODUCERS = [BalanceUpdater, OrdersUpdater, TradesUpdater,
                                   PositionsUpdater, BalanceProfitabilityUpdater]

UNAUTHENTICATED_UPDATER_PRODUCERS = [OHLCVUpdater, OrderBookUpdater, RecentTradeUpdater, TickerUpdater,
                                     KlineUpdater, MarkPriceUpdater, FundingUpdater]

__all__ = ['MissingOrderException',
           'SIMULATOR_PRODUCERS_TO_REAL_DATA_TYPE', 'SIMULATOR_PRODUCERS_TO_POSSIBLE_DATA_TYPE',
           'AUTHENTICATED_UPDATER_PRODUCERS', 'UNAUTHENTICATED_UPDATER_PRODUCERS',
           'AbstractTradingModeProducer', 'BalanceProfitabilityUpdater',
           'BalanceProfitabilityUpdaterSimulator', 'BalanceUpdater',
           'BalanceUpdaterSimulator', 'FundingUpdater',
           'FundingUpdaterSimulator', 'KlineUpdater', 'KlineUpdaterSimulator',
           'MarkPriceUpdater', 'MarkPriceUpdaterSimulator', 'OHLCVUpdater',
           'OHLCVUpdaterSimulator', 'OrderBookUpdater',
           'OrderBookUpdaterSimulator', 'OrdersUpdater',
           'OrdersUpdaterSimulator', 'PositionsUpdater',
           'PositionsUpdaterSimulator', 'RecentTradeUpdater',
           'RecentTradeUpdaterSimulator', 'TickerUpdater',
           'TickerUpdaterSimulator', 'TradesUpdater', 'abstract_mode_producer',
           'balance_updater', 'balance_updater_simulator', 'funding_updater',
           'funding_updater_simulator', 'kline_updater',
           'kline_updater_simulator', 'ohlcv_updater',
           'ohlcv_updater_simulator', 'order_book_updater',
           'order_book_updater_simulator', 'orders_updater',
           'orders_updater_simulator', 'positions_updater',
           'positions_updater_simulator', 'prices_updater',
           'prices_updater_simulator', 'recent_trade_updater',
           'recent_trade_updater_simulator', 'simulator',
           'simulator_updater_utils', 'ticker_updater',
           'ticker_updater_simulator', 'trades_updater', 'stop_and_pause']
