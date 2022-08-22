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
import octobot_commons.signals as signals
import octobot_trading.signals.util as signal_util
import octobot_trading.enums as trading_enums
import octobot_trading.errors as trading_errors
import octobot_trading.constants as trading_constants


class TradingSignalBundleBuilder(signals.SignalBundleBuilder):
    def __init__(self, identifier: str, strategy: str):
        super().__init__(identifier)
        self.strategy = strategy

    def build(self) -> signals.SignalBundle:
        """
        Link bundled an grouped orders and create a signal_bundle.SignalBundle from registered signals
        """
        self._pack_referenced_orders_together()
        return super().build()

    def add_created_order(self, order, exchange_manager, target_amount=None, target_position=None):
        if target_amount is None and target_position is None:
            raise trading_errors.InvalidArgumentError("target_amount or target_position has to be provided")
        if not self._update_pending_orders(order, exchange_manager,
                                           trading_enums.TradingSignalOrdersActions.CREATE,
                                           target_amount=target_amount,
                                           target_position=target_position):
            self.register_signal(
                trading_enums.TradingSignalTopics.ORDERS.value,
                signal_util.create_order_signal_content(
                    order,
                    trading_enums.TradingSignalOrdersActions.CREATE,
                    self.strategy,
                    exchange_manager,
                    target_amount=target_amount,
                    target_position=target_position
                )
            )

    def add_order_to_group(self, order, exchange_manager):
        if not self._update_pending_orders(order, exchange_manager,
                                           trading_enums.TradingSignalOrdersActions.ADD_TO_GROUP):
            self.register_signal(
                trading_enums.TradingSignalTopics.ORDERS.value,
                signal_util.create_order_signal_content(
                    order,
                    trading_enums.TradingSignalOrdersActions.ADD_TO_GROUP,
                    self.strategy,
                    exchange_manager,
                )
            )

    def add_edited_order(
            self, order, exchange_manager,
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
                exchange_manager,
                trading_enums.TradingSignalOrdersActions.EDIT,
                updated_target_amount=updated_target_amount,
                updated_target_position=updated_target_position,
                updated_limit_price=updated_limit_price,
                updated_stop_price=updated_stop_price,
                updated_current_price=updated_current_price
        ):
            self.register_signal(
                trading_enums.TradingSignalTopics.ORDERS.value,
                signal_util.create_order_signal_content(
                    order,
                    trading_enums.TradingSignalOrdersActions.EDIT,
                    self.strategy,
                    exchange_manager,
                    updated_target_amount=updated_target_amount,
                    updated_target_position=updated_target_position,
                    updated_limit_price=updated_limit_price,
                    updated_stop_price=updated_stop_price,
                    updated_current_price=updated_current_price
                )
            )

    def add_cancelled_order(self, order, exchange_manager):
        if not self._update_pending_orders(order, exchange_manager, trading_enums.TradingSignalOrdersActions.CANCEL):
            self.register_signal(
                trading_enums.TradingSignalTopics.ORDERS.value,
                signal_util.create_order_signal_content(
                    order,
                    trading_enums.TradingSignalOrdersActions.CANCEL,
                    self.strategy,
                    exchange_manager,
                )
            )

    def _update_pending_orders(
        self, order, exchange_manager,
        action,
        target_amount=None,
        target_position=None,
        updated_target_amount=None,
        updated_target_position=None,
        updated_limit_price=trading_constants.ZERO,
        updated_stop_price=trading_constants.ZERO,
        updated_current_price=trading_constants.ZERO,
    ):
        try:
            index, order_description = self._get_order_description_from_local_orders(order.shared_signal_order_id)
            if action is trading_enums.TradingSignalOrdersActions.CREATE:
                # replace order
                self.signals[index] = self.create_signal(
                    trading_enums.TradingSignalTopics.ORDERS.value,
                    signal_util.create_order_signal_content(
                        order,
                        trading_enums.TradingSignalOrdersActions.CREATE,
                        self.strategy,
                        exchange_manager,
                        target_amount=target_amount,
                        target_position=target_position
                    )
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
                if order_description[trading_enums.TradingSignalCommonsAttrs.ACTION.value] == \
                   trading_enums.TradingSignalOrdersActions.CREATE.value:
                    # avoid creating order that are to be cancelled
                    self.signals.pop(index)
                else:
                    # now cancel order (no need to perform previous actions as it will get cancelled anyway
                    order_description[trading_enums.TradingSignalCommonsAttrs.ACTION.value] = \
                        trading_enums.TradingSignalOrdersActions.CANCEL.value
            return True
        except trading_errors.OrderDescriptionNotFoundError:
            pass
        return False

    def _pack_referenced_orders_together(self):
        filtered_signals = []
        order_description_by_seen_group_ids = {}
        for signal in self.signals:
            include_signal = True
            # bundled orders must be sent at the same time as the original order, add them both to the same signal
            if add_to_order_id := signal.content[trading_enums.TradingSignalOrdersAttrs.BUNDLED_WITH.value]:
                _, order_description = self._get_order_description_from_local_orders(add_to_order_id)
                order_description[trading_enums.TradingSignalOrdersAttrs.ADDITIONAL_ORDERS.value].append(signal.content)
                include_signal = False
            # chained orders must be sent at the same time as the original order, add them both to the same signal
            elif add_to_order_id := signal.content[trading_enums.TradingSignalOrdersAttrs.CHAINED_TO.value]:
                _, order_description = self._get_order_description_from_local_orders(add_to_order_id)
                order_description[trading_enums.TradingSignalOrdersAttrs.ADDITIONAL_ORDERS.value].append(signal.content)
                include_signal = False
            # grouped orders must be created before the group is enabled, add them both to the same signal
            # groups might also need to be update together
            elif add_to_group_ids := signal.content[trading_enums.TradingSignalOrdersAttrs.GROUP_ID.value]:
                if add_to_group_ids in order_description_by_seen_group_ids:
                    order_description_by_seen_group_ids[add_to_group_ids][
                        trading_enums.TradingSignalOrdersAttrs.ADDITIONAL_ORDERS.value].append(signal.content)
                    include_signal = False
                else:
                    order_description_by_seen_group_ids[add_to_group_ids] = signal.content
            if include_signal:
                filtered_signals.append(signal)
        self.signals = filtered_signals

    def _get_order_description_from_local_orders(self, shared_signal_order_id):
        for index, signal in enumerate(self.signals):
            if signal.content[trading_enums.TradingSignalOrdersAttrs.SHARED_SIGNAL_ORDER_ID.value] == \
                    shared_signal_order_id:
                return index, signal.content
        raise trading_errors.OrderDescriptionNotFoundError(
            f"order not found (shared_signal_order_id: {shared_signal_order_id})"
        )
