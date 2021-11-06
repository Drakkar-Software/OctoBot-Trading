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
    def __init__(self, trader, symbol_contract):
        super().__init__()
        self.trader = trader
        self.exchange_manager = trader.exchange_manager
        self.simulated = trader.simulate

        self.logger_name = None
        self.position_id = None
        self.timestamp = 0
        self.symbol = None
        self.currency, self.market = None, None
        self.status = enums.PositionStatus.OPEN
        self.side = enums.PositionSide.UNKNOWN

        # Contract
        self.symbol_contract = symbol_contract
        self.leverage = symbol_contract.current_leverage if symbol_contract.current_leverage else constants.ONE
        self.margin_type = None

        # Prices
        self.entry_price = constants.ZERO
        self.mark_price = constants.ZERO
        self.liquidation_price = constants.ZERO
        self.fee_to_close = constants.ZERO

        # Size
        self.quantity = constants.ZERO
        self.size = constants.ZERO
        self.value = constants.ZERO
        self.initial_margin = constants.ZERO
        self.margin = constants.ZERO

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

    def get_logger_name(self):
        """
        :return: The position logger name
        """
        if self.logger_name is None:
            self.logger_name = f"{self.get_name()} | {self.position_id}"
        return self.logger_name

    async def initialize_impl(self, **kwargs):
        """
        Initialize position status update tasks
        """
        await positions_states.create_position_state(self, **kwargs)

    async def on_open(self, force_open=False, is_from_exchange_data=False):
        """
        Triggers a new position open state
        :param force_open: if the new state should be forced
        :param is_from_exchange_data: if it's call from exchange data
        """
        self.state = positions_states.OpenPositionState(self, is_from_exchange_data=is_from_exchange_data)
        await self.state.initialize(forced=force_open)

    async def on_liquidate(self, force_liquidate=False, is_from_exchange_data=False):
        """
        Triggers a new position liquidation state
        :param force_liquidate: if the new state should be forced
        :param is_from_exchange_data: if it's call from exchange data
        """
        self.state = positions_states.LiquidatePositionState(self, is_from_exchange_data=is_from_exchange_data)
        await self.state.initialize(forced=force_liquidate)

    def _should_change(self, original_value, new_value):
        if new_value and original_value != new_value:
            return True

    def _update(self, position_id, symbol, currency, market, timestamp,
                entry_price, mark_price, liquidation_price,
                quantity, size, value, margin,
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
            changed = True

        if self._should_change(self.size, size):
            self.size = size
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

        if self._should_change(self.leverage, leverage):
            self.leverage = leverage
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

        self._update_side()
        self._update_quantity_or_size_if_necessary()
        self._update_entry_price_if_necessary(mark_price)
        self.update_pnl()
        return changed

    def update(self, update_size=None, mark_price=None):
        """
        Updates position size and / or mark price
        :param update_size: the size update value
        :param mark_price: the mark price update value
        """
        if mark_price is not None:
            self._update_mark_price(mark_price)
        # TODO Check for liquidation before updating size ?
        if update_size is not None:
            self._update_size(update_size)
        if not self.is_idle():
            self._check_for_liquidation()

    def _update_mark_price(self, mark_price):
        """
        Updates position mark_price and triggers size related attributes update
        :param mark_price: the update mark_price
        """
        self.mark_price = mark_price
        self._update_entry_price_if_necessary(mark_price)
        if not self.is_idle():
            self.update_value()
            self.update_pnl()

    def _update_entry_price_if_necessary(self, mark_price):
        """
        Update the position entry price when entry price is 0 or when the position is new
        :param mark_price: the position mark_price
        """
        if self.entry_price == constants.ZERO:
            self.entry_price = mark_price

    def update_size_from_order(self, order):
        """
        Update position size from filled order portfolio
        :param order: the filled order instance
        :return: the updated quantity, True if the order increased position size
        """
        size_to_close = self.get_quantity_to_close()
        if order.close_position:
            self.close()
            return size_to_close, False
        order_quantity = order.filled_quantity if order.is_long() else -order.filled_quantity
        if order.reduce_only or not self.symbol_contract.is_one_way_position_mode():
            if self.is_long() and order.is_short():
                size_update = max(order_quantity, size_to_close)
            elif self.is_short() and order.is_long():
                size_update = min(order_quantity, size_to_close)
            elif not order.reduce_only:
                size_update = order_quantity
            else:
                # Can't reduce position
                size_update = constants.ZERO
        else:
            size_update = order_quantity
        is_increasing_position_size = self._is_update_increasing_size(size_update=size_update)
        self.update(update_size=size_update)
        return size_update, is_increasing_position_size

    def _is_update_increasing_size(self, size_update):
        """
        :param size_update: the size update
        :return: True if this update will increase position size
        """
        if self.is_idle():
            return True
        if self.is_long():
            return size_update > 0
        return size_update < 0

    def _update_size(self, update_size):
        """
        Updates position size and triggers size related attributes update
        :param update_size: the size quantity
        """
        self._check_and_update_size(update_size)
        self._update_quantity()
        self._update_side()
        self.update_initial_margin()
        self.update_fee_to_close()
        self.update_liquidation_price()
        self.update_value()
        self.update_pnl()

    def _check_and_update_size(self, size_update):
        """
        Updates the position size with a valid size according to the contract position mode if not close the position
        This check is not mandatory when using one way position mode because it can't produce invalid size with
        :param size_update: the size update
        """
        if not self.symbol_contract.is_one_way_position_mode() and \
                ((self.is_long() and self.size + size_update < constants.ZERO) or
                 (self.is_short() and self.size + size_update > constants.ZERO)):
            self.size = constants.ZERO
            self.close()
        else:
            self.size += size_update
            if self.size == constants.ZERO:
                self.close()

    def _update_quantity_or_size_if_necessary(self):
        """
        Set quantity from size if quantity is not set and size is set or update size
        """
        if self.quantity == constants.ZERO and self.size != constants.ZERO:
            self._update_quantity()
        elif self.size == constants.ZERO and self.quantity != constants.ZERO:
            self.size = self.quantity * self.leverage

    def _update_quantity(self):
        """
        Update position quantity from position quantity
        """
        self.quantity = self.size / self.leverage

    def update_value(self):
        raise NotImplementedError("update_value not implemented")

    def update_pnl(self):
        raise NotImplementedError("update_pnl not implemented")

    def update_initial_margin(self):
        raise NotImplementedError("update_initial_margin not implemented")

    def get_maintenance_margin_rate(self):
        """
        :return: Position symbol funding rate
        """
        return self.exchange_manager.exchange_symbols_data. \
            get_exchange_symbol_data(self.symbol).funding_manager.funding_rate

    def get_initial_margin_rate(self):
        """
        :return: Initial Margin Rate = 1 / Leverage
        """
        try:
            return constants.ONE / self.leverage
        except decimal.DivisionByZero:
            return constants.ZERO

    def calculate_maintenance_margin(self):
        raise NotImplementedError("calculate_maintenance_margin not implemented")

    def update_liquidation_price(self):
        """
        Updates position liquidation price
        Should call _update_fee_to_close() at the end of the implementation
        """
        if self.symbol_contract.is_isolated():
            self.update_isolated_liquidation_price()
        else:
            self.update_cross_liquidation_price()

    def update_cross_liquidation_price(self):
        raise NotImplementedError("update_cross_liquidation_price not implemented")

    def update_isolated_liquidation_price(self):
        raise NotImplementedError("update_isolated_liquidation_price not implemented")

    def get_bankruptcy_price(self, with_mark_price=False):
        """
        The bankruptcy price refers to the price at which the initial margin of all positions is lost.
        :param with_mark_price: if price should be mark price instead of entry price
        :return: the bankruptcy price
        """
        raise NotImplementedError("get_bankruptcy_price not implemented")

    def get_maker_fee(self):
        """
        :return: Position maker fee
        """
        try:
            symbol_fees = self.exchange_manager.exchange.get_fees(self.symbol)
            return decimal.Decimal(
                f"{symbol_fees[enums.ExchangeConstantsMarketPropertyColumns.MAKER.value]}") / constants.ONE_HUNDRED
        except decimal.DivisionByZero:
            return constants.ZERO

    def get_taker_fee(self):
        """
        :return: Position taker fee
        """
        try:
            symbol_fees = self.exchange_manager.exchange.get_fees(self.symbol)
            return decimal.Decimal(
                f"{symbol_fees[enums.ExchangeConstantsMarketPropertyColumns.TAKER.value]}") / constants.ONE_HUNDRED
        except decimal.DivisionByZero:
            return constants.ZERO

    def get_two_way_taker_fee(self):
        """
        :return: 2-way taker fee = fee to open + fee to close
        """
        return self.get_fee_to_open() + self.fee_to_close

    def get_order_cost(self):
        raise NotImplementedError("get_order_cost not implemented")

    def get_fee_to_open(self):
        raise NotImplementedError("get_fee_to_open not implemented")

    def update_fee_to_close(self):
        raise NotImplementedError("update_fee_to_close not implemented")

    def _update_margin(self):
        """
        Updates position margin = Initial margin + Fee to close
        """
        self.margin = self.initial_margin + self.fee_to_close

    def is_open(self):
        return self.state is None or self.state.is_open()

    def is_liquidated(self):
        return self.state is not None and self.state.is_liquidated()

    def is_refreshing(self):
        return self.state is not None and self.state.is_refreshing()

    def is_long(self):
        return self.side is enums.PositionSide.LONG

    def is_short(self):
        return self.side is enums.PositionSide.SHORT

    def is_idle(self):
        return self.quantity == constants.ZERO

    def get_quantity_to_close(self):
        """
        :return: the order quantity to close the position
        """
        return -self.size

    def get_unrealised_pnl_percent(self):
        """
        :return: Unrealized P&L% = [ Position's unrealized P&L / Position Margin ] x 100%
        """
        return (self.unrealised_pnl / self.margin) * 100

    async def recreate(self):
        """
        Recreate itself using its PositionManager instance
        """
        self.exchange_manager.exchange_personal_data.positions_manager.recreate_position(self)

    def update_from_raw(self, raw_position):
        symbol = str(raw_position.get(enums.ExchangeConstantsPositionColumns.SYMBOL.value, None))
        currency, market = self.exchange_manager.get_exchange_quote_and_base(symbol)
        return self._update(
            symbol=symbol,
            currency=currency,
            market=market,
            entry_price=raw_position.get(enums.ExchangeConstantsPositionColumns.ENTRY_PRICE.value, constants.ZERO),
            mark_price=raw_position.get(enums.ExchangeConstantsPositionColumns.MARK_PRICE.value, constants.ZERO),
            liquidation_price=raw_position.get(enums.ExchangeConstantsPositionColumns.LIQUIDATION_PRICE.value, constants.ZERO),
            quantity=raw_position.get(enums.ExchangeConstantsPositionColumns.QUANTITY.value, constants.ZERO),
            size=raw_position.get(enums.ExchangeConstantsPositionColumns.SIZE.value, constants.ZERO),
            value=raw_position.get(enums.ExchangeConstantsPositionColumns.NOTIONAL.value, constants.ZERO),
            margin=raw_position.get(enums.ExchangeConstantsPositionColumns.COLLATERAL.value, constants.ZERO),
            position_id=str(raw_position.get(enums.ExchangeConstantsPositionColumns.ID.value, symbol)),
            timestamp=raw_position.get(enums.ExchangeConstantsPositionColumns.TIMESTAMP.value, 0),
            unrealised_pnl=raw_position.get(enums.ExchangeConstantsPositionColumns.UNREALISED_PNL.value, constants.ZERO),
            realised_pnl=raw_position.get(enums.ExchangeConstantsPositionColumns.REALISED_PNL.value, constants.ZERO),
            leverage=raw_position.get(enums.ExchangeConstantsPositionColumns.LEVERAGE.value, None),
            margin_type=raw_position.get(enums.ExchangeConstantsPositionColumns.MARGIN_TYPE.value,
                                         enums.TraderPositionType.ISOLATED),
            status=position_util.parse_position_status(raw_position),
            side=raw_position.get(enums.ExchangeConstantsPositionColumns.SIDE.value, None)
        )

    def to_dict(self):
        return {
            enums.ExchangeConstantsPositionColumns.ID.value: self.position_id,
            enums.ExchangeConstantsPositionColumns.SYMBOL.value: self.symbol,
            enums.ExchangeConstantsPositionColumns.STATUS.value: self.status.value,
            enums.ExchangeConstantsPositionColumns.TIMESTAMP.value: self.timestamp,
            enums.ExchangeConstantsPositionColumns.SIDE.value: self.side.value,
            enums.ExchangeConstantsPositionColumns.QUANTITY.value: self.quantity,
            enums.ExchangeConstantsPositionColumns.SIZE.value: self.size,
            enums.ExchangeConstantsPositionColumns.NOTIONAL.value: self.value,
            enums.ExchangeConstantsPositionColumns.INITIAL_MARGIN.value: self.initial_margin,
            enums.ExchangeConstantsPositionColumns.COLLATERAL.value: self.margin,
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
            if self.mark_price >= self.liquidation_price > constants.ZERO:
                self.status = enums.PositionStatus.LIQUIDATING
                asyncio.create_task(positions_states.create_position_state(self))
        if self.is_long():
            if self.mark_price <= self.liquidation_price > constants.ZERO:
                self.status = enums.PositionStatus.LIQUIDATING
                asyncio.create_task(positions_states.create_position_state(self))

    def _update_side(self):
        """
        Checks if self.side still represents the position side
        Only relevant when account is using one way position mode
        """
        if self.symbol_contract.is_one_way_position_mode() or self.side is enums.PositionSide.UNKNOWN:
            if self.quantity >= constants.ZERO:
                self.side = enums.PositionSide.LONG
            elif self.quantity < constants.ZERO:
                self.side = enums.PositionSide.SHORT
            else:
                self.side = enums.PositionSide.UNKNOWN

    def __str__(self):
        return self.to_string()

    def to_string(self):
        return (f"{self.symbol} | "
                f"MarkPrice : {str(self.mark_price)} | "
                f"Quantity : {str(self.quantity)} | "
                f"State : {self.state.state.value if self.state is not None else 'Unknown'} | "
                f"id : {self.position_id}")

    def close(self):
        self.reset()

    def reset(self):
        """
        Reset position attributes
        """
        self.entry_price = constants.ZERO
        self.mark_price = constants.ZERO
        self.quantity = constants.ZERO
        self.size = constants.ZERO
        self.value = constants.ZERO
        self.initial_margin = constants.ZERO
        self.margin = constants.ZERO
        self.liquidation_price = constants.ZERO
        self.fee_to_close = constants.ZERO
        self.status = enums.PositionStatus.OPEN
        self.side = enums.PositionSide.UNKNOWN
        self.unrealised_pnl = constants.ZERO
        self.realised_pnl = constants.ZERO
        self.creation_time = constants.ZERO
        asyncio.create_task(self.on_open())

    def clear(self):
        """
        Clear position references
        """
        self.state.clear()
        self.trader = None
        self.exchange_manager = None
