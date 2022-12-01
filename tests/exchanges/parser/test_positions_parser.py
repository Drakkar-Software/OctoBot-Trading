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
from octobot_trading import exchanges
from octobot_trading.enums import (
    ExchangePositionCCXTColumns,
    FutureContractType,
    PositionMode,
    PositionSide,
    PositionStatus,
    TraderPositionType,
    ExchangeConstantsPositionColumns as PositionCols,
)
import octobot_trading.exchanges.parser as parser
import octobot_commons.tests.test_config as test_config


pytestmark = pytest.mark.asyncio


EXCHANGE_NAME = "binance"


def mock_get_pair_from_exchange(raw_symbol):
    return raw_symbol


async def mock_get_kline_price(symbol, time_frame):
    return [[456456546456, 4000, 5000, 3000, 4500, 43543534534]]


def mock_get_contract_type(symbol):
    return FutureContractType.LINEAR_PERPETUAL


@pytest.fixture
def abstract_exchange():
    config = test_config.load_test_config()
    exchange = exchanges.FutureCCXTExchange(
        config, exchanges.ExchangeManager(config, EXCHANGE_NAME)
    )
    exchange.get_pair_from_exchange = mock_get_pair_from_exchange
    exchange.get_kline_price = mock_get_kline_price
    exchange.get_contract_type = mock_get_contract_type
    return exchange


#         # connector.get_exchange_current_time
#         # get_pair_from_exchange
#         # get_kline_price


@pytest.fixture
def positions_parser(abstract_exchange):
    return parser.PositionsParser(exchange=abstract_exchange)


def get_raw_closed_positions():
    return [
        {
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
                "realized_pnl": "5.73893937",
                "cum_realized_pnl": "-12.12747167",
                "free_qty": "0",
                "tp_sl_mode": "Partial",
                "unrealized_pnl": "0",
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
    ]


def get_raw_open_positions():
    return [
        {
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
                "realized_pnl": "-5.73893937",
                "cum_realized_pnl": "-12.12747167",
                "free_qty": "-0.01",
                "tp_sl_mode": "Partial",
                "unrealized_pnl": "2.50941072",
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
    ]


def get_parsed_closed_positions():
    return [
        {
            "symbol": "10000NFT/USDT:USDT",
            "original_side": "short",
            "position_mode": PositionMode.ONE_WAY,
            "status": PositionStatus.CLOSED,
            "side": PositionSide.BOTH,
            "size": decimal.Decimal("0.0"),
            "contract_type": FutureContractType.LINEAR_PERPETUAL,
            "margin_type": TraderPositionType.CROSS,
            "leverage": decimal.Decimal("5.0"),
            "realized_pnl": decimal.Decimal("-12.12747167"),
        }
    ]


def get_parsed_open_positions():
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
            "realized_pnl": decimal.Decimal("-12.12747167"),
            "status": PositionStatus.OPEN,
            "quantity": decimal.Decimal("1.0"),
            "timestamp": 1668494270,
            "collateral": decimal.Decimal("33.5939353"),
            "notional": decimal.Decimal("167.96968928"),
            "unrealized_pnl": decimal.Decimal("2.50941072"),
            "liquidation_price": decimal.Decimal("13522.0"),
            "closing_fee": decimal.Decimal("0.080628"),
            "mark_price": decimal.Decimal("4500"),
            "value": decimal.Decimal("167.96968928"),
            "initial_margin": decimal.Decimal("33.5939353"),
            "entry_price": decimal.Decimal("16796.96892692"),
        }
    ]


async def test_parse_default_closed_position(
    positions_parser,
):
    just_parsed_positions = await positions_parser.parse_positions(
        get_raw_closed_positions()
    )
    assert get_parsed_closed_positions() == just_parsed_positions


async def test_parse_default_open_position(
    positions_parser,
):
    just_parsed_positions = await positions_parser.parse_positions(
        get_raw_open_positions()
    )
    assert get_parsed_open_positions() == just_parsed_positions


async def test_parse_one_way_mode(
    positions_parser,
    parsed_open_positions=get_parsed_open_positions(),
    parsed_closed_positions=get_parsed_closed_positions(),
    raw_open_positions=get_raw_open_positions(),
    raw_closed_positions=get_raw_closed_positions(),
):
    await set_and_check_open_and_closed(
        key=PositionCols.POSITION_MODE.value,
        positions_parser=positions_parser,
        value=PositionMode.ONE_WAY,
        parsed_open_positions=parsed_open_positions,
        parsed_closed_positions=parsed_closed_positions,
        raw_key="hedged",
        raw_value=False,
        raw_open_positions=raw_open_positions,
        raw_closed_positions=raw_closed_positions,
        set_to_info=True,
    )


async def test_parse_hedge_mode_long(
    positions_parser,
    parsed_open_positions=get_parsed_open_positions(),
    parsed_closed_positions=get_parsed_closed_positions(),
    raw_open_positions=get_raw_open_positions(),
    raw_closed_positions=get_raw_closed_positions(),
):
    raw_closed_positions[0][PositionCols.SIDE.value] = PositionSide.LONG.value
    raw_open_positions[0][PositionCols.SIDE.value] = PositionSide.LONG.value
    parsed_open_positions[0][PositionCols.ORIGINAL_SIDE.value] = PositionSide.LONG.value
    parsed_closed_positions[0][
        PositionCols.ORIGINAL_SIDE.value
    ] = PositionSide.LONG.value
    parsed_open_positions[0][PositionCols.SIDE.value] = PositionSide.LONG
    parsed_closed_positions[0][PositionCols.SIDE.value] = PositionSide.LONG
    await hedge_mode_test(
        positions_parser,
        parsed_open_positions,
        parsed_closed_positions,
        raw_open_positions,
        raw_closed_positions,
    )


async def test_parse_hedge_mode_short(
    positions_parser,
    parsed_open_positions=get_parsed_open_positions(),
    parsed_closed_positions=get_parsed_closed_positions(),
    raw_open_positions=get_raw_open_positions(),
    raw_closed_positions=get_raw_closed_positions(),
):
    raw_closed_positions[0][PositionCols.SIDE.value] = PositionSide.SHORT.value
    raw_open_positions[0][PositionCols.SIDE.value] = PositionSide.SHORT.value
    parsed_open_positions[0][
        PositionCols.ORIGINAL_SIDE.value
    ] = PositionSide.SHORT.value
    parsed_closed_positions[0][
        PositionCols.ORIGINAL_SIDE.value
    ] = PositionSide.SHORT.value
    parsed_open_positions[0][PositionCols.SIZE.value] *= (
        1 if parsed_open_positions[0][PositionCols.SIZE.value] < 0 else -1
    )
    parsed_open_positions[0][PositionCols.SIDE.value] = PositionSide.SHORT
    parsed_closed_positions[0][PositionCols.SIDE.value] = PositionSide.SHORT
    await hedge_mode_test(
        positions_parser,
        parsed_open_positions,
        parsed_closed_positions,
        raw_open_positions,
        raw_closed_positions,
    )


async def hedge_mode_test(
    positions_parser,
    parsed_open_positions,
    parsed_closed_positions,
    raw_open_positions,
    raw_closed_positions,
):
    await set_and_check_open_and_closed(
        key=PositionCols.POSITION_MODE.value,
        positions_parser=positions_parser,
        value=PositionMode.HEDGE,
        parsed_open_positions=parsed_open_positions,
        parsed_closed_positions=parsed_closed_positions,
        raw_key="hedged",
        raw_value=True,
        raw_open_positions=raw_open_positions,
        raw_closed_positions=raw_closed_positions,
        set_to_info=True,
    )


async def test_parse_position_missing_mode(
    positions_parser,
    raw_closed_positions=get_raw_closed_positions(),
    raw_open_positions=get_raw_open_positions(),
):
    _raw_closed_positions = raw_closed_positions.copy()
    _raw_open_positions = raw_open_positions.copy()
    try:
        _raw_closed_positions[0][ExchangePositionCCXTColumns.INFO.value].pop(
            positions_parser.MODE_KEY_NAMES[0]
        )
        await positions_parser.parse_positions(_raw_closed_positions)
        assert False
    except NotImplementedError:
        pass
    try:
        _raw_open_positions[0][ExchangePositionCCXTColumns.INFO.value].pop(
            positions_parser.MODE_KEY_NAMES[0]
        )
        await positions_parser.parse_positions(_raw_open_positions)
    except NotImplementedError:
        assert True
        return
    assert False


async def test_parse_position_side_short(
    positions_parser,
    parsed_open_positions=get_parsed_open_positions(),
    parsed_closed_positions=get_parsed_closed_positions(),
    raw_closed_positions=get_raw_closed_positions(),
    raw_open_positions=get_raw_open_positions(),
):
    raw_closed_positions[0][PositionCols.SIDE.value] = PositionSide.SHORT.value
    raw_open_positions[0][PositionCols.SIDE.value] = PositionSide.SHORT.value
    parsed_open_positions[0][
        PositionCols.ORIGINAL_SIDE.value
    ] = PositionSide.SHORT.value
    parsed_closed_positions[0][
        PositionCols.ORIGINAL_SIDE.value
    ] = PositionSide.SHORT.value
    parsed_open_positions[0][PositionCols.SIZE.value] *= -1
    await test_parse_one_way_mode(
        positions_parser,
        parsed_open_positions,
        parsed_closed_positions,
        raw_open_positions,
        raw_closed_positions,
    )
    parsed_open_positions[0][PositionCols.SIDE.value] = PositionSide.SHORT
    parsed_closed_positions[0][PositionCols.SIDE.value] = PositionSide.SHORT
    await test_parse_hedge_mode_short(
        positions_parser,
        parsed_open_positions,
        parsed_closed_positions,
        raw_open_positions,
        raw_closed_positions,
    )
    await test_parse_position_missing_mode(
        positions_parser,
        raw_closed_positions,
        raw_open_positions,
    )


async def test_parse_position_side_long(
    positions_parser,
    parsed_open_positions=get_parsed_open_positions(),
    parsed_closed_positions=get_parsed_closed_positions(),
    raw_closed_positions=get_raw_closed_positions(),
    raw_open_positions=get_raw_open_positions(),
):
    raw_closed_positions[0][PositionCols.SIDE.value] = PositionSide.LONG.value
    raw_open_positions[0][PositionCols.SIDE.value] = PositionSide.LONG.value
    parsed_open_positions[0][PositionCols.ORIGINAL_SIDE.value] = PositionSide.LONG.value
    parsed_closed_positions[0][
        PositionCols.ORIGINAL_SIDE.value
    ] = PositionSide.LONG.value
    await test_parse_one_way_mode(
        positions_parser,
        parsed_open_positions,
        parsed_closed_positions,
        raw_open_positions,
        raw_closed_positions,
    )
    parsed_open_positions[0][PositionCols.SIDE.value] = PositionSide.LONG
    parsed_closed_positions[0][PositionCols.SIDE.value] = PositionSide.LONG
    await test_parse_hedge_mode_long(
        positions_parser,
        parsed_open_positions,
        parsed_closed_positions,
        raw_open_positions,
        raw_closed_positions,
    )
    await test_parse_position_missing_mode(
        positions_parser,
        raw_closed_positions,
        raw_open_positions,
    )


async def test_parse_margin_type_CROSS_long(
    positions_parser,
    parsed_open_positions=get_parsed_open_positions(),
    parsed_closed_positions=get_parsed_closed_positions(),
    raw_closed_positions=get_raw_closed_positions(),
    raw_open_positions=get_raw_open_positions(),
):
    set_raw_and_parsed_open_and_closed_by_key(
        PositionCols.MARGIN_TYPE.value,
        value=TraderPositionType.CROSS,
        parsed_open_positions=parsed_open_positions,
        parsed_closed_positions=parsed_closed_positions,
        raw_key=ExchangePositionCCXTColumns.MARGIN_MODE.value,
        raw_value=TraderPositionType.CROSS.value,
        raw_open_positions=raw_open_positions,
        raw_closed_positions=raw_closed_positions,
    )
    await test_parse_position_side_long(
        positions_parser,
        parsed_open_positions=parsed_open_positions.copy(),
        parsed_closed_positions=parsed_closed_positions.copy(),
        raw_closed_positions=raw_closed_positions.copy(),
        raw_open_positions=raw_open_positions.copy(),
    )


async def test_parse_margin_type_CROSS_short(
    positions_parser,
    parsed_open_positions=get_parsed_open_positions(),
    parsed_closed_positions=get_parsed_closed_positions(),
    raw_closed_positions=get_raw_closed_positions(),
    raw_open_positions=get_raw_open_positions(),
):
    set_raw_and_parsed_open_and_closed_by_key(
        PositionCols.MARGIN_TYPE.value,
        value=TraderPositionType.CROSS,
        parsed_open_positions=parsed_open_positions,
        parsed_closed_positions=parsed_closed_positions,
        raw_key=ExchangePositionCCXTColumns.MARGIN_MODE.value,
        raw_value=TraderPositionType.CROSS.value,
        raw_open_positions=raw_open_positions,
        raw_closed_positions=raw_closed_positions,
    )
    await test_parse_position_side_short(
        positions_parser,
        parsed_open_positions=parsed_open_positions.copy(),
        parsed_closed_positions=parsed_closed_positions.copy(),
        raw_closed_positions=raw_closed_positions.copy(),
        raw_open_positions=raw_open_positions.copy(),
    )


async def test_parse_margin_type_ISOLATED_long(
    positions_parser,
    parsed_open_positions=get_parsed_open_positions(),
    parsed_closed_positions=get_parsed_closed_positions(),
    raw_closed_positions=get_raw_closed_positions(),
    raw_open_positions=get_raw_open_positions(),
):
    set_raw_and_parsed_open_and_closed_by_key(
        PositionCols.MARGIN_TYPE.value,
        value=TraderPositionType.ISOLATED,
        parsed_open_positions=parsed_open_positions,
        parsed_closed_positions=parsed_closed_positions,
        raw_key=ExchangePositionCCXTColumns.MARGIN_MODE.value,
        raw_value=TraderPositionType.ISOLATED.value,
        raw_open_positions=raw_open_positions,
        raw_closed_positions=raw_closed_positions,
    )
    await test_parse_position_side_long(
        positions_parser,
        parsed_open_positions=parsed_open_positions.copy(),
        parsed_closed_positions=parsed_closed_positions.copy(),
        raw_closed_positions=raw_closed_positions.copy(),
        raw_open_positions=raw_open_positions.copy(),
    )


async def test_parse_margin_type_ISOLATED_short(
    positions_parser,
    parsed_open_positions=get_parsed_open_positions(),
    parsed_closed_positions=get_parsed_closed_positions(),
    raw_closed_positions=get_raw_closed_positions(),
    raw_open_positions=get_raw_open_positions(),
):
    set_raw_and_parsed_open_and_closed_by_key(
        PositionCols.MARGIN_TYPE.value,
        value=TraderPositionType.ISOLATED,
        parsed_open_positions=parsed_open_positions,
        parsed_closed_positions=parsed_closed_positions,
        raw_key=ExchangePositionCCXTColumns.MARGIN_MODE.value,
        raw_value=TraderPositionType.ISOLATED.value,
        raw_open_positions=raw_open_positions,
        raw_closed_positions=raw_closed_positions,
    )
    await test_parse_position_side_short(
        positions_parser,
        parsed_open_positions=parsed_open_positions.copy(),
        parsed_closed_positions=parsed_closed_positions.copy(),
        raw_closed_positions=raw_closed_positions.copy(),
        raw_open_positions=raw_open_positions.copy(),
    )


async def check_open_and_closed_position(
    positions_parser,
    raw_closed_positions,
    parsed_closed_positions,
    raw_open_positions,
    parsed_open_positions,
):
    just_parsed_closed_positions = await positions_parser.parse_positions(
        raw_closed_positions
    )
    assert parsed_closed_positions == just_parsed_closed_positions
    just_parsed_open_positions = await positions_parser.parse_positions(
        raw_open_positions
    )
    assert parsed_open_positions == just_parsed_open_positions


def set_raw_and_parsed_open_and_closed_by_key(
    key,
    value,
    parsed_open_positions,
    parsed_closed_positions,
    raw_key,
    raw_value,
    raw_open_positions,
    raw_closed_positions,
    set_to_info=False,
):
    set_parsed_open_and_closed_key(
        key=key,
        value=value,
        parsed_open_positions=parsed_open_positions,
        parsed_closed_positions=parsed_closed_positions,
    )
    set_raw_open_and_closed_key(
        key=raw_key,
        value=raw_value,
        raw_open_positions=raw_open_positions,
        raw_closed_positions=raw_closed_positions,
        set_to_info=set_to_info,
    )


def set_parsed_open_and_closed_key(
    key, value, parsed_open_positions, parsed_closed_positions
):
    parsed_open_positions[0][key] = parsed_closed_positions[0][key] = value


def set_raw_open_and_closed_key(
    key, value, raw_open_positions, raw_closed_positions, set_to_info=False
):
    if set_to_info:
        raw_open_positions[0][ExchangePositionCCXTColumns.INFO.value][
            key
        ] = raw_closed_positions[0][ExchangePositionCCXTColumns.INFO.value][key] = value
    else:
        raw_open_positions[0][key] = raw_closed_positions[0][key] = value


async def set_and_check_open_and_closed(
    key,
    positions_parser,
    value,
    parsed_open_positions,
    parsed_closed_positions,
    raw_key,
    raw_value,
    raw_open_positions,
    raw_closed_positions,
    set_to_info=False,
):
    _parsed_open_positions = parsed_open_positions
    _parsed_closed_positions = parsed_closed_positions
    _raw_open_positions = raw_open_positions
    _raw_closed_positions = raw_closed_positions
    set_raw_and_parsed_open_and_closed_by_key(
        key=key,
        value=value,
        parsed_open_positions=_parsed_open_positions,
        parsed_closed_positions=_parsed_closed_positions,
        raw_key=raw_key,
        raw_value=raw_value,
        raw_open_positions=_raw_open_positions,
        raw_closed_positions=_raw_closed_positions,
        set_to_info=set_to_info,
    )
    await check_open_and_closed_position(
        parsed_closed_positions=_parsed_closed_positions,
        positions_parser=positions_parser,
        raw_closed_positions=_raw_closed_positions,
        parsed_open_positions=_parsed_open_positions,
        raw_open_positions=_raw_open_positions,
    )
