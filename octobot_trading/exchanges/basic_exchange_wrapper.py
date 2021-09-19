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
import contextlib
import ccxt.async_support
import ccxt

import octobot_trading.enums as enums


class BasicExchangeWrapper:
    def __init__(self, exchange_class_string: str, exchange_lib: enums.ExchangeWrapperLibs):
        """
        Always call self.stop() when done with an async ccxt exchange wrapper
        :param exchange_class_string: name of the exchange to create
        :param exchange_lib: lib to use to connect to the exchange
        """
        self.exchange_class_string = exchange_class_string
        self.exchange_lib = exchange_lib
        self.exchange = None

        self._exchange_factory()

    async def get_available_time_frames(self):
        if self.exchange_lib in (enums.ExchangeWrapperLibs.CCXT, enums.ExchangeWrapperLibs.ASYNC_CCXT):
            return self.exchange.timeframes

    async def stop(self):
        if self.exchange_lib is enums.ExchangeWrapperLibs.ASYNC_CCXT:
            await self.exchange.close()

    def _exchange_factory(self):
        if self.exchange_lib is enums.ExchangeWrapperLibs.ASYNC_CCXT:
            self.exchange = getattr(ccxt.async_support, self.exchange_class_string)()
        elif self.exchange_lib is enums.ExchangeWrapperLibs.CCXT:
            self.exchange = getattr(ccxt, self.exchange_class_string)()
        else:
            raise NotImplementedError(
                f"{self.exchange_lib} exchange lib is not implemented in {self.__class__.__name__}")


@contextlib.asynccontextmanager
async def temporary_exchange_wrapper(exchange_class_string: str, exchange_lib: enums.ExchangeWrapperLibs):
    """
    Automatically call to on exchange wrapper
    :param exchange_class_string: name of the exchange to create
    :param exchange_lib: lib to use to connect to the exchange
    :return:
    """
    wrapper = BasicExchangeWrapper(exchange_class_string, exchange_lib)
    try:
        yield wrapper
    finally:
        await wrapper.stop()
