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
from Cython.Build import cythonize
from Cython.Distutils import build_ext
from setuptools import find_packages
from setuptools import setup, Extension
import numpy as np
from octobot_trading import PROJECT_NAME, VERSION

PACKAGES = find_packages(exclude=["tests"])

packages_list: list = ["octobot_trading.util.initializable",
                       "octobot_trading.producers.balance_updater",
                       "octobot_trading.producers.ohlcv_updater",
                       "octobot_trading.producers.order_book_updater",
                       "octobot_trading.producers.kline_updater",
                       "octobot_trading.producers.orders_updater",
                       "octobot_trading.producers.positions_updater",
                       "octobot_trading.producers.recent_trade_updater",
                       "octobot_trading.producers.ticker_updater",
                       "octobot_trading.producers.trades_updater",
                       "octobot_trading.producers.simulator.balance_updater_simulator",
                       "octobot_trading.producers.simulator.ohlcv_updater_simulator",
                       "octobot_trading.producers.simulator.order_book_updater_simulator",
                       "octobot_trading.producers.simulator.kline_updater_simulator",
                       "octobot_trading.producers.simulator.orders_updater_simulator",
                       "octobot_trading.producers.simulator.positions_updater_simulator",
                       "octobot_trading.producers.simulator.recent_trade_updater_simulator",
                       "octobot_trading.producers.simulator.ticker_updater_simulator",
                       "octobot_trading.producers.simulator.trades_updater_simulator",
                       "octobot_trading.data.order",
                       "octobot_trading.data.position",
                       "octobot_trading.data.trade",
                       "octobot_trading.data.portfolio",
                       "octobot_trading.data.portfolio_profitability",
                       "octobot_trading.data.sub_portfolio",
                       "octobot_trading.data_manager.orders_manager",
                       "octobot_trading.data_manager.positions_manager",
                       "octobot_trading.data_manager.kline_manager",
                       "octobot_trading.data_manager.trades_manager",
                       "octobot_trading.data_manager.portfolio_manager",
                       "octobot_trading.data_manager.candles_manager",
                       "octobot_trading.data_manager.order_book_manager",
                       "octobot_trading.data_manager.ticker_manager",
                       "octobot_trading.data_manager.recent_trades_manager",
                       "octobot_trading.modes.abstract_mode_creator",
                       "octobot_trading.modes.abstract_mode_decider",
                       "octobot_trading.modes.abstract_trading_mode",
                       "octobot_trading.orders.buy_limit_order",
                       "octobot_trading.orders.buy_market_order",
                       "octobot_trading.orders.sell_limit_order",
                       "octobot_trading.orders.sell_market_order",
                       "octobot_trading.orders.stop_loss_limit_order",
                       "octobot_trading.orders.trailing_stop_order",
                       "octobot_trading.orders.stop_loss_order",
                       "octobot_trading.traders.trader",
                       "octobot_trading.traders.trader_simulator",
                       "octobot_trading.exchanges.exchange_manager",
                       "octobot_trading.exchanges.abstract_exchange",
                       "octobot_trading.exchanges.exchange_factory",
                       "octobot_trading.exchanges.rest_exchange",
                       "octobot_trading.exchanges.data.exchange_personal_data",
                       "octobot_trading.exchanges.data.exchange_symbol_data",
                       "octobot_trading.exchanges.data.exchange_symbols_data",
                       "octobot_trading.exchanges.util.exchange_market_status_fixer",
                       "octobot_trading.exchanges.websockets.abstract_websocket",
                       "octobot_trading.exchanges.websockets.octobot_websocket",
                       "octobot_trading.exchanges.websockets.websocket_callbacks",
                       "octobot_trading.channels.exchange_channel",
                       "octobot_trading.channels.balance",
                       "octobot_trading.channels.kline",
                       "octobot_trading.channels.ohlcv",
                       "octobot_trading.channels.order_book",
                       "octobot_trading.channels.orders",
                       "octobot_trading.channels.positions",
                       "octobot_trading.channels.recent_trade",
                       "octobot_trading.channels.ticker",
                       "octobot_trading.channels.trades",
                       "octobot_trading.exchanges.backtesting.backtesting",
                       "octobot_trading.exchanges.backtesting.exchange_simulator",
                       "octobot_trading.exchanges.backtesting.collector.data_file_manager",
                       "octobot_trading.exchanges.backtesting.collector.data_parser"]

ext_modules: list = [
    Extension(package, [f"{package.replace('.', '/')}.py"])
    for package in packages_list]

# long description from README file
with open('README.md', encoding='utf-8') as f:
    DESCRIPTION = f.read()

REQUIRED = open('requirements.txt').read()
REQUIRES_PYTHON = '>=3.7'

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
    install_requires=REQUIRED,
    include_dirs=[np.get_include()],
    cmdclass={'build_ext': build_ext},
    tests_require=["pytest"],
    test_suite="tests",
    zip_safe=False,
    data_files=[],
    setup_requires=['Cython', 'numpy'],
    python_requires=REQUIRES_PYTHON,
    ext_modules=cythonize(ext_modules),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Cython',
    ],
)
