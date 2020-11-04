# pylint: disable=E0611
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
import ccxt.async_support as ccxt
import typing

import octobot_trading.enums as enums
import octobot_trading.errors as errors
import octobot_trading.exchanges.types as exchanges_types
import octobot_trading.exchanges.implementations as exchange_implementations
from octobot_trading.enums import ExchangeConstantsOrderColumns as ecoc


class SpotCCXTExchange(exchange_implementations.CCXTExchange, exchanges_types.SpotExchange):
    async def create_order(self, order_type: enums.TraderOrderType, symbol: str, quantity: float,
                           price: float = None, stop_price=None, **kwargs: dict) -> typing.Optional[dict]:
        try:
            created_order = await self._create_specific_order(order_type, symbol, quantity, price)
            # some exchanges are not returning the full order details on creation: fetch it if necessary
            if created_order and not SpotCCXTExchange._ensure_order_details_completeness(created_order):
                if ecoc.ID.value in created_order:
                    order_symbol = created_order[ecoc.SYMBOL.value] if ecoc.SYMBOL.value in created_order else None
                    created_order = await self.exchange_manager.exchange.get_order(created_order[ecoc.ID.value],
                                                                                   order_symbol, **kwargs)

            # on some exchange, market order are not not including price, add it manually to ensure uniformity
            if created_order[ecoc.PRICE.value] is None and price is not None:
                created_order[ecoc.PRICE.value] = price

            return self.clean_order(created_order)

        except ccxt.InsufficientFunds as e:
            self._log_error(e, order_type, symbol, quantity, price, stop_price)
            self.logger.warning(str(e))
            raise errors.MissingFunds(e)
        except ccxt.NotSupported:
            raise errors.NotSupported
        except Exception as e:
            self._log_error(e, order_type, symbol, quantity, price, stop_price)
            self.logger.error(e)
        return None

    async def _create_specific_order(self, order_type, symbol, quantity, price=None):
        created_order = None
        if order_type == enums.TraderOrderType.BUY_MARKET:
            created_order = await self.client.create_market_buy_order(symbol, quantity)
        elif order_type == enums.TraderOrderType.BUY_LIMIT:
            created_order = await self.client.create_limit_buy_order(symbol, quantity, price)
        elif order_type == enums.TraderOrderType.SELL_MARKET:
            created_order = await self.client.create_market_sell_order(symbol, quantity)
        elif order_type == enums.TraderOrderType.SELL_LIMIT:
            created_order = await self.client.create_limit_sell_order(symbol, quantity, price)
        elif order_type == enums.TraderOrderType.STOP_LOSS:
            created_order = None
        elif order_type == enums.TraderOrderType.STOP_LOSS_LIMIT:
            created_order = None
        elif order_type == enums.TraderOrderType.TAKE_PROFIT:
            created_order = None
        elif order_type == enums.TraderOrderType.TAKE_PROFIT_LIMIT:
            created_order = None
        elif order_type == enums.TraderOrderType.TRAILING_STOP:
            created_order = None
        elif order_type == enums.TraderOrderType.TRAILING_STOP_LIMIT:
            created_order = None
        return created_order

    @staticmethod
    def _ensure_order_details_completeness(order, order_required_fields=None):
        if order_required_fields is None:
            order_required_fields = [ecoc.ID.value, ecoc.TIMESTAMP.value, ecoc.SYMBOL.value, ecoc.TYPE.value,
                                     ecoc.SIDE.value, ecoc.PRICE.value, ecoc.AMOUNT.value, ecoc.REMAINING.value]
        return all(key in order for key in order_required_fields)
