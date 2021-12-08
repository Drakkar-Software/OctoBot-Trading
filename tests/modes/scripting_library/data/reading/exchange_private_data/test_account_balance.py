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
import decimal

import octobot_trading.personal_data as trading_personal_data
import octobot_trading.modes.scripting_library.data.reading.exchange_private_data.account_balance as account_balance
import octobot_trading.enums as trading_enums
import octobot_trading.constants as trading_constants

from tests import event_loop
from tests.modes.scripting_library import null_context, mock_context
from tests.exchanges import backtesting_trader, backtesting_config, backtesting_exchange_manager, fake_backtesting


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_total_account_balance(mock_context):
    mock_context.exchange_manager.exchange_personal_data. \
        portfolio_manager.portfolio_value_holder.portfolio_current_value = decimal.Decimal(999)
    with mock.patch.object(trading_personal_data, "get_up_to_date_price", mock.AsyncMock(return_value=100)) \
            as get_up_to_date_price:
        assert await account_balance.total_account_balance(mock_context) == decimal.Decimal("9.99")
        get_up_to_date_price.assert_called_once_with(mock_context.exchange_manager, symbol=mock_context.symbol,
                                                     timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT)


async def test_available_account_balance(mock_context):
    ret_val = ("current_symbol_holding", "current_market_holding", "market_quantity", "current_price", "symbol_market")
    with mock.patch.object(trading_personal_data, "get_pre_order_data", mock.AsyncMock(return_value=ret_val)) \
         as get_pre_order_data_mock:
        assert "market_quantity" == await account_balance.available_account_balance(
            mock_context, side=trading_enums.TradeOrderSide.BUY.value)
        get_pre_order_data_mock.assert_called_once_with(mock_context.exchange_manager, symbol=mock_context.symbol,
                                                        timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT)
        assert "current_symbol_holding" == await account_balance.available_account_balance(
            mock_context, side=trading_enums.TradeOrderSide.SELL.value)


@pytest.mark.asyncio
async def test_adapt_amount_to_holdings(null_context):
    with mock.patch.object(account_balance, "available_account_balance",
                           mock.AsyncMock(return_value=decimal.Decimal(1))) as available_account_balance_mock:
        assert await account_balance.adapt_amount_to_holdings(null_context,
                                                              decimal.Decimal(0),
                                                              trading_enums.TradeOrderSide.SELL) == decimal.Decimal(0)
        available_account_balance_mock.assert_called_once_with(null_context, trading_enums.TradeOrderSide.SELL)
        assert await account_balance.adapt_amount_to_holdings(null_context,
                                                              decimal.Decimal(1),
                                                              trading_enums.TradeOrderSide.SELL) == decimal.Decimal(1)
        assert await account_balance.adapt_amount_to_holdings(null_context,
                                                              decimal.Decimal(2),
                                                              trading_enums.TradeOrderSide.SELL) == decimal.Decimal(1)
