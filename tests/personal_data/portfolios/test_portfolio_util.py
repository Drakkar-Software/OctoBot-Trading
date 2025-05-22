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


def test_resolve_sub_portfolios_with_unexpected_deltas():
    # more delta in post trade portfolio than actual orders => do not result in negative subportfolio
    master_pf = _sub_pf(0, _content({"BTC": 0.05, "TRX": 0, "USDT": 200}))
    sub_pft = _sub_pf(
        0,
        _content({"BTC": 0.05, "TRX": 13.1, "USDT": 100}),
        funds_deltas=_content({"BTC": -0.05, "TRX": -13.2, "USDT": 100}),
    )

    assert personal_data.resolve_sub_portfolios(master_pf, [sub_pft], [], [], {}) == (
        _sub_pf(0,  _content({"BTC": 0.05, "TRX": 0, "USDT": 0})),
        [_sub_pf(0, _content({"BTC": 0, "TRX": 0, "USDT": 200}))]
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

        # only equivalent sell and buy orders: no BTC delta
        pre_trade_content = _content({"BTC": 0.1, "USDT": 1000})
        post_trade_content = _content({"BTC": 0.1, "USDT": 995})  # now has SOL but no BTC
        filled_orders = [
            _order("BTC/USDT", 0.05, 550, "sell"),
            _order("BTC/USDT", 0.05, 555, "buy"),
        ]
        assert personal_data.get_portfolio_filled_orders_deltas(
            pre_trade_content, post_trade_content, filled_orders
        ) == (
            _content({"USDT": -5}),
            {}, # BTC is not a missing delta as there is no delta (delta = 0)
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

        # B. success with explaining fees
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

        # only equivalent sell and buy orders: no BTC delta
        pre_trade_content = _content({"BTC": 0.1, "USDT": 1000})
        post_trade_content = _content({"BTC": 0.1, "USDT": 995})
        filled_orders = [
            _order("BTC/USDT", 0.05, 550, "sell", {"USDT": 1}),
            _order("BTC/USDT", 0.05, 553, "buy", {"USDT": 1}),
        ]
        assert personal_data.get_portfolio_filled_orders_deltas(
            pre_trade_content, post_trade_content, filled_orders
        ) == (
            _content({"USDT": -5}),
            {}, # BTC is not a missing delta as there is no delta (delta = 0)
        )
        error_log.assert_not_called()

        # actual fee currency is different from expected fee currency, delta is explained by these fees
        BTC_fees = 0.00000109889 # 10% of computed BTC delta is fees but it's only fetched from portfolio, not expected order fees
        pre_trade_content = _content({"BTC": 0.00226262681, "USDT": 4376.532183487584})
        post_trade_content = _content({"BTC": 0.00227318792 - BTC_fees, "USDT": 4375.22614367084})
        filled_orders = [
            _order("BTC/USDT", 0.00108723, 111.778333746, "sell", {"USDT": 0.111778333746}),
            _order("BTC/USDT", 0.00109889, 112.972595229, "buy", {"USDT": 0.111778333746}), # expects USDT as fees but was actually BTC
        ]
        assert personal_data.get_portfolio_filled_orders_deltas(
            pre_trade_content, post_trade_content, filled_orders
        ) == (
            # BTC delta from unexpected fees are taken into account and don't create missing deltas
            _content({"BTC": 0.00000946222, "USDT": -1.306039816744}),
            {},
        )
        error_log.assert_not_called()

        # actual fee currency is different from expected fee currency, delta is explained by these fees
        pre_trade_content = _content({"BTC": 0.00226262681, "USDT": 4376.532183487584})
        post_trade_content = _content({"BTC": 0.00227318792, "USDT": 4375.22614367084})
        filled_orders = [
            _order("BTC/USDT", 0.00108723, 111.778333746, "sell", {"USDT": 0.111778333746}), # expects USDT as fees but was actually something else (like BNB)
            _order("BTC/USDT", 0.00109779111, 112.972595229, "buy", {"USDT": 0.111778333746}), # expects USDT as fees but was actually something else (like BNB)
        ]
        assert personal_data.get_portfolio_filled_orders_deltas(
            pre_trade_content, post_trade_content, filled_orders
        ) == (
            # USDT delta == 4375.22614367084 - 4376.532183487584
            _content({"USDT": -1.306039816744, "BTC": 0.00001056111}),
            {},
        )
        error_log.assert_not_called()

        actual_fees = 0.2775394125  # 0.6% fees
        # actual fees is much smaller than expected, portfolio delta is accepted
        pre_trade_content = _content({"MANA": 103.42087452540375, "USDC": actual_fees})
        post_trade_content = _content({"MANA": 72.65087452540375, "USDC": 0.0827944124999931})
        filled_orders = [
            _order("MANA/USDC", 103.05, 37.005255, "sell", {"USDC": actual_fees * 2}), # expects 1.2% fees
            _order("MANA/USDC", 72.28, 36.644921175, "buy", {"USDC": actual_fees * 2}),    # expects 1.2% fees
        ]
        assert personal_data.get_portfolio_filled_orders_deltas(
            pre_trade_content, post_trade_content, filled_orders
        ) == (
            # USDC delta from portfolio is accepted and not considered as missing
            _content({"MANA": -30.77, "USDC": -0.1947450000000069}),
            {},
        )
        error_log.assert_not_called()


def test_get_portfolio_filled_orders_deltas_considering_different_fee_tiers():
    error_log = mock.Mock()
    with mock.patch.object(octobot_commons.logging, "get_logger", mock.Mock(return_value=mock.Mock(error=error_log))):
        # base 1.2% fees
        pre_trade_usdc = 2.203362439822
        pre_trade_content = _content({"ETH": 0.01145892, "USDC": pre_trade_usdc, 'BTC': 0.01937857})
        filled_orders = [
            _order("BTC/USDC", 0.00091181, 99.2684993932, "sell", {"USDC": 1.1912219927184}),
            _order("XRP/USDC", 3.840399, 9.1942992459, "buy", {"USDC": 0.1103315909508}),
            _order("XLM/USDC", 33.59950349, 9.79704799822749, "buy", {"USDC": 0.11756457597873}),
            _order("SUI/USDC", 2.4, 9.35448, "buy", {"USDC": 0.11225376}),
            _order("SOL/USDC", 0.05705159, 9.78999848, "buy", {"USDC": 0.11747998176}),
            _order("LINK/USDC", 0.61, 9.73987, "buy", {"USDC": 0.11687844}),
            _order("ETH/USDC", 0.00387595, 9.7899907885, "buy", {"USDC": 0.117479889462}),
            _order("DOGE/USDC", 42.3, 9.778068, "buy", {"USDC": 0.117336816}),
            _order("BTC/USDC", 0.00008992, 9.7895661216, "buy", {"USDC": 0.1174747934592}),
            _order("AVAX/USDC", 0.42769768, 9.7899998952, "buy", {"USDC": 0.1174799987424}),
            _order("ADA/USDC", 12.75318927, 9.796999997214, "buy", {"USDC": 0.117563999966568}),
        ]
        max_fees_deltas = {
            "XRP": 3.840399, "SUI": 2.4, "XLM": 33.59950349, "SOL": 0.05705159, "LINK": 0.61, "DOGE": 42.3,
            "AVAX": 0.42769768, "ADA": 12.75318927, "ETH": 0.00387595, "USDC": 0.095113027520412,
            "BTC": -0.00082189
        }
        post_trade_content = _content({
            "XRP": 3.840399, "SUI": 2.4, "XLM": 33.59950349, "SOL": 0.05705159, "LINK": 0.61, "DOGE": 42.3,
            "AVAX": 0.42769768, "ADA": 12.75318927, "ETH": 0.01533487, "USDC": 2.298475467342412, "BTC": 0.01855668
        })
        assert personal_data.get_portfolio_filled_orders_deltas(
            pre_trade_content, post_trade_content, filled_orders
        ) == (_content(max_fees_deltas), {})
        error_log.assert_not_called()

        # use coinbase fees tiers for this test
        expected_fees_percent = 1.2
        for real_fee_percent in (1.2, 0.75, 0.4, 0.25, 0.20, 0.16, 0.14, 0.10, 0.08, 0.05):
            total_real_paid_fees = [decimal.Decimal(0)]

            def _get_expected_fees(cost):
                real_paid_fees = decimal.Decimal(str(cost)) * decimal.Decimal(str(real_fee_percent)) / decimal.Decimal(100)
                expected_paid_fees = decimal.Decimal(str(cost)) * decimal.Decimal(str(expected_fees_percent)) / decimal.Decimal(100)
                total_real_paid_fees[0] = total_real_paid_fees[0] + real_paid_fees
                # expected fees are always 1.2%
                return float(expected_paid_fees)

            filled_orders = [
                _order("BTC/USDC", 0.00091181, 99.2684993932, "sell", {"USDC": _get_expected_fees(99.2684993932)}),
                _order("XRP/USDC", 3.840399, 9.1942992459, "buy", {"USDC": _get_expected_fees(9.1942992459)}),
                _order("XLM/USDC", 33.59950349, 9.79704799822749, "buy", {"USDC": _get_expected_fees(9.79704799822749)}),
                _order("SUI/USDC", 2.4, 9.35448, "buy", {"USDC": _get_expected_fees(9.35448)}),
                _order("SOL/USDC", 0.05705159, 9.78999848, "buy", {"USDC": _get_expected_fees(9.78999848)}),
                _order("LINK/USDC", 0.61, 9.73987, "buy", {"USDC": _get_expected_fees(9.73987)}),
                _order("ETH/USDC", 0.00387595, 9.7899907885, "buy", {"USDC": _get_expected_fees(9.7899907885)}),
                _order("DOGE/USDC", 42.3, 9.778068, "buy", {"USDC": _get_expected_fees(9.778068)}),
                _order("BTC/USDC", 0.00008992, 9.7895661216, "buy", {"USDC": _get_expected_fees(9.7895661216)}),
                _order("AVAX/USDC", 0.42769768, 9.7899998952, "buy", {"USDC": _get_expected_fees(9.7899998952)}),
                _order("ADA/USDC", 12.75318927, 9.796999997214, "buy", {"USDC": _get_expected_fees(9.796999997214)}),
            ]

            post_trade_usdc = (
                decimal.Decimal(str(pre_trade_usdc))
                + sum(decimal.Decimal(str(o.total_cost)) for o in filled_orders if o.side == enums.TradeOrderSide.SELL)
                - sum(decimal.Decimal(str(o.total_cost)) for o in filled_orders if o.side == enums.TradeOrderSide.BUY)
                - total_real_paid_fees[0]
            )
            post_trade_content = _content({
                "XRP": 3.840399, "SUI": 2.4, "XLM": 33.59950349, "SOL": 0.05705159, "LINK": 0.61, "DOGE": 42.3,
                "AVAX": 0.42769768, "ADA": 12.75318927, "ETH": 0.01533487, "USDC": float(post_trade_usdc), "BTC": 0.01855668
            })
            local_fees_deltas = {
                "XRP": 3.840399, "SUI": 2.4, "XLM": 33.59950349, "SOL": 0.05705159, "LINK": 0.61, "DOGE": 42.3,
                "AVAX": 0.42769768, "ADA": 12.75318927, "ETH": 0.00387595, "BTC": -0.00082189,
                "USDC": float(post_trade_usdc - decimal.Decimal(str(pre_trade_usdc))),
            }

            if real_fee_percent == 1.2:
                # same result as previous (non looping) test
                assert personal_data.get_portfolio_filled_orders_deltas(
                    pre_trade_content, post_trade_content, filled_orders
                ) == (_content(max_fees_deltas), {})
            else:
                deltas, missing_deltas = personal_data.get_portfolio_filled_orders_deltas(
                    pre_trade_content, post_trade_content, filled_orders
                )
                # fix rounding issues
                local_fees_deltas["USDC"] = float(round(decimal.Decimal(local_fees_deltas["USDC"]), 8))
                assert missing_deltas == {}, f"{real_fee_percent=} {missing_deltas=}"
                for key in (octobot_commons.constants.PORTFOLIO_AVAILABLE, octobot_commons.constants.PORTFOLIO_TOTAL):
                    deltas["USDC"][key] = round(deltas["USDC"][key], 8)
                assert deltas == _content(local_fees_deltas), f"{real_fee_percent=}"

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
