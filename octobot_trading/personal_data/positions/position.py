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
import asyncio
import decimal

import octobot_trading.enums as enums
import octobot_trading.personal_data.positions.position_util as position_util
import octobot_trading.personal_data.positions.states as positions_states
import octobot_trading.util as util
import octobot_trading.constants as constants


class Position(util.Initializable):
    def __init__(self, trader):
        super().__init__()
        self.trader = trader
        self.exchange_manager = trader.exchange_manager
        self.simulated = trader.simulate

        self.position_id = None
        self.timestamp = 0
        self.symbol = None
        self.currency, self.market = None, None
        self.entry_price = constants.ZERO
        self.mark_price = constants.ZERO
        self.quantity = constants.ZERO
        self.value = constants.ZERO
        self.margin = constants.ZERO
        self.liquidation_price = constants.ZERO
        self.leverage = 0
        self.margin_type = None
        self.status = enums.PositionStatus.OPEN
        self.side = enums.PositionSide.UNKNOWN

        # PNL
        self.unrealised_pnl = constants.ZERO
        self.realised_pnl = constants.ZERO

        # original position attributes
        self.creation_time = self.exchange_manager.exchange.get_exchange_current_time()

        # position state is initialized in initialize_impl()
        self.state = None

    @classmethod
    def get_name(cls):
        return cls.__name__

    async def initialize_impl(self, **kwargs):
        """
        Initialize position status update tasks
        """
        await positions_states.create_position_state(self, **kwargs)
        await self.update_position_status()

    async def update_position_status(self, force_refresh=False):
        """
        update_position_status will define the rules for a simulated position to be liquidated
        Should be called after updating position.mark_price
        """
        raise NotImplementedError("update_position_status not implemented")

    def is_open(self):
        return self.state is None or self.state.is_open()

    async def on_open(self, force_open=False, is_from_exchange_data=False):
        self.state = positions_states.OpenPositionState(self, is_from_exchange_data=is_from_exchange_data)
        await self.state.initialize(forced=force_open)

    async def on_liquidate(self, force_liquidate=False, is_from_exchange_data=False):
        self.state = positions_states.LiquidatePositionState(self, is_from_exchange_data=is_from_exchange_data)
        await self.state.initialize(forced=force_liquidate)

    def _should_change(self, original_value, new_value):
        if new_value and original_value != new_value:
            return True

    def _update(self, position_id, symbol, currency, market, timestamp,
                entry_price, mark_price, liquidation_price,
                quantity, value, margin,
                unrealised_pnl, realised_pnl,
                leverage, margin_type, status=None, side=None):
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
            self.quantity = quantity
            self._switch_side_if_necessary()
            changed = True

        if self._should_change(self.value, value):
            self.value = value
            changed = True

        if self._should_change(self.margin, margin):
            self.margin = margin
            changed = True

        if self._should_change(self.unrealised_pnl, unrealised_pnl):
            self.unrealised_pnl = unrealised_pnl
            changed = True

        if self._should_change(self.realised_pnl, realised_pnl):
            self.realised_pnl = realised_pnl
            changed = True

        if self._should_change(self.leverage, int(leverage)):
            self.leverage = int(leverage)
            changed = True

        if self._should_change(self.margin_type, margin_type):
            if self.margin_type is not None:
                # The margin type changed, we have to recreate the position
                self.margin_type = margin_type
                asyncio.create_task(self.recreate())

            self.margin_type = margin_type

        if self._should_change(self.entry_price, entry_price):
            self.entry_price = entry_price

        if self._should_change(self.mark_price, mark_price):
            self.mark_price = mark_price

        if self._should_change(self.liquidation_price, liquidation_price):
            self.liquidation_price = liquidation_price

        if self._should_change(self.status.value, status):
            self.status = enums.PositionStatus(status)

        if self._should_change(self.side.value, side):
            self.side = enums.PositionSide(side)

        if self.side is enums.PositionSide.UNKNOWN and self.quantity:
            self._switch_side_if_necessary()

        return changed

    def is_liquidated(self):
        return self.status is enums.PositionStatus.LIQUIDATING

    def is_long(self):
        return self.side is enums.PositionSide.LONG

    def is_short(self):
        return self.side is enums.PositionSide.SHORT

    async def recreate(self):
        self.exchange_manager.exchange_personal_data.positions_manager.recreate_position(self)

    async def update_from_filled_order(self, order):
        self.quantity = order.filled_quantity if order.is_long() else -order.filled_quantity

    def update_from_raw(self, raw_position):
        symbol = str(raw_position.get(enums.ExchangeConstantsPositionColumns.SYMBOL.value, None))
        currency, market = self.exchange_manager.get_exchange_quote_and_base(symbol)
        return self._update(**{
            "symbol": symbol,
            "currency": currency,
            "market": market,
            "entry_price": decimal.Decimal(str(raw_position.get(enums.ExchangeConstantsPositionColumns.ENTRY_PRICE.value, 0.0))),
            "mark_price": decimal.Decimal(str(raw_position.get(enums.ExchangeConstantsPositionColumns.MARK_PRICE.value, 0.0))),
            "liquidation_price": decimal.Decimal(str(raw_position.get(enums.ExchangeConstantsPositionColumns.LIQUIDATION_PRICE.value, 0.0))),
            "quantity": decimal.Decimal(str(raw_position.get(enums.ExchangeConstantsPositionColumns.QUANTITY.value, 0.0))),
            "value": decimal.Decimal(str(raw_position.get(enums.ExchangeConstantsPositionColumns.VALUE.value, 0.0))),
            "margin": decimal.Decimal(str(raw_position.get(enums.ExchangeConstantsPositionColumns.MARGIN.value, 0.0))),
            "position_id": str(raw_position.get(enums.ExchangeConstantsPositionColumns.ID.value, symbol)),
            "timestamp": raw_position.get(enums.ExchangeConstantsPositionColumns.TIMESTAMP.value, 0.0),
            "unrealised_pnl": decimal.Decimal(str(raw_position.get(enums.ExchangeConstantsPositionColumns.UNREALISED_PNL.value, 0.0))),
            "realised_pnl": decimal.Decimal(str(raw_position.get(enums.ExchangeConstantsPositionColumns.REALISED_PNL.value, 0.0))),
            "leverage": raw_position.get(enums.ExchangeConstantsPositionColumns.LEVERAGE.value, 0),
            "margin_type": raw_position.get(enums.ExchangeConstantsPositionColumns.MARGIN_TYPE.value,
                                            enums.TraderPositionType.ISOLATED),
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
            enums.ExchangeConstantsPositionColumns.MARGIN_TYPE.value: self.margin_type,
        }

    def _check_for_liquidation(self):
        """
        _check_for_liquidation will defines rules for a simulated position to be liquidated
        :return: True if the position is being liquidated else False
        """
        if self.is_short():
            if self.mark_price >= self.liquidation_price:
                self.status = enums.PositionStatus.LIQUIDATING
                return True
        if self.is_long():
            if self.mark_price <= self.liquidation_price:
                self.status = enums.PositionStatus.LIQUIDATING
                return True
        return False

    def _switch_side_if_necessary(self):
        """
        check if self.side still represents the position side
        """
        if self.quantity >= 0 and self.is_short():
            self.side = enums.PositionSide.LONG
        else:
            self.side = enums.PositionSide.SHORT

    def __str__(self):
        return self.to_string()

    def to_string(self):
        return (f"{self.symbol} | "
                f"MarkPrice : {str(self.mark_price)} | "
                f"Quantity : {str(self.quantity)} | "
                f"State : {self.state.state.value if self.state is not None else 'Unknown'} | "
                f"id : {self.position_id}")

    def clear(self):
        """
        Clear position references
        """
        self.state.clear()
        self.trader = None
        self.exchange_manager = None


def parse_position_type(raw_position):
    """
    Parse the raw position type to match a enums.TraderPositionType value
    :param raw_position: the raw position dict
    :return: the enums.TraderPositionType value
    """
    try:
        return enums.TraderPositionType(raw_position[enums.ExchangeConstantsPositionColumns.MARGIN_TYPE.value])
    except (KeyError, ValueError):
        return enums.TraderPositionType.ISOLATED
