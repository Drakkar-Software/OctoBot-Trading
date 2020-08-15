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

dist.Distribution().fetch_build_eggs(['Cython>=0.29.21', 'numpy>=1.19.1'])

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

packages_list = ["octobot_trading.util.initializable",
                 "octobot_trading.consumers.abstract_mode_consumer",
                 "octobot_trading.producers.balance_updater",
                 "octobot_trading.producers.funding_updater",
                 "octobot_trading.producers.ohlcv_updater",
                 "octobot_trading.producers.order_book_updater",
                 "octobot_trading.producers.kline_updater",
                 "octobot_trading.producers.abstract_mode_producer",
                 "octobot_trading.producers.orders_updater",
                 "octobot_trading.producers.positions_updater",
                 "octobot_trading.producers.prices_updater",
                 "octobot_trading.producers.recent_trade_updater",
                 "octobot_trading.producers.ticker_updater",
                 "octobot_trading.producers.trades_updater",
                 "octobot_trading.producers.simulator.funding_updater_simulator",
                 "octobot_trading.producers.simulator.ohlcv_updater_simulator",
                 "octobot_trading.producers.simulator.order_book_updater_simulator",
                 "octobot_trading.producers.simulator.kline_updater_simulator",
                 "octobot_trading.producers.simulator.orders_updater_simulator",
                 "octobot_trading.producers.simulator.positions_updater_simulator",
                 "octobot_trading.producers.simulator.prices_updater_simulator",
                 "octobot_trading.producers.simulator.recent_trade_updater_simulator",
                 "octobot_trading.producers.simulator.ticker_updater_simulator",
                 "octobot_trading.data.margin_portfolio",
                 "octobot_trading.data.order",
                 "octobot_trading.data.position",
                 "octobot_trading.data.trade",
                 "octobot_trading.data.portfolio",
                 "octobot_trading.data.portfolio_profitability",
                 "octobot_trading.data.sub_portfolio",
                 "octobot_trading.data_adapters.candles_adapter",
                 "octobot_trading.data_manager.candles_manager",
                 "octobot_trading.data_manager.funding_manager",
                 "octobot_trading.data_manager.orders_manager",
                 "octobot_trading.data_manager.positions_manager",
                 "octobot_trading.data_manager.kline_manager",
                 "octobot_trading.data_manager.trades_manager",
                 "octobot_trading.data_manager.portfolio_manager",
                 "octobot_trading.data_manager.price_events_manager",
                 "octobot_trading.data_manager.prices_manager",
                 "octobot_trading.data_manager.order_book_manager",
                 "octobot_trading.data_manager.ticker_manager",
                 "octobot_trading.data_manager.recent_trades_manager",
                 "octobot_trading.orders.order_adapter",
                 "octobot_trading.orders.order_factory",
                 "octobot_trading.orders.order_state",
                 "octobot_trading.orders.order_util",
                 "octobot_trading.orders.states.cancel_order_state",
                 "octobot_trading.orders.states.close_order_state",
                 "octobot_trading.orders.states.fill_order_state",
                 "octobot_trading.orders.states.open_order_state",
                 "octobot_trading.orders.states.order_state_factory",
                 "octobot_trading.orders.types.limit.limit_order",
                 "octobot_trading.orders.types.limit.buy_limit_order",
                 "octobot_trading.orders.types.limit.take_profit_order",
                 "octobot_trading.orders.types.limit.take_profit_limit_order",
                 "octobot_trading.orders.types.limit.sell_limit_order",
                 "octobot_trading.orders.types.limit.stop_loss_order",
                 "octobot_trading.orders.types.limit.stop_loss_limit_order",
                 "octobot_trading.orders.types.market.market_order",
                 "octobot_trading.orders.types.market.buy_market_order",
                 "octobot_trading.orders.types.market.sell_market_order",
                 "octobot_trading.orders.types.trailing.trailing_stop_order",
                 "octobot_trading.orders.types.trailing.trailing_stop_limit_order",
                 "octobot_trading.orders.types.unknown_order",
                 "octobot_trading.traders.trader",
                 "octobot_trading.traders.trader_simulator",
                 "octobot_trading.trades.trade_factory",
                 "octobot_trading.exchanges.exchange_manager",
                 "octobot_trading.exchanges.abstract_exchange",
                 "octobot_trading.exchanges.exchange_builder",
                 "octobot_trading.exchanges.exchanges",
                 "octobot_trading.exchanges.exchange_util",
                 "octobot_trading.exchanges.exchange_simulator",
                 "octobot_trading.exchanges.rest_exchange",
                 "octobot_trading.exchanges.types.future_exchange",
                 "octobot_trading.exchanges.types.margin_exchange",
                 "octobot_trading.exchanges.types.spot_exchange",
                 "octobot_trading.exchanges.types.websocket_exchange",
                 "octobot_trading.exchanges.data.exchange_personal_data",
                 "octobot_trading.exchanges.data.exchange_config_data",
                 "octobot_trading.exchanges.data.exchange_symbol_data",
                 "octobot_trading.exchanges.data.exchange_symbols_data",
                 "octobot_trading.exchanges.util.exchange_market_status_fixer",
                 "octobot_trading.exchanges.websockets.abstract_websocket",
                 "octobot_trading.exchanges.websockets.octobot_websocket",
                 "octobot_trading.exchanges.websockets.websockets_util",
                 "octobot_trading.channels.exchange_channel",
                 "octobot_trading.channels.balance",
                 "octobot_trading.channels.funding",
                 "octobot_trading.channels.kline",
                 "octobot_trading.channels.mode",
                 "octobot_trading.channels.ohlcv",
                 "octobot_trading.channels.order_book",
                 "octobot_trading.channels.orders",
                 "octobot_trading.channels.positions",
                 "octobot_trading.channels.price",
                 "octobot_trading.channels.recent_trade",
                 "octobot_trading.channels.ticker",
                 "octobot_trading.channels.trades"]

ext_modules = [
    Extension(package, [f"{package.replace('.', '/')}.py"], include_dirs=[np.get_include()])
    for package in packages_list]

# long description from README file
with open('README.md', encoding='utf-8') as f:
    DESCRIPTION = f.read()

REQUIRED = open('requirements.txt').readlines()
REQUIRES_PYTHON = '>=3.7'
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
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Cython',
        'Operating System :: OS Independent',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX'
    ],
)
