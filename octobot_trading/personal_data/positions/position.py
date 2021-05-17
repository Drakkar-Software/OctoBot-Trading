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
import octobot_trading.enums as enums
import octobot_trading.personal_data.positions.position_util as position_util


class Position:
    def __init__(self, trader):
        self.trader = trader
        self.exchange_manager = trader.exchange_manager

        self.position_id = None
        self.timestamp = 0
        self.symbol = None
        self.currency, self.market = None, None
        self.creation_time = 0
        self.entry_price = 0
        self.mark_price = 0
        self.quantity = 0
        self.value = 0
        self.margin = 0
        self.liquidation_price = 0
        self.unrealised_pnl = 0
        self.realised_pnl = 0
        self.leverage = 0
        self.status = enums.PositionStatus.OPEN
        self.side = enums.PositionSide.UNKNOWN

    def _should_change(self, original_value, new_value):
        if new_value and original_value != new_value:
            return True

    def _update(self, position_id, symbol, currency, market, timestamp,
                entry_price, mark_price, liquidation_price,
                quantity, value, margin,
                unrealised_pnl, realised_pnl,
                leverage, status=None, side=None):
        changed: bool = False

        if self._should_change(self.position_id, position_id):
            self.position_id = position_id

        if self._should_change(self.symbol, symbol):
            self.symbol, self.currency, self.market = symbol, currency, market

        if self._should_change(self.timestamp, timestamp):
            self.timestamp = timestamp
        if not self.timestamp:
            if not timestamp:
                self.creation_time = self.exchange_manager.exchange.get_exchange_current_time()
            else:
                # if we have a timestamp, it's a real trader => need to format timestamp if necessary
                self.creation_time = self.exchange_manager.exchange.get_uniform_timestamp(timestamp)
            self.timestamp = self.creation_time

        if self._should_change(self.quantity, quantity):
            self.quantity = float(quantity)
            changed = True

        if self._should_change(self.value, value):
            self.value = float(value)
            changed = True

        if self._should_change(self.margin, margin):
            self.margin = float(margin)
            changed = True

        if self._should_change(self.unrealised_pnl, unrealised_pnl):
            self.unrealised_pnl = float(unrealised_pnl)
            changed = True

        if self._should_change(self.realised_pnl, realised_pnl):
            self.realised_pnl = float(realised_pnl)
            changed = True

        if self._should_change(self.leverage, leverage):
            self.leverage = int(leverage)
            changed = True

        if self._should_change(self.entry_price, entry_price):
            self.entry_price = float(entry_price)

        if self._should_change(self.mark_price, mark_price):
            self.mark_price = float(mark_price)

        if self._should_change(self.liquidation_price, liquidation_price):
            self.liquidation_price = float(liquidation_price)

        if self._should_change(self.status.value, status):
            self.status = enums.PositionStatus(status)

        if self._should_change(self.side.value, side):
            self.side = enums.PositionSide(side)

        if self.side is enums.PositionSide.UNKNOWN and self.quantity:
            self.side = enums.PositionSide.LONG if self.quantity > 0 else enums.PositionSide.SHORT

        return changed

    def is_liquidated(self):
        return self.status is enums.PositionStatus.LIQUIDATING

    def is_long(self):
        return self.side is enums.PositionSide.LONG

    def is_short(self):
        return self.side is enums.PositionSide.SHORT

    def update_from_raw(self, raw_position):
        symbol = str(raw_position.get(enums.ExchangeConstantsPositionColumns.SYMBOL.value, None))
        currency, market = self.exchange_manager.get_exchange_quote_and_base(symbol)
        return self._update(**{
            "symbol": symbol,
            "currency": currency,
            "market": market,
            "entry_price": raw_position.get(enums.ExchangeConstantsPositionColumns.ENTRY_PRICE.value, 0.0),
            "mark_price": raw_position.get(enums.ExchangeConstantsPositionColumns.MARK_PRICE.value, 0.0),
            "liquidation_price": raw_position.get(enums.ExchangeConstantsPositionColumns.LIQUIDATION_PRICE.value, 0.0),
            "quantity": raw_position.get(enums.ExchangeConstantsPositionColumns.QUANTITY.value, 0.0),
            "value": raw_position.get(enums.ExchangeConstantsPositionColumns.VALUE.value, 0.0),
            "margin": raw_position.get(enums.ExchangeConstantsPositionColumns.MARGIN.value, 0.0),
            "position_id": str(raw_position.get(enums.ExchangeConstantsPositionColumns.ID.value, None)),
            "timestamp": raw_position.get(enums.ExchangeConstantsPositionColumns.TIMESTAMP.value, 0.0),
            "unrealised_pnl": raw_position.get(enums.ExchangeConstantsPositionColumns.UNREALISED_PNL.value, 0.0),
            "realised_pnl": raw_position.get(enums.ExchangeConstantsPositionColumns.REALISED_PNL.value, 0.0),
            "leverage": raw_position.get(enums.ExchangeConstantsPositionColumns.LEVERAGE.value, 0),
            "status": position_util.parse_position_status(raw_position),
            "side": raw_position.get(enums.ExchangeConstantsPositionColumns.SIDE.value, None)
        })

    def to_dict(self):
        return {
            enums.ExchangeConstantsPositionColumns.ID.value: self.position_id,
            enums.ExchangeConstantsPositionColumns.SYMBOL.value: self.symbol,
            enums.ExchangeConstantsPositionColumns.STATUS.value: self.status.value,
            enums.ExchangeConstantsPositionColumns.TIMESTAMP.value: self.timestamp,
            enums.ExchangeConstantsPositionColumns.SIDE.value: self.side.value,
            enums.ExchangeConstantsPositionColumns.QUANTITY.value: self.quantity,
            enums.ExchangeConstantsPositionColumns.VALUE.value: self.value,
            enums.ExchangeConstantsPositionColumns.MARGIN.value: self.margin,
            enums.ExchangeConstantsPositionColumns.ENTRY_PRICE.value: self.entry_price,
            enums.ExchangeConstantsPositionColumns.MARK_PRICE.value: self.mark_price,
            enums.ExchangeConstantsPositionColumns.LIQUIDATION_PRICE.value: self.liquidation_price,
            enums.ExchangeConstantsPositionColumns.UNREALISED_PNL.value: self.unrealised_pnl,
            enums.ExchangeConstantsPositionColumns.REALISED_PNL.value: self.realised_pnl,
            enums.ExchangeConstantsPositionColumns.LEVERAGE.value: self.leverage,
        }

    def _check_for_liquidation(self):
        """
        _check_for_liquidation will defines rules for a simulated position to be liquidated
        """
        if self.is_short():
            if self.mark_price >= self.liquidation_price:
                self.status = enums.PositionStatus.LIQUIDATING
        elif self.is_long():
            if self.mark_price <= self.liquidation_price:
                self.status = enums.PositionStatus.LIQUIDATING

    async def close(self):
        await self.trader.notify_position_close(self)

    async def liquidate(self):
        await self.trader.notify_position_liquidate(self)

    async def update_status(self, mark_price):
        self.mark_price = mark_price

        # liquidation check
        self._check_for_liquidation()
        if self.is_liquidated():
            await self.liquidate()

        # update P&L
        # TODO

