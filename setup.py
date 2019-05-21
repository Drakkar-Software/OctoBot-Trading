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

from octobot_trading import PROJECT_NAME, VERSION

PACKAGES = find_packages(exclude=["tests"])

packages_list = ["octobot_trading.producers.balance_updater",
                 "octobot_trading.producers.exchange_updater",
                 "octobot_trading.producers.ohlcv_updater",
                 "octobot_trading.producers.order_book_updater",
                 "octobot_trading.producers.orders_updater",
                 "octobot_trading.producers.recent_trade_updater",
                 "octobot_trading.producers.ticker_updater",
                 "octobot_trading.producers.simulator.exchange_updater_simulator"]

PACKAGE_DATA = {
    package: [f"{package.replace('.', '/')}.pxd"]
    for package in packages_list
}

ext_modules = [
    Extension(package, [f"{package.replace('.', '/')}.pyx"], include_dirs=['.'])
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
    package_data=PACKAGE_DATA,
    include_package_data=True,
    long_description=DESCRIPTION,
    install_requires=REQUIRED,
    cmdclass={'build_ext': build_ext},
    tests_require=["pytest"],
    test_suite="tests",
    zip_safe=False,
    data_files=[],
    setup_requires=['Cython'],
    python_requires=REQUIRES_PYTHON,
    ext_modules=cythonize(ext_modules),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Cython',
    ],
)
