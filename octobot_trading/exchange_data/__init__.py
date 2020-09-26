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
from octobot_trading.exchange_data import candles_adapter
from octobot_trading.exchange_data import candles_manager
from octobot_trading.exchange_data import funding_manager
from octobot_trading.exchange_data import kline_manager
from octobot_trading.exchange_data import order_book_manager
from octobot_trading.exchange_data import price_events_manager
from octobot_trading.exchange_data import prices_manager
from octobot_trading.exchange_data import recent_trades_manager
from octobot_trading.exchange_data import ticker_manager

from octobot_trading.exchange_data.candles_adapter import (get_candle_as_list,
                                                           get_symbol_close_candles,
                                                           get_symbol_high_candles,
                                                           get_symbol_low_candles,
                                                           get_symbol_open_candles,
                                                           get_symbol_time_candles,
                                                           get_symbol_volume_candles,)
from octobot_trading.exchange_data.candles_manager import (CandlesManager,)
from octobot_trading.exchange_data.funding_manager import (FundingManager,)
from octobot_trading.exchange_data.kline_manager import (KlineManager,)
from octobot_trading.exchange_data.order_book_manager import (INVALID_PARSED_VALUE,
                                                              ORDER_ID_NOT_FOUND,
                                                              OrderBookManager,)
from octobot_trading.exchange_data.price_events_manager import (PriceEventsManager,)
from octobot_trading.exchange_data.prices_manager import (PricesManager,
                                                          calculate_mark_price_from_recent_trade_prices,)
from octobot_trading.exchange_data.recent_trades_manager import (RecentTradesManager,)
from octobot_trading.exchange_data.ticker_manager import (TickerManager,)

__all__ = ['CandlesManager', 'FundingManager', 'INVALID_PARSED_VALUE',
           'KlineManager', 'ORDER_ID_NOT_FOUND', 'OrderBookManager',
           'PriceEventsManager', 'PricesManager', 'RecentTradesManager',
           'TickerManager', 'calculate_mark_price_from_recent_trade_prices',
           'candles_adapter', 'candles_manager', 'funding_manager',
           'get_candle_as_list', 'get_symbol_close_candles',
           'get_symbol_high_candles', 'get_symbol_low_candles',
           'get_symbol_open_candles', 'get_symbol_time_candles',
           'get_symbol_volume_candles', 'kline_manager', 'order_book_manager',
           'price_events_manager', 'prices_manager', 'recent_trades_manager',
           'ticker_manager']
