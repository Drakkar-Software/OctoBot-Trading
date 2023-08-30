#  Drakkar-Software OctoBot
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

from tests import event_loop
import octobot_trading.personal_data as personal_data
import octobot_trading.enums as enums

from octobot_trading.api.exchange import cancel_ccxt_throttle_task

from tests.exchanges import simulated_exchange_manager, simulated_trader
from tests.personal_data.trades import create_executed_trade


SYMBOL = "BTC/USDT"


def test_aggregate_trades_by_exchange_order_id(simulated_trader):
    _, _, trader = simulated_trader
    t1 = create_executed_trade(
        trader, enums.TradeOrderSide.BUY, 1, decimal.Decimal(10), decimal.Decimal(1500), SYMBOL, _get_fees("BTC", 0.1)
    )
    t2 = create_executed_trade(
        trader, enums.TradeOrderSide.BUY, 3, decimal.Decimal(13), decimal.Decimal(1605), SYMBOL, _get_fees("BTC", 0.5)
    )
    t3 = create_executed_trade(
        trader, enums.TradeOrderSide.BUY, 7, decimal.Decimal(7), decimal.Decimal(1400), SYMBOL, _get_fees("BTC", 1.4)
    )
    aggregated = personal_data.aggregate_trades_by_exchange_order_id([t1, t2, t3])
    # aggregated all trades together as all of their exchange_order_id is None
    assert list(aggregated) == [None]
    assert aggregated[None].trader is trader
    assert aggregated[None].symbol == t1.symbol
    assert aggregated[None].side is t1.side
    assert aggregated[None].executed_price == decimal.Decimal("1522.166666666666666666666667")
    assert aggregated[None].executed_quantity == sum(t.executed_quantity for t in (t1, t2, t3))
    assert aggregated[None].total_cost == sum(t.total_cost for t in (t1, t2, t3))
    assert aggregated[None].fee[enums.FeePropertyColumns.COST.value] == \
       sum(t.fee[enums.FeePropertyColumns.COST.value] for t in (t1, t2, t3))
    assert aggregated[None].executed_time == 7

    # set exchange_order_id
    t1.exchange_order_id = "1"
    t2.exchange_order_id = "1"
    t3.exchange_order_id = "2"
    aggregated = personal_data.aggregate_trades_by_exchange_order_id([t1, t2, t3])
    # aggregated all trades together as all of their exchange_order_id is None
    assert list(aggregated) == ["1", "2"]
    assert aggregated["1"].trader is trader
    assert aggregated["1"].symbol == t1.symbol
    assert aggregated["1"].side is t1.side
    assert aggregated["1"].executed_price == decimal.Decimal("1559.347826086956521739130435")
    assert aggregated["1"].executed_quantity == sum(t.executed_quantity for t in (t1, t2))
    assert aggregated["1"].total_cost == sum(t.total_cost for t in (t1, t2))
    assert aggregated["1"].fee[enums.FeePropertyColumns.COST.value] == \
       sum(t.fee[enums.FeePropertyColumns.COST.value] for t in (t1, t2))
    assert aggregated["1"].executed_time == 3

    assert aggregated["2"].executed_price == decimal.Decimal(1400)
    assert aggregated["2"].executed_quantity == decimal.Decimal(7)
    assert aggregated["2"].total_cost == t3.total_cost
    assert aggregated["2"].fee == _get_fees("BTC", 1.4)
    assert aggregated["2"].executed_time == 7


def _get_fees(currency, value):
    return {
        enums.FeePropertyColumns.CURRENCY.value: currency,
        enums.FeePropertyColumns.COST.value: decimal.Decimal(str(value))
    }
