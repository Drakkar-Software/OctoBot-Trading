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
import decimal
import pytest
import mock
from octobot_trading.enums import (
    FutureContractType,
    PositionMode,
    PositionSide,
    PositionStatus,
    TraderPositionType,
    ExchangeConstantsPositionColumns as PositionCols,
)
import octobot_trading.exchanges.parser as parser

pytestmark = pytest.mark.asyncio


@pytest.fixture
def exchange():
    exchange = None  
    # todo required:
    # logger
    # get_kline
    # connector.get_exchange_current_time
    # get_pair_from_exchange
    # get_kline_price
    # get_contract_type
    return exchange


@pytest.fixture
def positions_parser(exchange):
    return parser.PositionsParser(exchange=exchange)


@pytest.fixture
def raw_closed_positions():
    return {
        "info": {
            "user_id": "285169",
            "symbol": "10000NFTUSDT",
            "side": "None",
            "size": "0",
            "position_value": "0",
            "entry_price": "0",
            "liq_price": "0",
            "bust_price": "0",
            "leverage": "5",
            "auto_add_margin": "0",
            "is_isolated": False,
            "position_margin": "0",
            "occ_closing_fee": "0",
            "realised_pnl": "5.73893937",
            "cum_realised_pnl": "-12.12747167",
            "free_qty": "0",
            "tp_sl_mode": "Partial",
            "unrealised_pnl": "0",
            "deleverage_indicator": "0",
            "risk_id": "1",
            "stop_loss": "0",
            "take_profit": "0",
            "trailing_stop": "0",
            "position_idx": "0",
            "mode": "MergedSingle",
            "hedged": False,
        },
        "id": None,
        "symbol": "10000NFT/USDT:USDT",
        "timestamp": 1668494270,
        "datetime": None,
        "initialMargin": None,
        "initialMarginPercentage": None,
        "maintenanceMargin": None,
        "maintenanceMarginPercentage": None,
        "entryPrice": None,
        "notional": 0.0,
        "leverage": 5.0,
        "unrealizedPnl": None,
        "contracts": 0.0,
        "contractSize": 1.0,
        "marginRatio": None,
        "liquidationPrice": None,
        "markPrice": None,
        "collateral": 0.0,
        "marginMode": "cross",
        "side": "short",
        "percentage": None,
    }


@pytest.fixture
def raw_open_positions():
    return {
        "info": {
            "user_id": "285169",
            "symbol": "BTCUSDT",
            "side": "Buy",
            "size": "0.01",
            "position_value": "167.96968928",
            "entry_price": "16796.96892692",
            "liq_price": "13522",
            "bust_price": "13438",
            "leverage": "5",
            "auto_add_margin": "0",
            "is_isolated": True,
            "position_margin": "33.5939353",
            "occ_closing_fee": "0.080628",
            "realised_pnl": "-5.73893937",
            "cum_realised_pnl": "-12.12747167",
            "free_qty": "-0.01",
            "tp_sl_mode": "Partial",
            "unrealised_pnl": "2.50941072",
            "deleverage_indicator": "2",
            "risk_id": "1",
            "stop_loss": "0",
            "take_profit": "0",
            "trailing_stop": "0",
            "position_idx": "0",
            "mode": "MergedSingle",
            "hedged": False,
        },
        "id": None,
        "symbol": "BTC/USDT:USDT",
        "timestamp": 1668494270,
        "datetime": None,
        "initialMargin": 33.59393785384,
        "initialMarginPercentage": 0.19999999998714055,
        "maintenanceMargin": None,
        "maintenanceMarginPercentage": None,
        "entryPrice": 16796.96892692,
        "notional": 167.96968928,
        "leverage": 5.0,
        "unrealizedPnl": 2.50941072,
        "contracts": 0.01,
        "contractSize": 1.0,
        "marginRatio": None,
        "liquidationPrice": 13522.0,
        "markPrice": None,
        "collateral": 33.5939353,
        "marginMode": "isolated",
        "side": "long",
        "percentage": 7.469832000398127,
    }


@pytest.fixture
def parsed_closed_positions():
    return [
        {
            "symbol": "10000NFT/USDT:USDT",
            "original_side": "short",
            "position_mode": PositionMode.ONE_WAY,
            "status": PositionStatus.CLOSED,
            "side": PositionSide.BOTH,
            "size": decimal.Decimal("0"),
            "contract_type": FutureContractType.LINEAR_PERPETUAL,
            "margin_type": TraderPositionType.CROSS,
            "leverage": decimal.Decimal("5.0"),
            "realised_pnl": decimal.Decimal("5.73893937"),
        }
    ]


@pytest.fixture
def parsed_open_positions():
    return [
        {
            "symbol": "BTC/USDT:USDT",
            "original_side": "long",
            "position_mode": PositionMode.ONE_WAY,
            "side": PositionSide.BOTH,
            "size": decimal.Decimal("0.01"),
            "contract_type": FutureContractType.LINEAR_PERPETUAL,
            "margin_type": TraderPositionType.ISOLATED,
            "leverage": decimal.Decimal("5.0"),
            "realised_pnl": decimal.Decimal("-5.73893937"),
            "quantity": decimal.Decimal("1.0"),
            "status": PositionStatus.OPEN,
            "timestamp": 1668494270,
            "collateral": decimal.Decimal("33.5939353"),
            "notional": decimal.Decimal("167.96968928"),
        }
    ]


def test_parse_default_closed_position(
    positions_parser, raw_closed_positions, parsed_closed_positions
):
    assert check_if_dicts_match(
        parsed_closed_positions, positions_parser.parse_positions(raw_closed_positions)
    )


def test_parse_default_open_position(
    positions_parser, raw_open_positions, parsed_open_positions
):
    assert check_if_dicts_match(
        parsed_open_positions, positions_parser.parse_positions(raw_open_positions)
    )


def test_parse_position_mode_one_way(
    positions_parser: parser.PositionsParser,
    raw_closed_positions,
    parsed_closed_positions,
    parsed_open_positions,
    raw_open_positions,
):
    assert set_and_check_open_and_closed(
        key=PositionCols.POSITION_MODE.value,
        positions_parser=positions_parser,
        parsed_value=PositionMode.ONE_WAY,
        parsed_open_positions=parsed_open_positions,
        parsed_closed_positions=parsed_closed_positions,
        raw_value=False,
        raw_open_positions=raw_open_positions,
        raw_closed_positions=raw_closed_positions,
        set_to_info=True,
    )


def test_parse_position_mode_hedged(
    positions_parser: parser.PositionsParser,
    raw_closed_positions,
    parsed_closed_positions,
    parsed_open_positions,
    raw_open_positions,
):
    assert set_and_check_open_and_closed(
        key=PositionCols.POSITION_MODE.value,
        positions_parser=positions_parser,
        parsed_value=PositionMode.HEDGE,
        parsed_open_positions=parsed_open_positions,
        parsed_closed_positions=parsed_closed_positions,
        raw_value=True,
        raw_open_positions=raw_open_positions,
        raw_closed_positions=raw_closed_positions,
        set_to_info=True,
    )



def test_parse_position_missing_mode(
    positions_parser: parser.PositionsParser,
    raw_closed_positions,
):
    try:
        raw_closed_positions[PositionCols.INFO.value].pop(
            positions_parser.MODE_KEY_NAMES[0]
        )
        positions_parser.parse_positions(raw_closed_positions)

    except NotImplementedError:
        assert True
    assert False


def test_parse_position_original_side_short(
    positions_parser: parser.PositionsParser,
    raw_closed_positions,
    parsed_closed_positions,
    parsed_open_positions,
    raw_open_positions,
):
    assert set_and_check_open_and_closed(
        key=PositionCols.ORIGINAL_SIDE.value,
        positions_parser=positions_parser,
        parsed_value="short",
        parsed_open_positions=parsed_open_positions,
        parsed_closed_positions=parsed_closed_positions,
        raw_value="short",
        raw_open_positions=raw_open_positions,
        raw_closed_positions=raw_closed_positions
    )


def test_parse_position_original_side_short(
    positions_parser: parser.PositionsParser,
    raw_closed_positions,
    parsed_closed_positions,
    parsed_open_positions,
    raw_open_positions,
):
    assert set_and_check_open_and_closed(
        key=PositionCols.ORIGINAL_SIDE.value,
        positions_parser=positions_parser,
        parsed_value="short",
        parsed_open_positions=parsed_open_positions,
        parsed_closed_positions=parsed_closed_positions,
        raw_value="short",
        raw_open_positions=raw_open_positions,
        raw_closed_positions=raw_closed_positions
    )


def check_open_and_closed_position(
    parsed_closed_positions,
    positions_parser,
    raw_closed_positions,
    parsed_open_positions,
    raw_open_positions,
):
    closed_success = check_if_dicts_match(
        parsed_closed_positions, positions_parser.parse_positions(raw_closed_positions)
    )
    open_success = check_if_dicts_match(
        parsed_open_positions, positions_parser.parse_positions(raw_open_positions)
    )
    return closed_success and open_success


def test_parse_position_(
    positions_parser: parser.PositionsParser,
    raw_closed_positions,
    parsed_closed_positions,
):
    parsed_closed_positions[PositionCols.POSITION_MODE.value] = PositionMode.HEDGE
    raw_closed_positions[PositionCols.INFO.value][
        positions_parser.MODE_KEY_NAMES[0]
    ] = True
    assert check_if_dicts_match(
        parsed_closed_positions, positions_parser.parse_positions(raw_closed_positions)
    )


def check_if_dicts_match(example_dict, result_dict):
    for example_key in example_dict:
        if (
            example_key not in result_dict
            or example_dict[example_key] != result_dict[example_key]
        ):
            return False
    return True


def set_raw_and_parsed_open_and_closed_by_key(
    key,
    parsed_value,
    parsed_open_positions,
    parsed_closed_positions,
    raw_value,
    raw_open_positions,
    raw_closed_positions,
    set_to_info=False,
):
    set_parsed_open_and_closed_key(
        key=key,
        parsed_value=parsed_value,
        parsed_open_positions=parsed_open_positions,
        parsed_closed_positions=parsed_closed_positions,
    )
    set_raw_open_and_closed_key(
        key=key,
        raw_value=raw_value,
        raw_open_positions=raw_open_positions,
        raw_closed_positions=raw_closed_positions,
        set_to_info=set_to_info,
    )


def set_parsed_open_and_closed_key(
    key, value, parsed_open_positions, parsed_closed_positions
):
    parsed_open_positions[key] = parsed_closed_positions[key] = value


def set_raw_open_and_closed_key(
    key, value, raw_open_positions, raw_closed_positions, set_to_info=False
):
    if set_to_info:
        raw_open_positions[PositionCols.INFO.value][key] = raw_closed_positions[
            PositionCols.INFO.value
        ][key] = value
    raw_open_positions[key] = raw_closed_positions[key] = value


def set_and_check_open_and_closed(
    key,
    positions_parser,
    parsed_value,
    parsed_open_positions,
    parsed_closed_positions,
    raw_value,
    raw_open_positions,
    raw_closed_positions,
    set_to_info=False,
):
    set_raw_and_parsed_open_and_closed_by_key(
        key=key,
        parsed_value=parsed_value,
        parsed_open_positions=parsed_open_positions,
        parsed_closed_positions=parsed_closed_positions,
        raw_value=raw_value,
        raw_open_positions=raw_open_positions,
        raw_closed_positions=raw_closed_positions,
        set_to_info=set_to_info,
    )
    return check_open_and_closed_position(
        parsed_closed_positions=parsed_closed_positions,
        positions_parser=positions_parser,
        raw_closed_positions=raw_closed_positions,
        parsed_open_positions=parsed_open_positions,
        raw_open_positions=raw_open_positions,
    )
