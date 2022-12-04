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
from .parser_tests_util import (
    mock_abstract_exchange,
    set_and_check_open_and_closed,
    set_raw_and_parsed_open_and_closed_by_key,
)

pytestmark = pytest.mark.asyncio


def active_parser_class():
    return parser.PositionsParser(exchange=mock_abstract_exchange())


def active_parser(raw_records):
    _parser = active_parser_class()
    return _parser.parse_positions(raw_records)


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
                active_parser_class().MODE_KEY_NAMES[0]: False,
                ExchangePositionCCXTColumns.MARK_PRICE.value: 4500.55,
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
                active_parser_class().MODE_KEY_NAMES[0]: False,
                ExchangePositionCCXTColumns.MARK_PRICE.value: 4500.55,
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
            PositionCols.SYMBOL.value: "10000NFT/USDT:USDT",
            PositionCols.ORIGINAL_SIDE.value: "short",
            PositionCols.POSITION_MODE.value: PositionMode.ONE_WAY,
            PositionCols.SIDE.value: PositionSide.BOTH,
            PositionCols.SIZE.value: decimal.Decimal("0"),
            PositionCols.CONTRACT_TYPE.value: FutureContractType.LINEAR_PERPETUAL,
            PositionCols.MARGIN_TYPE.value: TraderPositionType.CROSS,
            PositionCols.LEVERAGE.value: decimal.Decimal("5.0"),
            PositionCols.REALIZED_PNL.value: decimal.Decimal("-12.12747167"),
            PositionCols.STATUS.value: PositionStatus.CLOSED,
            PositionCols.MARK_PRICE.value: decimal.Decimal("4500.55"),
        }
    ]


def get_parsed_open_positions():
    return [
        {
            PositionCols.SYMBOL.value: "BTC/USDT:USDT",
            PositionCols.ORIGINAL_SIDE.value: "long",
            PositionCols.POSITION_MODE.value: PositionMode.ONE_WAY,
            PositionCols.STATUS.value: PositionStatus.OPEN,
            PositionCols.SIDE.value: PositionSide.BOTH,
            PositionCols.SIZE.value: decimal.Decimal("0.01"),
            PositionCols.CONTRACT_TYPE.value: FutureContractType.LINEAR_PERPETUAL,
            PositionCols.MARGIN_TYPE.value: TraderPositionType.ISOLATED,
            PositionCols.LEVERAGE.value: decimal.Decimal("5.0"),
            PositionCols.REALIZED_PNL.value: decimal.Decimal("-12.12747167"),
            PositionCols.QUANTITY.value: decimal.Decimal("1.0"),
            PositionCols.TIMESTAMP.value: 1668494270,
            PositionCols.COLLATERAL.value: decimal.Decimal("33.5939353"),
            PositionCols.NOTIONAL.value: decimal.Decimal("167.96968928"),
            PositionCols.UNREALIZED_PNL.value: decimal.Decimal("2.50941072"),
            PositionCols.LIQUIDATION_PRICE.value: decimal.Decimal("13522.0"),
            PositionCols.CLOSING_FEE.value: decimal.Decimal("0.080628"),
            PositionCols.MARK_PRICE.value: decimal.Decimal("4500.55"),
            PositionCols.VALUE.value: decimal.Decimal("167.96968928"),
            PositionCols.INITIAL_MARGIN.value: decimal.Decimal("33.5939353"),
            PositionCols.ENTRY_PRICE.value: decimal.Decimal("16796.96892692"),
        }
    ]


async def test_parse_default_closed_position():
    just_parsed_positions = await active_parser(get_raw_closed_positions())
    assert get_parsed_closed_positions() == just_parsed_positions


async def test_parse_default_open_position():
    just_parsed_positions = await active_parser(get_raw_open_positions())
    assert get_parsed_open_positions() == just_parsed_positions


async def test_parse_one_way_mode(
    parsed_open_positions=get_parsed_open_positions(),
    parsed_closed_positions=get_parsed_closed_positions(),
    raw_open_positions=get_raw_open_positions(),
    raw_closed_positions=get_raw_closed_positions(),
):
    await set_and_check_open_and_closed(
        active_parser=active_parser,
        key=PositionCols.POSITION_MODE.value,
        value=PositionMode.ONE_WAY,
        parsed_open_records=parsed_open_positions,
        parsed_closed_records=parsed_closed_positions,
        raw_key=active_parser_class().MODE_KEY_NAMES[0],
        raw_value=active_parser_class().ONEWAY_VALUES[0],
        raw_open_records=raw_open_positions,
        raw_closed_records=raw_closed_positions,
        set_to_info=True,
    )


async def test_parse_hedge_mode_long(
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
        parsed_open_positions,
        parsed_closed_positions,
        raw_open_positions,
        raw_closed_positions,
    )


async def test_parse_hedge_mode_short(
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
    parsed_open_positions[0][PositionCols.QUANTITY.value] *= (
        1 if parsed_open_positions[0][PositionCols.QUANTITY.value] < 0 else -1
    )
    parsed_open_positions[0][PositionCols.SIDE.value] = PositionSide.SHORT
    parsed_closed_positions[0][PositionCols.SIDE.value] = PositionSide.SHORT
    await hedge_mode_test(
        parsed_open_positions,
        parsed_closed_positions,
        raw_open_positions,
        raw_closed_positions,
    )


async def hedge_mode_test(
    parsed_open_positions,
    parsed_closed_positions,
    raw_open_positions,
    raw_closed_positions,
):
    await set_and_check_open_and_closed(
        active_parser=active_parser,
        key=PositionCols.POSITION_MODE.value,
        value=PositionMode.HEDGE,
        parsed_open_records=parsed_open_positions,
        parsed_closed_records=parsed_closed_positions,
        raw_key=active_parser_class().MODE_KEY_NAMES[0],
        raw_value=active_parser_class().HEDGE_VALUES[0],
        raw_open_records=raw_open_positions,
        raw_closed_records=raw_closed_positions,
        set_to_info=True,
    )


async def test_parse_position_missing_mode(
    raw_closed_positions=get_raw_closed_positions(),
    raw_open_positions=get_raw_open_positions(),
):
    _raw_closed_positions = raw_closed_positions.copy()
    _raw_open_positions = raw_open_positions.copy()
    try:
        _raw_closed_positions[0][ExchangePositionCCXTColumns.INFO.value].pop(
            active_parser_class().MODE_KEY_NAMES[0]
        )
        await active_parser(_raw_closed_positions)
        assert False
    except NotImplementedError:
        pass
    try:
        _raw_open_positions[0][ExchangePositionCCXTColumns.INFO.value].pop(
            active_parser_class().MODE_KEY_NAMES[0]
        )
        await active_parser(_raw_open_positions)
    except NotImplementedError:
        assert True
        return
    assert False


async def test_parse_position_side_short(
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
    parsed_open_positions[0][PositionCols.QUANTITY.value] *= -1
    await test_parse_one_way_mode(
        parsed_open_positions,
        parsed_closed_positions,
        raw_open_positions,
        raw_closed_positions,
    )
    parsed_open_positions[0][PositionCols.SIDE.value] = PositionSide.SHORT
    parsed_closed_positions[0][PositionCols.SIDE.value] = PositionSide.SHORT
    await test_parse_hedge_mode_short(
        parsed_open_positions,
        parsed_closed_positions,
        raw_open_positions,
        raw_closed_positions,
    )
    await test_parse_position_missing_mode(
        raw_closed_positions,
        raw_open_positions,
    )


async def test_parse_position_side_long(
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
        parsed_open_positions,
        parsed_closed_positions,
        raw_open_positions,
        raw_closed_positions,
    )
    parsed_open_positions[0][PositionCols.SIDE.value] = PositionSide.LONG
    parsed_closed_positions[0][PositionCols.SIDE.value] = PositionSide.LONG
    await test_parse_hedge_mode_long(
        parsed_open_positions,
        parsed_closed_positions,
        raw_open_positions,
        raw_closed_positions,
    )
    await test_parse_position_missing_mode(
        raw_closed_positions,
        raw_open_positions,
    )


async def test_parse_margin_type_CROSS_long(
    parsed_open_positions=get_parsed_open_positions(),
    parsed_closed_positions=get_parsed_closed_positions(),
    raw_closed_positions=get_raw_closed_positions(),
    raw_open_positions=get_raw_open_positions(),
):
    set_raw_and_parsed_open_and_closed_by_key(
        PositionCols.MARGIN_TYPE.value,
        value=TraderPositionType.CROSS,
        parsed_open_records=parsed_open_positions,
        parsed_closed_records=parsed_closed_positions,
        raw_key=ExchangePositionCCXTColumns.MARGIN_MODE.value,
        raw_value=TraderPositionType.CROSS.value,
        raw_open_records=raw_open_positions,
        raw_closed_records=raw_closed_positions,
    )
    await test_parse_position_side_long(
        parsed_open_positions=parsed_open_positions.copy(),
        parsed_closed_positions=parsed_closed_positions.copy(),
        raw_closed_positions=raw_closed_positions.copy(),
        raw_open_positions=raw_open_positions.copy(),
    )


async def test_parse_margin_type_CROSS_short(
    parsed_open_positions=get_parsed_open_positions(),
    parsed_closed_positions=get_parsed_closed_positions(),
    raw_closed_positions=get_raw_closed_positions(),
    raw_open_positions=get_raw_open_positions(),
):
    set_raw_and_parsed_open_and_closed_by_key(
        PositionCols.MARGIN_TYPE.value,
        value=TraderPositionType.CROSS,
        parsed_open_records=parsed_open_positions,
        parsed_closed_records=parsed_closed_positions,
        raw_key=ExchangePositionCCXTColumns.MARGIN_MODE.value,
        raw_value=TraderPositionType.CROSS.value,
        raw_open_records=raw_open_positions,
        raw_closed_records=raw_closed_positions,
    )
    await test_parse_position_side_short(
        parsed_open_positions=parsed_open_positions.copy(),
        parsed_closed_positions=parsed_closed_positions.copy(),
        raw_closed_positions=raw_closed_positions.copy(),
        raw_open_positions=raw_open_positions.copy(),
    )


async def test_parse_margin_type_ISOLATED_long(
    parsed_open_positions=get_parsed_open_positions(),
    parsed_closed_positions=get_parsed_closed_positions(),
    raw_closed_positions=get_raw_closed_positions(),
    raw_open_positions=get_raw_open_positions(),
):
    set_raw_and_parsed_open_and_closed_by_key(
        PositionCols.MARGIN_TYPE.value,
        value=TraderPositionType.ISOLATED,
        parsed_open_records=parsed_open_positions,
        parsed_closed_records=parsed_closed_positions,
        raw_key=ExchangePositionCCXTColumns.MARGIN_MODE.value,
        raw_value=TraderPositionType.ISOLATED.value,
        raw_open_records=raw_open_positions,
        raw_closed_records=raw_closed_positions,
    )
    await test_parse_position_side_long(
        parsed_open_positions=parsed_open_positions.copy(),
        parsed_closed_positions=parsed_closed_positions.copy(),
        raw_closed_positions=raw_closed_positions.copy(),
        raw_open_positions=raw_open_positions.copy(),
    )


async def test_parse_margin_type_ISOLATED_short(
    parsed_open_positions=get_parsed_open_positions(),
    parsed_closed_positions=get_parsed_closed_positions(),
    raw_closed_positions=get_raw_closed_positions(),
    raw_open_positions=get_raw_open_positions(),
):
    set_raw_and_parsed_open_and_closed_by_key(
        PositionCols.MARGIN_TYPE.value,
        value=TraderPositionType.ISOLATED,
        parsed_open_records=parsed_open_positions,
        parsed_closed_records=parsed_closed_positions,
        raw_key=ExchangePositionCCXTColumns.MARGIN_MODE.value,
        raw_value=TraderPositionType.ISOLATED.value,
        raw_open_records=raw_open_positions,
        raw_closed_records=raw_closed_positions,
    )
    await test_parse_position_side_short(
        parsed_open_positions=parsed_open_positions.copy(),
        parsed_closed_positions=parsed_closed_positions.copy(),
        raw_closed_positions=raw_closed_positions.copy(),
        raw_open_positions=raw_open_positions.copy(),
    )
