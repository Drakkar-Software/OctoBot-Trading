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
from ccxt import NotSupported, InsufficientFunds

from octobot_trading import errors
from octobot_trading.enums import TraderOrderType, ExchangeConstantsOrderColumns as ecoc
from octobot_trading.errors import MissingFunds
from octobot_trading.exchanges.implementations.ccxt_exchange import CCXTExchange
from octobot_trading.exchanges.types.spot_exchange import SpotExchange


class SpotCCXTExchange(CCXTExchange, SpotExchange):
    async def create_order(self, order_type: TraderOrderType, symbol: str, quantity: float,
                           price: float = None, stop_price=None, **kwargs: dict) -> dict:
        try:
            created_order = await self._create_specific_order(order_type, symbol, quantity, price)
            # some exchanges are not returning the full order details on creation: fetch it if necessary
            if created_order and not SpotCCXTExchange._ensure_order_details_completeness(created_order):
                if ecoc.ID.value in created_order:
                    order_symbol = created_order[ecoc.SYMBOL.value] if ecoc.SYMBOL.value in created_order else None
                    created_order = await self.exchange_manager.get_exchange().get_order(created_order[ecoc.ID.value],
                                                                                         order_symbol, params=kwargs)

            # on some exchange, market order are not not including price, add it manually to ensure uniformity
            if created_order[ecoc.PRICE.value] is None and price is not None:
                created_order[ecoc.PRICE.value] = price

            return self.clean_order(created_order)

        except InsufficientFunds as e:
            self._log_error(e, order_type, symbol, quantity, price, stop_price)
            self.logger.warning(e)
            raise MissingFunds(e)
        except NotSupported:
            raise errors.NotSupported
        except Exception as e:
            self._log_error(e, order_type, symbol, quantity, price, stop_price)
            self.logger.error(e)
        return None

    async def _create_specific_order(self, order_type, symbol, quantity, price=None):
        created_order = None
        if order_type == TraderOrderType.BUY_MARKET:
            created_order = await self.client.create_market_buy_order(symbol, quantity)
        elif order_type == TraderOrderType.BUY_LIMIT:
            created_order = await self.client.create_limit_buy_order(symbol, quantity, price)
        elif order_type == TraderOrderType.SELL_MARKET:
            created_order = await self.client.create_market_sell_order(symbol, quantity)
        elif order_type == TraderOrderType.SELL_LIMIT:
            created_order = await self.client.create_limit_sell_order(symbol, quantity, price)
        elif order_type == TraderOrderType.STOP_LOSS:
            created_order = None
        elif order_type == TraderOrderType.STOP_LOSS_LIMIT:
            created_order = None
        elif order_type == TraderOrderType.TAKE_PROFIT:
            created_order = None
        elif order_type == TraderOrderType.TAKE_PROFIT_LIMIT:
            created_order = None
        elif order_type == TraderOrderType.TRAILING_STOP:
            created_order = None
        elif order_type == TraderOrderType.TRAILING_STOP_LIMIT:
            created_order = None
        return created_order

    @staticmethod
    def _ensure_order_details_completeness(order, order_required_fields=None):
        if order_required_fields is None:
            order_required_fields = [ecoc.ID.value, ecoc.TIMESTAMP.value, ecoc.SYMBOL.value, ecoc.TYPE.value,
                                     ecoc.SIDE.value, ecoc.PRICE.value, ecoc.AMOUNT.value, ecoc.REMAINING.value]
        return all(key in order for key in order_required_fields)
