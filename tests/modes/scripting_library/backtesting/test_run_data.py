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
import pytest
import mock

import octobot_trading.modes.scripting_library.backtesting.run_data as run_data
import octobot_trading.enums as trading_enums
import octobot_commons.enums as commons_enums

from tests import event_loop
from tests.modes.scripting_library.backtesting.data_store import default_price_data, default_trades_data, \
    default_portfolio_data, default_portfolio_historical_value, default_pnl_historical_value

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_plot_historical_portfolio_value(default_price_data, default_trades_data, default_portfolio_data,
                                               default_portfolio_historical_value):
    expected_time_data = [candle[commons_enums.PriceIndexes.IND_PRICE_TIME.value]
                          for candle in default_price_data["BTC/USDT"]]
    await _test_historical_portfolio_values(default_price_data, default_trades_data, default_portfolio_data,
                                            expected_time_data, default_portfolio_historical_value)


async def test_get_historical_pnl(default_price_data, default_trades_data, default_pnl_historical_value):
    # expected_time_data start at the 1st time data with a default_pnl_historical_value at 0
    expected_time_data = [default_price_data["BTC/USDT"][0][commons_enums.PriceIndexes.IND_PRICE_TIME.value]] + \
                         [trade[trading_enums.PlotAttributes.X.value]
                          for trade in default_trades_data["BTC/USDT"]
                          if trade[trading_enums.PlotAttributes.SIDE.value] == trading_enums.TradeOrderSide.SELL.value]
    await _test_historical_pnl_values(default_price_data, default_trades_data, False, False,
                                      expected_time_data, default_pnl_historical_value)

    cumulative_pnl_historical_value = [default_pnl_historical_value[0]]
    for value in default_pnl_historical_value[1:]:
        cumulative_pnl_historical_value.append(cumulative_pnl_historical_value[-1] + value)
    await _test_historical_pnl_values(default_price_data, default_trades_data, True, False,
                                      expected_time_data, cumulative_pnl_historical_value)

    expected_time_data = [i for i in range(len(cumulative_pnl_historical_value))]
    await _test_historical_pnl_values(default_price_data, default_trades_data, True, True,
                                      expected_time_data, cumulative_pnl_historical_value)


def test_total_paid_fees(default_trades_data):
    usdt_fees = sum(trade[trading_enums.DBTables.FEES_AMOUNT.value]
                    for trade in default_trades_data["BTC/USDT"]
                    if trade[trading_enums.DBTables.FEES_CURRENCY.value] == "USDT")
    btc_fees_in_usdt = sum(trade[trading_enums.DBTables.FEES_AMOUNT.value] * trade[trading_enums.PlotAttributes.Y.value]
                           for trade in default_trades_data["BTC/USDT"]
                           if trade[trading_enums.DBTables.FEES_CURRENCY.value] == "BTC")
    assert round(run_data.total_paid_fees(default_trades_data["BTC/USDT"]), 15) == \
           round(usdt_fees + btc_fees_in_usdt, 15)


async def _test_historical_portfolio_values(price_data, trades_data, portfolio_data, expected_time_data, expected_value_data):
    plotted_element = mock.Mock()
    with mock.patch.object(run_data, "_load_historical_values",
                           mock.AsyncMock(return_value=(price_data, trades_data, portfolio_data))) \
            as _load_historical_values_mock:
        await run_data.plot_historical_portfolio_value("meta_database", plotted_element,
                                                       exchange="exchange", own_yaxis=True)
        _load_historical_values_mock.assert_called_once_with("meta_database", "exchange")
        plotted_element.plot.assert_called_once_with(
            kind="scatter",
            x=expected_time_data,
            y=expected_value_data,
            title="Portfolio value",
            own_yaxis=True
        )


async def _test_historical_pnl_values(price_data, trades_data, cumulative, x_as_trade_count,
                                      expected_time_data, expected_value_data):
    plotted_element = mock.Mock()
    with mock.patch.object(run_data, "_load_historical_values",
                           mock.AsyncMock(return_value=(price_data, trades_data, None))) \
            as _load_historical_values_mock:
        await run_data._get_historical_pnl("meta_database", plotted_element, cumulative,
                                           exchange="exchange", x_as_trade_count=x_as_trade_count, own_yaxis=True)
        _load_historical_values_mock.assert_called_once_with("meta_database", "exchange")
        plotted_element.plot.assert_called_once_with(
            kind="scatter",
            x=expected_time_data,
            y=expected_value_data,
            x_type="tick0" if x_as_trade_count else "date",
            title="Cumulative P&L" if cumulative else "P&L per trade",
            own_yaxis=True
        )
