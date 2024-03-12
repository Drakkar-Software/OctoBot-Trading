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

import octobot_commons.symbols as commons_symbols
import octobot_trading.errors as errors
import octobot_trading.constants as constants
import octobot_trading.personal_data as trading_personal_data
import octobot_trading.modes.script_keywords as script_keywords
import octobot_trading.modes.script_keywords.dsl as dsl
import octobot_trading.modes.script_keywords.basic_keywords.account_balance as account_balance

from tests import event_loop
from tests.modes.script_keywords import null_context

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_get_amount_from_input_amount(null_context):
    with pytest.raises(errors.InvalidArgumentError):
        await script_keywords.get_amount_from_input_amount(null_context, "-1")

    with pytest.raises(errors.InvalidArgumentError):
        await script_keywords.get_amount_from_input_amount(null_context, "1sdsqdq")

    with pytest.raises(NotImplementedError):
        await script_keywords.get_amount_from_input_amount(null_context,
                                                           f"1{script_keywords.QuantityType.POSITION_PERCENT.value}")

    with mock.patch.object(account_balance, "adapt_amount_to_holdings",
                           mock.AsyncMock(return_value=decimal.Decimal(1))) as adapt_amount_to_holdings_mock:
        for quantity_delta in (script_keywords.QuantityType.DELTA, script_keywords.QuantityType.DELTA_BASE):
            with mock.patch.object(dsl, "parse_quantity",
                                   mock.Mock(return_value=(quantity_delta, decimal.Decimal(2)))) \
                    as parse_quantity_mock:
                assert await script_keywords.get_amount_from_input_amount(null_context, "1", "buy") \
                       == decimal.Decimal(1)
                adapt_amount_to_holdings_mock.assert_called_once_with(null_context, decimal.Decimal(2), "buy",
                                                                      False, True, False, target_price=None)
                parse_quantity_mock.assert_called_once_with("1")
                adapt_amount_to_holdings_mock.reset_mock()

        with mock.patch.object(dsl, "parse_quantity",
                               mock.Mock(return_value=(script_keywords.QuantityType.DELTA_QUOTE, decimal.Decimal(2)))) \
                as parse_quantity_mock:
            with mock.patch.object(trading_personal_data, "get_up_to_date_price",
                                   mock.AsyncMock(return_value=decimal.Decimal(100))) \
                    as get_up_to_date_price_mock:
                assert await script_keywords.get_amount_from_input_amount(null_context, "1", "buy") == decimal.Decimal(1)
                get_up_to_date_price_mock.assert_awaited_with(
                    null_context.exchange_manager,
                    symbol=null_context.symbol,
                    timeout=constants.ORDER_DATA_FETCHING_TIMEOUT
                )
                # without target_price
                adapt_amount_to_holdings_mock.assert_called_once_with(
                    null_context, decimal.Decimal(2) / decimal.Decimal(100), "buy",
                    False, True, False, target_price=None
                )
                parse_quantity_mock.assert_called_once_with("1")
                adapt_amount_to_holdings_mock.reset_mock()
                parse_quantity_mock.reset_mock()
                get_up_to_date_price_mock.reset_mock()
                # with target_price
                assert await script_keywords.get_amount_from_input_amount(
                    null_context, "1", "buy", target_price=decimal.Decimal(23)
                ) == decimal.Decimal(1)
                get_up_to_date_price_mock.assert_not_called()
                adapt_amount_to_holdings_mock.assert_called_once_with(
                    null_context, decimal.Decimal(2) / decimal.Decimal(23), "buy",
                    False, True, False, target_price=decimal.Decimal(23)
                )
                parse_quantity_mock.assert_called_once_with("1")
                adapt_amount_to_holdings_mock.reset_mock()

        with mock.patch.object(dsl, "parse_quantity",
                               mock.Mock(return_value=(script_keywords.QuantityType.PERCENT, decimal.Decimal(75)))) \
                as parse_quantity_mock, \
                mock.patch.object(account_balance, "available_account_balance",
                                  mock.AsyncMock(return_value=decimal.Decimal(2))) \
                as available_account_balance_mock:
            assert await script_keywords.get_amount_from_input_amount(null_context, "50", "buy", use_total_holding=True,
                                                                      reduce_only=False,
                                                                      is_stop_order=True,
                                                                      target_price=constants.ZERO) == decimal.Decimal(1)
            adapt_amount_to_holdings_mock.assert_called_once_with(null_context, decimal.Decimal("1.5"), "buy",
                                                                  True, False, True, target_price=constants.ZERO)
            parse_quantity_mock.assert_called_once_with("50")
            available_account_balance_mock.assert_called_once_with(null_context, "buy",
                                                                   use_total_holding=True, reduce_only=False)
            adapt_amount_to_holdings_mock.reset_mock()

        with mock.patch.object(dsl, "parse_quantity",
                               mock.Mock(return_value=(
                                       script_keywords.QuantityType.AVAILABLE_PERCENT, decimal.Decimal(75)))) \
                as parse_quantity_mock, \
                mock.patch.object(account_balance, "available_account_balance",
                                  mock.AsyncMock(return_value=decimal.Decimal(2))) \
                as available_account_balance_mock:
            assert await script_keywords.get_amount_from_input_amount(null_context, "50", "buy") == decimal.Decimal(1)
            adapt_amount_to_holdings_mock.assert_called_once_with(null_context, decimal.Decimal("1.5"), "buy",
                                                                  False, True, False, target_price=None)
            parse_quantity_mock.assert_called_once_with("50")
            available_account_balance_mock.assert_called_once_with(null_context, "buy",
                                                                   use_total_holding=False, reduce_only=True)
            adapt_amount_to_holdings_mock.reset_mock()

        with mock.patch.object(dsl, "parse_quantity",
                               mock.Mock(return_value=(
                                       script_keywords.QuantityType.CURRENT_SYMBOL_ASSETS_PERCENT, decimal.Decimal(75)))) \
                as parse_quantity_mock, \
                mock.patch.object(account_balance, "get_holdings_value",
                                  mock.Mock(return_value=decimal.Decimal(2))) \
                as get_holdings_value_mock:
            null_context.symbol = None
            with pytest.raises(errors.InvalidArgumentError):
                # context.symbol is None
                assert await script_keywords.get_amount_from_input_amount(null_context, "50", "buy") == decimal.Decimal(
                    1)
            parse_quantity_mock.reset_mock()
            null_context.symbol = "BTC/USDT"

            assert await script_keywords.get_amount_from_input_amount(null_context, "50", "buy") == decimal.Decimal(1)
            adapt_amount_to_holdings_mock.assert_called_once_with(null_context, decimal.Decimal("1.5"), "buy",
                                                                  False, True, False, target_price=None)
            parse_quantity_mock.assert_called_once_with("50")
            get_holdings_value_mock.assert_called_once_with(null_context, ("BTC", "USDT"), "BTC")
            adapt_amount_to_holdings_mock.reset_mock()

        with mock.patch.object(dsl, "parse_quantity",
                               mock.Mock(return_value=(
                                       script_keywords.QuantityType.TRADED_SYMBOLS_ASSETS_PERCENT, decimal.Decimal(75)))) \
                as parse_quantity_mock, \
                mock.patch.object(account_balance, "get_holdings_value",
                                  mock.Mock(return_value=decimal.Decimal(10))) \
                as get_holdings_value_mock:
            null_context.symbol = None
            with pytest.raises(errors.InvalidArgumentError):
                # context.symbol is None
                assert await script_keywords.get_amount_from_input_amount(null_context, "50", "buy") == decimal.Decimal(
                    1)
            parse_quantity_mock.reset_mock()
            null_context.symbol = "BTC/USDT"
            null_context.exchange_manager = mock.Mock(
                exchange_config=mock.Mock(
                    traded_symbols=[
                        commons_symbols.parse_symbol("BTC/USDT"),
                        commons_symbols.parse_symbol("ETH/BTC"),
                        commons_symbols.parse_symbol("SOL/USDT"),
                    ]
                )
            )

            assert await script_keywords.get_amount_from_input_amount(null_context, "50", "buy") == decimal.Decimal(1)
            adapt_amount_to_holdings_mock.assert_called_once_with(null_context, decimal.Decimal("7.5"), "buy",
                                                                  False, True, False, target_price=None)
            parse_quantity_mock.assert_called_once_with("50")
            get_holdings_value_mock.assert_called_once_with(null_context, {'BTC', 'ETH', 'SOL', 'USDT'}, "BTC")
            adapt_amount_to_holdings_mock.reset_mock()
