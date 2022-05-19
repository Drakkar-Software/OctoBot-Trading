#  Drakkar-Software OctoBot-Commons
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
# from distutils.extension import Extension
import os

from setuptools import dist

dist.Distribution().fetch_build_eggs(['Cython>=0.29.26', 'numpy==1.22.0'])

import numpy as np

try:
    from Cython.Distutils import build_ext
    from Cython.Build import cythonize
except ImportError:
    # create closure for deferred import
    def cythonize(*args, **kwargs):
        from Cython.Build import cythonize
        return cythonize(*args, **kwargs)


    def build_ext(*args, **kwargs):
        from Cython.Distutils import build_ext
        return build_ext(*args, **kwargs)

from setuptools import find_packages
from setuptools import setup, Extension

from octobot_trading import PROJECT_NAME, VERSION

PACKAGES = find_packages(exclude=["tests"])

packages_list = [
    "octobot_trading.octobot_channel_consumer",
    "octobot_trading.util.initializable",
    "octobot_trading.util.config_util",
    "octobot_trading.exchange_data.exchange_symbols_data",
    "octobot_trading.exchange_data.exchange_symbol_data",
    "octobot_trading.exchange_data.ticker.ticker_manager",
    "octobot_trading.exchange_data.ticker.channel.ticker",
    "octobot_trading.exchange_data.ticker.channel.ticker_updater",
    "octobot_trading.exchange_data.ticker.channel.ticker_updater_simulator",
    "octobot_trading.exchange_data.contracts.margin_contract",
    "octobot_trading.exchange_data.contracts.future_contract",
    "octobot_trading.exchange_data.order_book.order_book_manager",
    "octobot_trading.exchange_data.order_book.channel.order_book",
    "octobot_trading.exchange_data.order_book.channel.order_book_updater_simulator",
    "octobot_trading.exchange_data.order_book.channel.order_book_updater",
    "octobot_trading.exchange_data.funding.funding_manager",
    "octobot_trading.exchange_data.funding.channel.funding",
    "octobot_trading.exchange_data.funding.channel.funding_updater",
    "octobot_trading.exchange_data.funding.channel.funding_updater_simulator",
    "octobot_trading.exchange_data.kline.kline_manager",
    "octobot_trading.exchange_data.kline.channel.kline",
    "octobot_trading.exchange_data.kline.channel.kline_updater",
    "octobot_trading.exchange_data.kline.channel.kline_updater_simulator",
    "octobot_trading.exchange_data.recent_trades.recent_trades_manager",
    "octobot_trading.exchange_data.recent_trades.channel.recent_trade",
    "octobot_trading.exchange_data.recent_trades.channel.recent_trade_updater_simulator",
    "octobot_trading.exchange_data.recent_trades.channel.recent_trade_updater",
    "octobot_trading.exchange_data.prices.price_events_manager",
    "octobot_trading.exchange_data.prices.prices_manager",
    "octobot_trading.exchange_data.prices.channel.price",
    "octobot_trading.exchange_data.prices.channel.prices_updater_simulator",
    "octobot_trading.exchange_data.prices.channel.prices_updater",
    "octobot_trading.exchange_data.ohlcv.candles_manager",
    "octobot_trading.exchange_data.ohlcv.candles_adapter",
    "octobot_trading.exchange_data.ohlcv.channel.ohlcv_updater",
    "octobot_trading.exchange_data.ohlcv.channel.ohlcv_updater_simulator",
    "octobot_trading.exchange_data.ohlcv.channel.ohlcv",
    "octobot_trading.personal_data.exchange_personal_data",
    "octobot_trading.personal_data.state",
    "octobot_trading.personal_data.trades.trades_manager",
    "octobot_trading.personal_data.trades.trade",
    "octobot_trading.personal_data.trades.trade_factory",
    "octobot_trading.personal_data.trades.channel.trades_updater",
    "octobot_trading.personal_data.trades.channel.trades",
    "octobot_trading.personal_data.orders.order",
    "octobot_trading.personal_data.orders.order_adapter",
    "octobot_trading.personal_data.orders.decimal_order_adapter",
    "octobot_trading.personal_data.orders.orders_manager",
    "octobot_trading.personal_data.orders.order_state",
    "octobot_trading.personal_data.orders.order_group",
    "octobot_trading.personal_data.orders.order_util",
    "octobot_trading.personal_data.orders.order_factory",
    "octobot_trading.personal_data.orders.groups.balanced_take_profit_and_stop_order_group",
    "octobot_trading.personal_data.orders.groups.one_cancels_the_other_order_group",
    "octobot_trading.personal_data.orders.states.fill_order_state",
    "octobot_trading.personal_data.orders.states.cancel_order_state",
    "octobot_trading.personal_data.orders.states.close_order_state",
    "octobot_trading.personal_data.orders.states.order_state_factory",
    "octobot_trading.personal_data.orders.states.open_order_state",
    "octobot_trading.personal_data.orders.types.unknown_order",
    "octobot_trading.personal_data.orders.types.market.buy_market_order",
    "octobot_trading.personal_data.orders.types.market.market_order",
    "octobot_trading.personal_data.orders.types.market.sell_market_order",
    "octobot_trading.personal_data.orders.types.trailing.trailing_stop_limit_order",
    "octobot_trading.personal_data.orders.types.trailing.trailing_stop_order",
    "octobot_trading.personal_data.orders.types.limit.take_profit_limit_order",
    "octobot_trading.personal_data.orders.types.limit.stop_loss_limit_order",
    "octobot_trading.personal_data.orders.types.limit.limit_order",
    "octobot_trading.personal_data.orders.types.limit.sell_limit_order",
    "octobot_trading.personal_data.orders.types.limit.stop_loss_order",
    "octobot_trading.personal_data.orders.types.limit.buy_limit_order",
    "octobot_trading.personal_data.orders.types.limit.take_profit_order",
    "octobot_trading.personal_data.orders.channel.orders_updater_simulator",
    "octobot_trading.personal_data.orders.channel.orders",
    "octobot_trading.personal_data.orders.channel.orders_updater",
    "octobot_trading.personal_data.portfolios.portfolio_value_holder",
    "octobot_trading.personal_data.portfolios.portfolio_manager",
    "octobot_trading.personal_data.portfolios.sub_portfolio",
    "octobot_trading.personal_data.portfolios.portfolio",
    "octobot_trading.personal_data.portfolios.asset",
    "octobot_trading.personal_data.portfolios.portfolio_factory",
    "octobot_trading.personal_data.portfolios.portfolio_profitability",
    "octobot_trading.personal_data.portfolios.portfolio_util",
    "octobot_trading.personal_data.portfolios.assets.future_asset",
    "octobot_trading.personal_data.portfolios.assets.margin_asset",
    "octobot_trading.personal_data.portfolios.assets.spot_asset",
    "octobot_trading.personal_data.portfolios.types.spot_portfolio",
    "octobot_trading.personal_data.portfolios.types.future_portfolio",
    "octobot_trading.personal_data.portfolios.types.margin_portfolio",
    "octobot_trading.personal_data.portfolios.channel.balance_updater",
    "octobot_trading.personal_data.portfolios.channel.balance_updater_simulator",
    "octobot_trading.personal_data.portfolios.channel.balance",
    "octobot_trading.personal_data.portfolios.history.historical_asset_value",
    "octobot_trading.personal_data.portfolios.history.historical_asset_value_factory",
    "octobot_trading.personal_data.portfolios.history.historical_portfolio_value_manager",
    "octobot_trading.personal_data.positions.position",
    "octobot_trading.personal_data.positions.position_factory",
    "octobot_trading.personal_data.positions.position_state",
    "octobot_trading.personal_data.positions.position_util",
    "octobot_trading.personal_data.positions.positions_manager",
    "octobot_trading.personal_data.positions.channel.positions",
    "octobot_trading.personal_data.positions.channel.positions_updater",
    "octobot_trading.personal_data.positions.channel.positions_updater_simulator",
    "octobot_trading.personal_data.positions.types.inverse_position",
    "octobot_trading.personal_data.positions.types.linear_position",
    "octobot_trading.personal_data.positions.states.liquidate_position_state",
    "octobot_trading.personal_data.positions.states.open_position_state",
    "octobot_trading.personal_data.positions.states.position_state_factory",
    "octobot_trading.personal_data.transactions.transaction",
    "octobot_trading.personal_data.transactions.transaction_factory",
    "octobot_trading.personal_data.transactions.transactions_manager",
    "octobot_trading.personal_data.transactions.types.blockchain_transaction",
    "octobot_trading.personal_data.transactions.types.fee_transaction",
    "octobot_trading.personal_data.transactions.types.realised_pnl_transaction",
    "octobot_trading.personal_data.transactions.types.transfer_transaction",
    "octobot_trading.modes.modes_factory",
    "octobot_trading.modes.modes_util",
    "octobot_trading.modes.channel.abstract_mode_producer",
    "octobot_trading.modes.channel.mode",
    "octobot_trading.modes.channel.abstract_mode_consumer",
    "octobot_trading.exchanges.exchanges",
    "octobot_trading.exchanges.exchange_manager",
    "octobot_trading.exchanges.abstract_exchange",
    "octobot_trading.exchanges.abstract_websocket_exchange",
    "octobot_trading.exchanges.basic_exchange_wrapper",
    "octobot_trading.exchanges.exchange_websocket_factory",
    "octobot_trading.exchanges.config.exchange_config_data",
    "octobot_trading.exchanges.config.backtesting_exchange_config",
    "octobot_trading.exchanges.exchange_builder",
    "octobot_trading.exchanges.exchange_channels",
    "octobot_trading.exchanges.exchange_factory",
    "octobot_trading.exchanges.connectors.ccxt_exchange",
    "octobot_trading.exchanges.connectors.exchange_simulator",
    "octobot_trading.exchanges.connectors.abstract_websocket_connector",
    "octobot_trading.exchanges.connectors.ccxt_websocket_connector",
    "octobot_trading.exchanges.connectors.cryptofeed_websocket_connector",
    "octobot_trading.exchanges.traders.trader",
    "octobot_trading.exchanges.traders.trader_simulator",
    "octobot_trading.exchanges.util.exchange_market_status_fixer",
    "octobot_trading.exchanges.util.websockets_util",
    "octobot_trading.exchanges.util.exchange_util",
    "octobot_trading.exchanges.types.spot_exchange",
    "octobot_trading.exchanges.types.margin_exchange",
    "octobot_trading.exchanges.types.future_exchange",
    "octobot_trading.exchanges.types.websocket_exchange",
    "octobot_trading.exchanges.implementations.future_ccxt_exchange",
    "octobot_trading.exchanges.implementations.future_exchange_simulator",
    "octobot_trading.exchanges.implementations.margin_ccxt_exchange",
    "octobot_trading.exchanges.implementations.margin_exchange_simulator",
    "octobot_trading.exchanges.implementations.spot_ccxt_exchange",
    "octobot_trading.exchanges.implementations.spot_exchange_simulator",
    "octobot_trading.exchanges.implementations.ccxt_websocket_exchange",
    "octobot_trading.exchanges.implementations.cryptofeed_websocket_exchange",
    # "octobot_trading.exchanges.implementations.default_spot_ccxt_exchange",
    "octobot_trading.exchange_channel",
    "octobot_trading.storage.run_databases_provider",
]

ext_modules = [
    Extension(package, [f"{package.replace('.', '/')}.py"], include_dirs=[np.get_include()])
    for package in packages_list]

# long description from README file
with open('README.md', encoding='utf-8') as f:
    DESCRIPTION = f.read()

REQUIRED = open('requirements.txt').readlines()
REQUIRES_PYTHON = '>=3.8'
CYTHON_DEBUG = False if not os.getenv('CYTHON_DEBUG') else os.getenv('CYTHON_DEBUG')

if CYTHON_DEBUG:
    from Cython.Compiler.Options import get_directive_defaults

    get_directive_defaults()['cache_builtins'] = False

setup(
    name=PROJECT_NAME,
    version=VERSION,
    url='https://github.com/Drakkar-Software/OctoBot-Trading',
    license='LGPL-3.0',
    author='Drakkar-Software',
    author_email='drakkar-software@protonmail.com',
    description='OctoBot project trading package',
    packages=PACKAGES,
    include_package_data=True,
    long_description=DESCRIPTION,
    include_dirs=[np.get_include()],
    cmdclass={'build_ext': build_ext},
    tests_require=["pytest"],
    test_suite="tests",
    zip_safe=False,
    data_files=[],
    setup_requires=REQUIRED,
    install_requires=REQUIRED,
    ext_modules=cythonize(ext_modules, gdb_debug=CYTHON_DEBUG),
    python_requires=REQUIRES_PYTHON,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Cython',
        'Operating System :: OS Independent',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX'
    ],
)
