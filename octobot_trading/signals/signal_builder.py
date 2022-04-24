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
import octobot_trading.signals.trading_signal as trading_signal
import octobot_trading.signals.util as signal_util
import octobot_trading.enums as trading_enums
import octobot_trading.errors as trading_errors
import octobot_trading.constants as trading_constants


class SignalBuilder:
    def __init__(self, strategy, exchange, exchange_type, symbol, description, state, orders):
        self.strategy = strategy
        self.exchange = exchange
        self.exchange_type = exchange_type
        self.symbol = symbol
        self.description = description
        self.state = state
        self.orders = orders
        self.reset()

    def add_created_order(self, order, target_amount=None, target_position=None):
        if target_amount is None and target_position is None:
            raise trading_errors.InvalidArgumentError("target_amount or target_position has to be provided")
        if not self._update_pending_orders(order, trading_enums.TradingSignalOrdersActions.CREATE,
                                           target_amount=target_amount,
                                           target_position=target_position):
            self.orders.append(signal_util.create_order_signal_description(
                order,
                trading_enums.TradingSignalOrdersActions.CREATE,
                target_amount=target_amount,
                target_position=target_position
            ))

    def add_order_to_group(self, order):
        if not self._update_pending_orders(order, trading_enums.TradingSignalOrdersActions.ADD_TO_GROUP):
            self.orders.append(signal_util.create_order_signal_description(
                order,
                trading_enums.TradingSignalOrdersActions.ADD_TO_GROUP
            ))

    def add_edited_order(
            self, order,
            updated_target_amount=None,
            updated_target_position=None,
            updated_limit_price=trading_constants.ZERO,
            updated_stop_price=trading_constants.ZERO,
            updated_current_price=trading_constants.ZERO
    ):
        if updated_target_amount is updated_target_position is None and \
           updated_limit_price is updated_stop_price is updated_current_price is trading_constants.ZERO:
            raise trading_errors.InvalidArgumentError("an updated argument has to be provided")
        if not self._update_pending_orders(
                order,
                trading_enums.TradingSignalOrdersActions.EDIT,
                updated_target_amount=updated_target_amount,
                updated_target_position=updated_target_position,
                updated_limit_price=updated_limit_price,
                updated_stop_price=updated_stop_price,
                updated_current_price=updated_current_price
        ):
            self.orders.append(signal_util.create_order_signal_description(
                order,
                trading_enums.TradingSignalOrdersActions.EDIT,
                updated_target_amount=updated_target_amount,
                updated_target_position=updated_target_position,
                updated_limit_price=updated_limit_price,
                updated_stop_price=updated_stop_price,
                updated_current_price=updated_current_price
            ))

    def add_cancelled_order(self, order):
        if not self._update_pending_orders(order, trading_enums.TradingSignalOrdersActions.CANCEL):
            self.orders.append(signal_util.create_order_signal_description(
                order,
                trading_enums.TradingSignalOrdersActions.CANCEL
            ))

    def _update_pending_orders(
        self, order,
        action,
        target_amount=None,
        target_position=None,
        updated_target_amount=None,
        updated_target_position=None,
        updated_limit_price=trading_constants.ZERO,
        updated_stop_price=trading_constants.ZERO,
        updated_current_price=trading_constants.ZERO
    ):
        try:
            index, order_description = self.get_order_description_from_local_orders(order)
            if action is trading_enums.TradingSignalOrdersActions.CREATE:
                # replace order
                self.orders[index] = signal_util.create_order_signal_description(
                    order,
                    trading_enums.TradingSignalOrdersActions.CREATE,
                    target_amount=target_amount,
                    target_position=target_position
                )
            if action is trading_enums.TradingSignalOrdersActions.ADD_TO_GROUP:
                # update order group
                order_description[trading_enums.TradingSignalOrdersAttrs.GROUP_ID.value] = order.order_group.name
                order_description[trading_enums.TradingSignalOrdersAttrs.GROUP_TYPE.value] = \
                    order.order_group.__class__.__name__
            elif action is trading_enums.TradingSignalOrdersActions.EDIT:
                # avoid editing order that are not yet created
                order_description[trading_enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value] = \
                    updated_target_amount
                order_description[trading_enums.TradingSignalOrdersAttrs.UPDATED_TARGET_AMOUNT.value] = \
                    updated_target_amount
                order_description[trading_enums.TradingSignalOrdersAttrs.TARGET_POSITION.value] = \
                    updated_target_position
                order_description[trading_enums.TradingSignalOrdersAttrs.UPDATED_TARGET_POSITION.value] = \
                    updated_target_position
                order_description[trading_enums.TradingSignalOrdersAttrs.LIMIT_PRICE.value] = \
                    float(updated_limit_price)
                order_description[trading_enums.TradingSignalOrdersAttrs.UPDATED_LIMIT_PRICE.value] = \
                    float(updated_limit_price)
                order_description[trading_enums.TradingSignalOrdersAttrs.STOP_PRICE.value] = \
                    float(updated_stop_price)
                order_description[trading_enums.TradingSignalOrdersAttrs.UPDATED_STOP_PRICE.value] = \
                    float(updated_stop_price)
                order_description[trading_enums.TradingSignalOrdersAttrs.CURRENT_PRICE.value] = \
                    float(updated_current_price)
                order_description[trading_enums.TradingSignalOrdersAttrs.UPDATED_CURRENT_PRICE.value] = \
                    float(updated_current_price)
            elif action is trading_enums.TradingSignalOrdersActions.CANCEL:
                if order_description[trading_enums.TradingSignalOrdersAttrs.ACTION.value] == \
                   trading_enums.TradingSignalOrdersActions.CREATE.value:
                    # avoid creating order that are to be cancelled
                    self.orders.pop(index)
                else:
                    # now cancel order (no need to perform previous actions as it will get cancelled anyway
                    order_description[trading_enums.TradingSignalOrdersAttrs.ACTION.value] = \
                        trading_enums.TradingSignalOrdersActions.CANCEL.value
            return True
        except trading_errors.OrderDescriptionNotFoundError:
            pass
        return False

    def get_order_description_from_local_orders(self, order):
        for index, order_description in enumerate(self.orders):
            if order_description[trading_enums.TradingSignalOrdersAttrs.SHARED_SIGNAL_ORDER_ID.value] == \
                    order.shared_signal_order_id:
                return index, order_description
        raise trading_errors.OrderDescriptionNotFoundError(f"order not found {order}")

    def build(self):
        return trading_signal.TradingSignal(
            self.strategy,
            self.exchange,
            self.exchange_type,
            self.symbol,
            self.description,
            self.state,
            self.orders
        )

    def reset(self):
        self.orders = []
