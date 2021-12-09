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

import octobot_trading.errors as errors
import octobot_trading.modes.scripting_library.dsl as dsl
import octobot_trading.modes.scripting_library.orders.position_size.amount as amount
import octobot_trading.modes.scripting_library.data.reading.exchange_private_data as exchange_private_data
import octobot_commons.constants as commons_constants

from tests import event_loop
from tests.modes.scripting_library import null_context

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_get_amount(null_context):
    with pytest.raises(errors.InvalidArgumentError):
        await amount.get_amount(null_context, "-1")

    with pytest.raises(errors.InvalidArgumentError):
        await amount.get_amount(null_context, "1sdsqdq")

    with mock.patch.object(exchange_private_data, "adapt_amount_to_holdings",
                           mock.AsyncMock(return_value=decimal.Decimal(1))) as adapt_amount_to_holdings_mock:
        with mock.patch.object(dsl, "parse_quantity",
                               mock.Mock(return_value=(dsl.QuantityType.DELTA, decimal.Decimal(2)))) \
                as parse_quantity_mock:
            assert await amount.get_amount(null_context, "1", "buy") == decimal.Decimal(1)
            adapt_amount_to_holdings_mock.assert_called_once_with(null_context, decimal.Decimal(2), "buy")
            parse_quantity_mock.assert_called_once_with("1")
            adapt_amount_to_holdings_mock.reset_mock()

        with mock.patch.object(dsl, "parse_quantity",
                               mock.Mock(return_value=(dsl.QuantityType.PERCENT, decimal.Decimal(75)))) \
                as parse_quantity_mock, \
            mock.patch.object(exchange_private_data, "total_account_balance",
                              mock.AsyncMock(return_value=decimal.Decimal(2))) \
                as total_account_balance_mock:
            assert await amount.get_amount(null_context, "50", "buy") == decimal.Decimal(1)
            adapt_amount_to_holdings_mock.assert_called_once_with(null_context, decimal.Decimal("1.5"), "buy")
            parse_quantity_mock.assert_called_once_with("50")
            total_account_balance_mock.assert_called_once_with(null_context)
            adapt_amount_to_holdings_mock.reset_mock()

        with mock.patch.object(dsl, "parse_quantity",
                               mock.Mock(return_value=(dsl.QuantityType.AVAILABLE_PERCENT, decimal.Decimal(75)))) \
                as parse_quantity_mock, \
            mock.patch.object(exchange_private_data, "available_account_balance",
                               mock.AsyncMock(return_value=decimal.Decimal(2))) \
                as available_account_balance_mock:
            assert await amount.get_amount(null_context, "50", "buy") == decimal.Decimal(1)
            adapt_amount_to_holdings_mock.assert_called_once_with(null_context, decimal.Decimal("1.5"), "buy")
            parse_quantity_mock.assert_called_once_with("50")
            available_account_balance_mock.assert_called_once_with(null_context, "buy")
            adapt_amount_to_holdings_mock.reset_mock()

        with mock.patch.object(dsl, "parse_quantity",
                               mock.Mock(return_value=(dsl.QuantityType.POSITION_PERCENT, decimal.Decimal(75)))) \
                as parse_quantity_mock, \
            mock.patch.object(exchange_private_data, "open_position_size",
                              mock.Mock(return_value=decimal.Decimal(2))) \
                as open_position_size_mock:
            assert await amount.get_amount(null_context, "50", "buy") == decimal.Decimal(1)
            adapt_amount_to_holdings_mock.assert_called_once_with(null_context, decimal.Decimal("1.5"), "buy")
            parse_quantity_mock.assert_called_once_with("50")
            open_position_size_mock.assert_called_once_with(null_context, "buy",
                                                            amount_type=commons_constants.PORTFOLIO_AVAILABLE)
            adapt_amount_to_holdings_mock.reset_mock()
