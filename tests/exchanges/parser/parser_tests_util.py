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
from octobot_trading import exchanges
from octobot_trading.enums import (
    ExchangePositionCCXTColumns,
    FutureContractType,
)
import octobot_commons.tests.test_config as test_config


pytestmark = pytest.mark.asyncio


EXCHANGE_NAME = "binance"


def mock_get_pair_from_exchange(raw_symbol):
    return raw_symbol


def mock_get_contract_type(symbol):
    return FutureContractType.LINEAR_PERPETUAL


def mock_abstract_exchange():
    config = test_config.load_test_config()
    exchange = exchanges.FutureCCXTExchange(
        config, exchanges.ExchangeManager(config, EXCHANGE_NAME)
    )
    exchange.get_pair_from_exchange = mock_get_pair_from_exchange
    exchange.get_contract_type = mock_get_contract_type
#         # get_pair_from_exchange
    return exchange


async def check_open_and_closed(
    active_parser,
    raw_closed_records,
    parsed_closed_records,
    raw_open_records,
    parsed_open_records,
):
    just_parsed_closed_records = await active_parser(raw_closed_records)
    assert parsed_closed_records == just_parsed_closed_records
    just_parsed_open_records = await active_parser(raw_open_records)
    assert parsed_open_records == just_parsed_open_records


def set_raw_and_parsed_open_and_closed_by_key(
    key,
    value,
    parsed_open_records,
    parsed_closed_records,
    raw_key,
    raw_value,
    raw_open_records,
    raw_closed_records,
    set_to_info=False,
):
    set_parsed_open_and_closed_key(
        key=key,
        value=value,
        parsed_open_records=parsed_open_records,
        parsed_closed_records=parsed_closed_records,
    )
    set_raw_open_and_closed_key(
        key=raw_key,
        value=raw_value,
        raw_open_records=raw_open_records,
        raw_closed_records=raw_closed_records,
        set_to_info=set_to_info,
    )


def set_parsed_open_and_closed_key(
    key, value, parsed_open_records, parsed_closed_records
):
    parsed_open_records[0][key] = parsed_closed_records[0][key] = value


def set_raw_open_and_closed_key(
    key, value, raw_open_records, raw_closed_records, set_to_info=False
):
    if set_to_info:
        raw_open_records[0][ExchangePositionCCXTColumns.INFO.value][
            key
        ] = raw_closed_records[0][ExchangePositionCCXTColumns.INFO.value][key] = value
    else:
        raw_open_records[0][key] = raw_closed_records[0][key] = value


async def set_and_check_open_and_closed(
    active_parser,
    key,
    value,
    parsed_open_records,
    parsed_closed_records,
    raw_key,
    raw_value,
    raw_open_records,
    raw_closed_records,
    set_to_info=False,
):
    _parsed_open_records = parsed_open_records
    _parsed_closed_records = parsed_closed_records
    _raw_open_records = raw_open_records
    _raw_closed_records = raw_closed_records
    set_raw_and_parsed_open_and_closed_by_key(
        key=key,
        value=value,
        parsed_open_records=_parsed_open_records,
        parsed_closed_records=_parsed_closed_records,
        raw_key=raw_key,
        raw_value=raw_value,
        raw_open_records=_raw_open_records,
        raw_closed_records=_raw_closed_records,
        set_to_info=set_to_info,
    )
    await check_open_and_closed(
        active_parser=active_parser,
        parsed_closed_records=_parsed_closed_records,
        raw_closed_records=_raw_closed_records,
        parsed_open_records=_parsed_open_records,
        raw_open_records=_raw_open_records,
    )
