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
import copy
import mock

import octobot_commons.constants
import octobot_trading.enums as enums
import octobot_trading.personal_data as personal_data


def test_resolve_sub_portfolios_no_filling_assets():
    master_pf = _sub_pf(0, _content({"BTC": 0.1, "ETH": 9.9999999, "USDT": 100}))
    origin_master_pf = copy.deepcopy(master_pf)

    assert personal_data.resolve_sub_portfolios(master_pf, [], [], [], {}) == (
        origin_master_pf, []
    )

    sub_pf_btc = _sub_pf(0, _content({"BTC": 0.01}))
    assert personal_data.resolve_sub_portfolios(master_pf, [sub_pf_btc], [], [], {}) == (
        _sub_pf(0, _content({"BTC": 0.09, "ETH": 9.9999999, "USDT": 100})),
        [_sub_pf(0, _content({"BTC": 0.01}))]
    )

    sub_pf_btc_usdt = _sub_pf(1, _content({"BTC": 0.05, "USDT": 100}))
    assert personal_data.resolve_sub_portfolios(
        master_pf, [sub_pf_btc, sub_pf_btc_usdt], [], [], {}
    ) == (
        _sub_pf(0, _content({"BTC": 0.04, "ETH": 9.9999999, "USDT": 0})),
        [
            _sub_pf(0, _content({"BTC": 0.01})),
            _sub_pf(1, _content({"BTC": 0.05, "USDT": 100}))
        ]
    )

    # not enough BTC and USDT in master portfolio for this sub portfolio
    sub_pf_btc_usdt_2 = _sub_pf(2, _content({"BTC": 0.06, "USDT": 40, "TRX": 11}))
    assert personal_data.resolve_sub_portfolios(
        master_pf, [sub_pf_btc, sub_pf_btc_usdt, sub_pf_btc_usdt_2], [], [], {}
    ) == (
        _sub_pf(0, _content({"BTC": 0, "ETH": 9.9999999, "USDT": 0})),
        [
            _sub_pf(0, _content({"BTC": 0.01})),
            _sub_pf(1, _content({"BTC": 0.05, "USDT": 100})),
            _sub_pf(
                2,
                _content({"BTC": 0.04, "USDT": 0, "TRX": 0}),
                missing_funds=_missing_funds({"BTC": 0.02, "USDT": 40, "TRX": 11})
            )  # adapted to available in master
        ]
    )

    # portfolio with higher priority takes BTC before others
    priority_sub_pf_btc = _sub_pf(0.1, _content({"BTC": 0.02}))
    assert personal_data.resolve_sub_portfolios(
        master_pf, [sub_pf_btc, sub_pf_btc_usdt, sub_pf_btc_usdt_2, priority_sub_pf_btc], [], [], {}
    ) == (
        _sub_pf(0, _content({"BTC": 0, "ETH": 9.9999999, "USDT": 0})),
        [
            _sub_pf(0, _content({"BTC": 0.01})),
            _sub_pf(0.1, _content({"BTC": 0.02})),
            _sub_pf(1, _content({"BTC": 0.05, "USDT": 100})),
            _sub_pf(
                2,
                _content({"BTC": 0.02, "USDT": 0, "TRX": 0}),
                missing_funds=_missing_funds({"BTC": 0.04, "USDT": 40, "TRX": 11})
            )  # adapted to available in master
        ]
    )


def test_resolve_sub_portfolios_with_filling_assets():
    master_pf = _sub_pf(0, _content({"BTC": 0.1, "ETH": 9.9999999, "USDT": 100, "USDC": 100}))
    origin_master_pf = copy.deepcopy(master_pf)
    filling_assets = ["USDC", "SOL"]
    market_prices = {
        "SOL/USDT": 150,
        "BTC/USDC": 83000,
        "ETH/USDC": 2000,
        "USDT/USDC": 1,
        "USDC/TRX": 0.5,    # equivalent to TRX/USDT: 2
    }

    assert personal_data.resolve_sub_portfolios(master_pf, [], filling_assets, [], market_prices) == (
        origin_master_pf, []
    )

    sub_pf_btc = _sub_pf(0, _content({"BTC": 0.01}))
    sub_pf_btc_usdt = _sub_pf(1, _content({"BTC": 0.05, "USDT": 100}))
    # not enough BTC and USDT in master portfolio for this sub portfolio but can use USDC instead
    sub_pf_btc_usdt_2 = _sub_pf(2, _content({"BTC": 0.04001, "USDT": 40, "TRX": 11}))

    # no allowed filling assets
    assert personal_data.resolve_sub_portfolios(
        master_pf, [sub_pf_btc, sub_pf_btc_usdt, sub_pf_btc_usdt_2], [], [], market_prices
    ) == (
        _sub_pf(0, _content({"BTC": 0, "ETH": 9.9999999, "USDT": 0, "USDC": 100})),
        [
            _sub_pf(0, _content({"BTC": 0.01})),
            _sub_pf(1, _content({"BTC": 0.05, "USDT": 100})),
            _sub_pf(
                2,
                _content({"BTC": 0.04, "USDT": 0, "TRX": 0}),
                # BTC not considered as missing since the missing amount % is very low
                missing_funds=_missing_funds({"USDT": 40, "TRX": 11})
            )  # adapted to available in master
        ]
    )

    # no market_prices
    assert personal_data.resolve_sub_portfolios(
        master_pf, [sub_pf_btc, sub_pf_btc_usdt, sub_pf_btc_usdt_2], filling_assets, [], {}
    ) == (
        _sub_pf(0, _content({"BTC": 0, "ETH": 9.9999999, "USDT": 0, "USDC": 100})),
        [
            _sub_pf(0, _content({"BTC": 0.01})),
            _sub_pf(1, _content({"BTC": 0.05, "USDT": 100})),
            _sub_pf(
                2,
                _content({"BTC": 0.04, "USDT": 0, "TRX": 0}),
                # BTC not considered as missing since the missing amount % is very low
                missing_funds=_missing_funds({"USDT": 40, "TRX": 11})
            )  # adapted to available in master
        ]
    )

    # now adapt sub portfolio 3
    assert personal_data.resolve_sub_portfolios(
        master_pf, [sub_pf_btc, sub_pf_btc_usdt, sub_pf_btc_usdt_2], filling_assets, [], market_prices
    ) == (
        _sub_pf(0, _content({"BTC": 0, "ETH": 9.9999999, "USDT": 0, "USDC": 38})),
        [
            _sub_pf(0, _content({"BTC": 0.01})),
            _sub_pf(1, _content({"BTC": 0.05, "USDT": 100})),
            _sub_pf(
                2,
                # 62 = 40 (for USDT) + 22 (for 11 TRX)
                _content({"BTC": 0.04, "USDT": 0, "USDC": 62, "TRX": 0}),
                # BTC not considered as missing since the missing amount % is very low
                funds_deltas=_content({"USDC": 62}),
            )  # adapted to available in master
        ]
    )

    # now adapt sub portfolio 3 and partially 4
    sub_pf_usdt_ada = _sub_pf(5, _content({"ETH": 1, "USDT": 4, "ADA": 1199}))
    assert personal_data.resolve_sub_portfolios(
        master_pf, [sub_pf_btc, sub_pf_btc_usdt, sub_pf_btc_usdt_2, sub_pf_usdt_ada], filling_assets, [], market_prices
    ) == (
        _sub_pf(0, _content({"BTC": 0, "ETH": 8.9999999, "USDT": 0, "USDC": 34})),
        [
            _sub_pf(0, _content({"BTC": 0.01})),
            _sub_pf(1, _content({"BTC": 0.05, "USDT": 100})),
            _sub_pf(
                2,
                # 62 = 40 (for USDT) + 22 (for 11 TRX)
                _content({"BTC": 0.04, "USDT": 0, "USDC": 62, "TRX": 0}),
                # BTC not considered as missing since the missing amount % is very low
                funds_deltas=_content({"USDC": 62}),
            ),
            _sub_pf(
                5,
                _content({"ETH": 1, "USDT": 0, "USDC": 4, "ADA": 0}),
                funds_deltas=_content({"USDC": 4}),
                missing_funds=_missing_funds({"ADA": 1199}),
            ),
        ]
    )

    # with forbidden assets
    forbidden_assets = ["USDT", "ADA"]
    assert personal_data.resolve_sub_portfolios(
        master_pf, [sub_pf_btc, sub_pf_btc_usdt, sub_pf_btc_usdt_2, sub_pf_usdt_ada], filling_assets, forbidden_assets, market_prices
    ) == (
        # USDT is kept in master portfolio
        _sub_pf(0, _content({"BTC": 0, "ETH": 8.9999999, "USDT": 100, "USDC": 0})),
        [
            _sub_pf(0, _content({"BTC": 0.01})),
            _sub_pf(
                1,
                _content({"BTC": 0.05,"USDC": 100,"USDT": 0}),
                funds_deltas=_content({"USDC": 100})
            ),
            _sub_pf(
                2,
                # 62 = 40 (for USDT) + 22 (for 11 TRX)
                _content({"BTC": 0.04, "USDC": 0, "USDT": 0, "TRX": 0}),
                # BTC not considered as missing since the missing amount % is very low
                funds_deltas=_content({"USDC": 0}),
                missing_funds=_missing_funds({"TRX": 11, "USDT": 40}),
            ),
            _sub_pf(
                5,
                _content({"ADA": 0, "ETH": 1, "USDC": 0, "USDT": 0}),
                funds_deltas=_content({"USDC": 0}),
                missing_funds=_missing_funds({"ADA": 1199, "USDT": 4}),
            ),
        ]
    )


def test_get_portfolio_filled_orders_deltas():
    pre_trade_content = _content({"BTC": 0.1, "USDT": 1000})
    post_trade_content = _content({"BTC": 0.2, "USDT": 500})

    # no filled order
    assert personal_data.get_portfolio_filled_orders_deltas(pre_trade_content, post_trade_content, []) == (
        {}, {}
    )

    filled_orders = [
        _order("BTC/USDT", 0.06, 100, "buy"),
        _order("BTC/USDT", 0.05, 451, "buy"),   # 1 will be ignored, (allowed error margin)
        _order("BTC/USDT", 0.01, 50, "sell"),
    ]
    assert personal_data.get_portfolio_filled_orders_deltas(
        pre_trade_content, post_trade_content, filled_orders
    ) == (
        _content({"BTC": 0.1, "USDT": -500}),   # all orders found in deltas
        {}
    )

    filled_orders = [
        _order("BTC/USDT", 0.06, 100, "buy"),
        _order("BTC/USDT", 0.05, 450, "buy"),
        _order("BTC/USDT", 0.01, 50, "buy"),    # not found in portfolio delta
    ]
    assert personal_data.get_portfolio_filled_orders_deltas(
        pre_trade_content, post_trade_content, filled_orders
    ) == (
        {},
        _content({"BTC": 0.1, "USDT": -500}),   # all missing: orders can't explain this delta
    )

    filled_orders = [
        _order("SOL/USDT", 1, 200, "buy"),  # won't be found
        _order("BTC/USDT", 0.06, 100.01, "buy"),    # small change compared to portfolio
        _order("BTC/USDT", 0.01, 50, "buy"),    # not found in portfolio delta
    ]
    assert personal_data.get_portfolio_filled_orders_deltas(
        pre_trade_content, post_trade_content, filled_orders
    ) == (
        _content({"BTC": 0.07, "USDT": -350.01}),   # adapted to orders explained orders delta
        _content({"SOL": 1}),   # not found in portfolio delta
    )

    post_trade_content = _content({"USDT": 500, "SOL": 1})  # now has SOL but no BTC
    filled_orders = [
        _order("SOL/USDT", 1, 200, "buy"),  # won't be found
        _order("BTC/USDT", 0.06, 100.01, "buy"),    # small change compared to portfolio
        _order("BTC/USDT", 0.01, 50, "buy"),    # not found in portfolio delta
    ]
    assert personal_data.get_portfolio_filled_orders_deltas(
        pre_trade_content, post_trade_content, filled_orders
    ) == (
        _content({"SOL": 1, "USDT": -350.01}),   # adapted to orders explained orders delta
        _content({"BTC": -0.1}),   # not found in portfolio delta
    )

    # only sell orders
    post_trade_content = _content({"USDT": 2000})  # now has SOL but no BTC
    filled_orders = [
        _order("BTC/USDT", 0.06, 400, "sell"),    # small change compared to portfolio
        _order("BTC/USDT", 0.04, 600, "sell"),    # not found in portfolio delta
    ]
    assert personal_data.get_portfolio_filled_orders_deltas(
        pre_trade_content, post_trade_content, filled_orders
    ) == (
        _content({"BTC": -0.1, "USDT": 1000}),
        {},
    )


def _sub_pf(
    priority_key: float,
    content: dict[str, dict[str, decimal.Decimal]],
    funds_deltas: dict[str, dict[str, decimal.Decimal]] = None,
    missing_funds: dict[str, decimal.Decimal] = None,
) -> personal_data.SubPortfolioData:
    return personal_data.SubPortfolioData("", "", priority_key, content, "", funds_deltas or {}, missing_funds or {})

def _content(content: dict[str, float]) -> dict[str, dict[str, decimal.Decimal]]:
    return {
        key: {
            octobot_commons.constants.PORTFOLIO_TOTAL: decimal.Decimal(str(val)),
            octobot_commons.constants.PORTFOLIO_AVAILABLE: decimal.Decimal(str(val)),
        }
        for key, val in content.items()
    }

def _missing_funds(funds: dict[str, float]) -> dict[str, decimal.Decimal]:
    return {
        key: decimal.Decimal(str(val))
        for key, val in funds.items()
    }

def _order(symbol: str, quantity: float, cost: float, side: str) -> personal_data.Order:
    trader = mock.Mock(exchange_manager=mock.Mock())
    order = personal_data.Order(trader)
    order.symbol = symbol
    order.origin_quantity = decimal.Decimal(str(quantity))
    order.total_cost = decimal.Decimal(str(cost))
    order.side = enums.TradeOrderSide(side)
    return order
