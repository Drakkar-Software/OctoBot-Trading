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
import octobot_commons.logging
import octobot_trading.enums as enums
import octobot_trading.personal_data as personal_data
import octobot_trading.api as trading_api


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


def test_resolve_sub_portfolios_no_filling_assets_with_locked_funds():
    master_pf = _sub_pf(
        0,
        _content_with_available({"BTC": (0.019998, 0.1), "ETH": (0.019998, 0.1), "USDT": (0.019998, 0.1)})
    )
    sub_pf_btc = _sub_pf(0, _content({"BTC": 0.1}))
    sub_pf_btc.locked_funds_by_asset = trading_api.get_orders_locked_amounts_by_asset([
        _open_order("BTC/USDT", 0.06, 400, "sell", 0.000001, "BTC"),
        _open_order("BTC/USDT", 0.02, 600, "sell", 0.000001, "BTC"),
    ])
    assert personal_data.resolve_sub_portfolios(master_pf, [sub_pf_btc], [], [], {}) == (
        _sub_pf(0, _content_with_available({"BTC": (0, 0), "ETH": (0.019998, 0.1), "USDT": (0.019998, 0.1)})),
        [_sub_pf(0, _content_with_available({"BTC": (0.019998, 0.1)}))]
    )

    master_pf = _sub_pf(
        0,
        _content_with_available({"BTC": (0.019997, 0.1), "ETH": (0.1, 0.1), "USDT": (0, 100)})
    )
    sub_pf_1 = _sub_pf(
        0, _content({"BTC": 0.085, "ETH": 0.1}),
        locked_funds_by_asset = trading_api.get_orders_locked_amounts_by_asset([
            _open_order("BTC/USDT", 0.06, 400, "sell", 0.000001, "BTC"),
            _open_order("BTC/USDT", 0.02, 600, "sell", 0.000001, "BTC"),
        ])
    )
    sub_pf_2 = _sub_pf(
        0, _content({"BTC": 0.015, "USDT": 100}),
        locked_funds_by_asset = trading_api.get_orders_locked_amounts_by_asset([
            _open_order("BTC/USDT", 0.1, 30, "buy", 0.000001, "BTC"),
            _open_order("BTC/USDT", 0.1, 60, "buy", 5, "USDT"),
            _open_order("ETH/USDT", 0.1, 4, "buy", 1, "USDT"),
        ])
    )
    assert personal_data.resolve_sub_portfolios(master_pf, [sub_pf_1, sub_pf_2], [], [], {}) == (
        _sub_pf(0, _content_with_available({"BTC": (0, 0), "ETH": (0, 0), "USDT": (0, 0)})),
        [
            _sub_pf(0, _content_with_available({"BTC": (0.004998, 0.085), "ETH": (0.1, 0.1)})),
            _sub_pf(0, _content_with_available({"BTC": (0.015, 0.015), "USDT": (0, 100)}))
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
                funds_deltas={},
                missing_funds=_missing_funds({"TRX": 11, "USDT": 40}),
            ),
            _sub_pf(
                5,
                _content({"ADA": 0, "ETH": 1, "USDC": 0, "USDT": 0}),
                funds_deltas={},
                missing_funds=_missing_funds({"ADA": 1199, "USDT": 4}),
            ),
        ]
    )


def test_get_portfolio_filled_orders_deltas():
    pre_trade_content = _content({"BTC": 0.1, "USDT": 1000})
    post_trade_content = _content({"BTC": 0.2, "USDT": 500})
    error_log = mock.Mock()
    with mock.patch.object(octobot_commons.logging, "get_logger", mock.Mock(return_value=mock.Mock(error=error_log))):
        # no filled order
        assert personal_data.get_portfolio_filled_orders_deltas(pre_trade_content, post_trade_content, []) == (
            {}, {}
        )
        error_log.assert_not_called()

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
        error_log.assert_not_called()

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
        error_log.assert_not_called()

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
        error_log.assert_not_called()

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
        error_log.assert_not_called()

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
        error_log.assert_not_called()


def test_get_portfolio_filled_orders_deltas_considering_fees():
    pre_trade_content = _content({"BTC": 0.1, "USDT": 600.2})
    post_trade_content = _content({"BTC": 0.2, "USDT": 50.2})    # paid 50 USDT in fees
    error_log = mock.Mock()
    with mock.patch.object(octobot_commons.logging, "get_logger", mock.Mock(return_value=mock.Mock(error=error_log))):
        # no filled order
        assert personal_data.get_portfolio_filled_orders_deltas(pre_trade_content, post_trade_content, []) == (
            {}, {}
        )
        error_log.assert_not_called()

        # with fees: delta is found
        filled_orders = [
            _order("BTC/USDT", 0.06, 100, "buy", {"USDT": 25}),
            _order("BTC/USDT", 0.05, 450, "buy", {"USDT": 25}),
            _order("BTC/USDT", 0.01, 50, "sell", {"BTC": 0.0000001}),
        ]
        assert personal_data.get_portfolio_filled_orders_deltas(
            pre_trade_content, post_trade_content, filled_orders
        ) == (
            # all orders found in deltas because fees have been taken into account
            _content({"BTC": 0.1, "USDT": -550}),
            {}
        )
        error_log.assert_not_called()

        # without fees explanation
        filled_orders = [
            _order("BTC/USDT", 0.06, 100, "buy", {"USDT": 0.025}),
            _order("BTC/USDT", 0.05, 450, "buy", {"USDT": 0.025}),
            _order("BTC/USDT", 0.01, 50, "sell", {"BTC": 0.0000001}),
        ]
        assert personal_data.get_portfolio_filled_orders_deltas(
            pre_trade_content, post_trade_content, filled_orders
        ) == (
            # fees can't explain the additional -50 only consider -500
            _content({"BTC": 0.1, "USDT": -500}),
            {}
        )
        error_log.assert_not_called()

        # with small numbers
        pre_trade_content = _content({"BTC": 0.1, "USDT": 0.2})
        post_trade_content = _content({"BTC": 0.089, "USDT": 0.1})    # paid 0.1 USDT and 0.001 BTC in fees
        filled_orders = [
            _order("BTC/USDT", 0.1, 100, "sell", {"USDT": 0.1}),
            _order("BTC/USDT", 0.09, 100, "buy", {"BTC": 0.001}),
        ]
        assert personal_data.get_portfolio_filled_orders_deltas(
            pre_trade_content, post_trade_content, filled_orders
        ) == (
            _content({"BTC": -0.011, "USDT": -0.1}),
            {}
        )
        error_log.assert_not_called()

        # with USDT holdings increasing

        # A. return ignored assets because no explaining fees
        pre_trade_content = _content({"BTC": 0.1, "USDT": 0.2})
        post_trade_content = _content({"BTC": 0.089, "USDT": 0.8})
        filled_orders = [
            _order("BTC/USDT", 0.1, 100, "sell", {"USDT": 0.000001}),
            _order("BTC/USDT", 0.09, 99.3, "buy", {"BTC": 0.000000001}),
        ]
        assert personal_data.get_portfolio_filled_orders_deltas(
            pre_trade_content, post_trade_content, filled_orders
        ) == (
            # 0.6 is NOT explained by 0.7 from order delta - 0.000001 fees
            _content({"BTC": -0.01}),   # takes a bit too much of post trade portfolio (fees are not considered),
            # will be adapted later on if necessary
            _content({"USDT": 0.6}) # ignored assets
        )
        error_log.assert_not_called()

        # B. success with  explaining fees
        pre_trade_content = _content({"BTC": 0.1, "USDT": 0.2})
        post_trade_content = _content({"BTC": 0.089, "USDT": 0.8})
        filled_orders = [
            _order("BTC/USDT", 0.1, 100, "sell", {"USDT": 0.1}),
            _order("BTC/USDT", 0.09, 99.3, "buy", {"BTC": 0.001}),
        ]
        assert personal_data.get_portfolio_filled_orders_deltas(
            pre_trade_content, post_trade_content, filled_orders
        ) == (
            # 0.6 is explained by 0.7 from order delta - 0.1 fees
            _content({"BTC": -0.011, "USDT": 0.6}),
            {}
        )
        error_log.assert_not_called()


def test_resolve_sub_portfolios_with_filling_assets_with_locked_funds():
    master_pf = _sub_pf(
        0,
        _content_with_available({
            "BTC": (0.019998, 0.1), "ETH": (0.019998, 0.1), "USDT": (10.019998, 10.1), "SOL": (0.5, 1), "USDC": (2, 2)
        })
    )
    filling_assets = ["USDC", "SOL"]
    market_prices = {
        "SOL/USDT": 150,
        "BTC/USDC": 83000,
        "ETH/USDC": 2000,
        "USDT/USDC": 1,
    }
    sub_pf_btc = _sub_pf(
        0, _content({"BTC": 0.1}),
        locked_funds_by_asset = trading_api.get_orders_locked_amounts_by_asset([
            _open_order("BTC/USDT", 0.06, 400, "sell", 0.000001, "BTC"),
            _open_order("BTC/USDT", 0.02, 600, "sell", 0.000001, "BTC"),
        ])
    )
    # nothing to fill
    assert personal_data.resolve_sub_portfolios(master_pf, [sub_pf_btc], filling_assets, [], market_prices) == (
        _sub_pf(0, _content_with_available({
            "BTC": (0, 0), "ETH": (0.019998, 0.1), "USDT": (10.019998, 10.1), "SOL": (0.5, 1), "USDC": (2, 2)
        })),
        [_sub_pf(0, _content_with_available({"BTC": (0.019998, 0.1)}))]
    )

    master_pf = _sub_pf(
        0,
        _content_with_available({
            "BTC": (0.019998, 0.1), "ETH": (0.019998, 0.1), "USDT": (10.019998, 10.1), "SOL": (0.5, 1), "USDC": (2, 2)
        })
    )
    sub_pf_missing_usdt = _sub_pf(
        1, _content_with_available({"USDT": (140, 150), "SOL": (0, 0.5)}),
        locked_funds_by_asset = trading_api.get_orders_locked_amounts_by_asset([
            _open_order("BTC/USDT", 0.01, 10, "buy", 0.000001, "BTC"),
            _open_order("SOL/USDT", 0.5, 1, "sell", 0.000001, "USDT"),
        ])
    )
    # fill with locked amount
    assert personal_data.resolve_sub_portfolios(master_pf, [sub_pf_btc, sub_pf_missing_usdt], filling_assets, [], market_prices) == (
        _sub_pf(0, _content_with_available({
            "BTC": (0, 0), "ETH": (0.019998, 0.1), "USDT": (0, 0), "SOL": (0, 0), "USDC": (0, 0)
        })),
        [
            _sub_pf(0, _content_with_available({"BTC": (0.019998, 0.1)})),
            _sub_pf(
                1,
                _content_with_available({"USDT": (10.019998, 10.1), "SOL": (0.5, 1), "USDC": (2, 2)}),
                funds_deltas=_content_with_available({
                    "SOL": (0.5, 0.5), "USDC": (2, 2)
                }),
                missing_funds=_missing_funds({
                    "USDT": float(
                        decimal.Decimal(140)
                        - decimal.Decimal("10.019998")
                        - decimal.Decimal(str(market_prices["SOL/USDT"])) / decimal.Decimal("2")
                        - decimal.Decimal(market_prices["USDT/USDC"] * 2)
                    )
                })
            )
        ]
    )



def _sub_pf(
    priority_key: float,
    content: dict[str, dict[str, decimal.Decimal]],
    funds_deltas: dict[str, dict[str, decimal.Decimal]] = None,
    missing_funds: dict[str, decimal.Decimal] = None,
    locked_funds_by_asset: dict[str, decimal.Decimal] = None,
) -> personal_data.SubPortfolioData:
    return personal_data.SubPortfolioData(
        "", "", priority_key, content, "", funds_deltas or {}, missing_funds or {}, locked_funds_by_asset or {}
    )

def _content(content: dict[str, float]) -> dict[str, dict[str, decimal.Decimal]]:
    return {
        key: {
            octobot_commons.constants.PORTFOLIO_TOTAL: decimal.Decimal(str(val)),
            octobot_commons.constants.PORTFOLIO_AVAILABLE: decimal.Decimal(str(val)),
        }
        for key, val in content.items()
    }

def _content_with_available(content: dict[str, (float, float)]) -> dict[str, dict[str, decimal.Decimal]]:
    return {
        key: {
            octobot_commons.constants.PORTFOLIO_TOTAL: decimal.Decimal(str(total)),
            octobot_commons.constants.PORTFOLIO_AVAILABLE: decimal.Decimal(str(available)),
        }
        for key, (available, total) in content.items()
    }

def _missing_funds(funds: dict[str, float]) -> dict[str, decimal.Decimal]:
    return {
        key: decimal.Decimal(str(val))
        for key, val in funds.items()
    }

def _order(symbol: str, quantity: float, cost: float, side: str, fee: dict = None) -> personal_data.Order:
    trader = mock.Mock(exchange_manager=mock.Mock())
    order = personal_data.Order(trader)
    order.symbol = symbol
    order.origin_quantity = decimal.Decimal(str(quantity))
    order.total_cost = decimal.Decimal(str(cost))
    order.origin_price = order.total_cost / order.origin_quantity
    order.side = enums.TradeOrderSide(side)
    order.get_computed_fee = mock.Mock(return_value={
        enums.FeePropertyColumns.COST.value: decimal.Decimal(str(next(iter(fee.values())) if fee else 0)),
        enums.FeePropertyColumns.CURRENCY.value: next(iter(fee.keys())) if fee else None,
        enums.FeePropertyColumns.IS_FROM_EXCHANGE.value: False,
    })
    return order

def _open_order(symbol: str, quantity: float, cost: float, side: str, fee_cost: float, fee_unit: str) -> personal_data.Order:
    order = _order(symbol, quantity, cost, side)
    order.is_filled = mock.Mock(return_value=False)
    order.get_computed_fee = mock.Mock(
        return_value={
            enums.FeePropertyColumns.CURRENCY.value: fee_unit,
            enums.FeePropertyColumns.COST.value: decimal.Decimal(str(fee_cost)),
        }
    )
    return order

def _locked_amounts_by_asset(amount_by_asset: dict[str, float]) -> dict[str, decimal.Decimal]:
    return {
        asset: decimal.Decimal(str(amount))
        for asset, amount in amount_by_asset.items()
    }
