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
import octobot_trading.enums as trading_enums
import octobot_trading.exchanges as exchanges
import octobot_trading.constants as trading_constants


def create_order_signal_content(
        order, action, strategy, exchange_manager,
        target_amount=None,
        target_position=None,
        updated_target_amount=None,
        updated_target_position=None,
        updated_limit_price=trading_constants.ZERO,
        updated_stop_price=trading_constants.ZERO,
        updated_current_price=trading_constants.ZERO,
) -> dict:
    # only use order.order_id to identify orders in signals (exchange_order_id is local and never shared)
    return {
        trading_enums.TradingSignalCommonsAttrs.ACTION.value: action.value,
        trading_enums.TradingSignalOrdersAttrs.STRATEGY.value: strategy,
        trading_enums.TradingSignalOrdersAttrs.SYMBOL.value: order.symbol,
        trading_enums.TradingSignalOrdersAttrs.EXCHANGE.value: exchange_manager.exchange_name,
        trading_enums.TradingSignalOrdersAttrs.EXCHANGE_TYPE.value: exchanges.get_exchange_type(exchange_manager).value,
        trading_enums.TradingSignalOrdersAttrs.SIDE.value: order.side.value,
        trading_enums.TradingSignalOrdersAttrs.TYPE.value: order.order_type.value,
        trading_enums.TradingSignalOrdersAttrs.QUANTITY.value: float(order.origin_quantity),
        trading_enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value: target_amount
        if updated_target_amount is None else updated_target_amount,
        trading_enums.TradingSignalOrdersAttrs.TARGET_POSITION.value: target_position
        if updated_target_position is None else updated_target_position,
        trading_enums.TradingSignalOrdersAttrs.UPDATED_TARGET_AMOUNT.value: updated_target_amount,
        trading_enums.TradingSignalOrdersAttrs.UPDATED_TARGET_POSITION.value: updated_target_position,
        trading_enums.TradingSignalOrdersAttrs.LIMIT_PRICE.value: float(updated_limit_price)
        if updated_limit_price else float(order.origin_price),
        trading_enums.TradingSignalOrdersAttrs.UPDATED_LIMIT_PRICE.value: float(updated_limit_price),
        trading_enums.TradingSignalOrdersAttrs.STOP_PRICE.value: float(updated_stop_price)
        if updated_stop_price else float(order.origin_stop_price),
        trading_enums.TradingSignalOrdersAttrs.UPDATED_STOP_PRICE.value: float(updated_stop_price),
        trading_enums.TradingSignalOrdersAttrs.CURRENT_PRICE.value: float(updated_current_price)
        if updated_current_price else float(order.created_last_price),
        trading_enums.TradingSignalOrdersAttrs.UPDATED_CURRENT_PRICE.value: float(updated_current_price),
        trading_enums.TradingSignalOrdersAttrs.REDUCE_ONLY.value: order.reduce_only,
        trading_enums.TradingSignalOrdersAttrs.POST_ONLY.value: False,
        trading_enums.TradingSignalOrdersAttrs.GROUP_ID.value:
            None if order.order_group is None else order.order_group.name,
        trading_enums.TradingSignalOrdersAttrs.GROUP_TYPE.value:
            None if order.order_group is None else order.order_group.__class__.__name__,
        trading_enums.TradingSignalOrdersAttrs.TAG.value: order.tag,
        trading_enums.TradingSignalOrdersAttrs.ASSOCIATED_ORDER_IDS.value: order.associated_entry_ids,
        trading_enums.TradingSignalOrdersAttrs.UPDATE_WITH_TRIGGERING_ORDER_FEES.value:
            order.update_with_triggering_order_fees,
        trading_enums.TradingSignalOrdersAttrs.ORDER_ID.value: order.order_id,
        trading_enums.TradingSignalOrdersAttrs.BUNDLED_WITH.value:
            None if order.triggered_by is None else order.triggered_by.order_id
        if order.has_been_bundled else None,
        trading_enums.TradingSignalOrdersAttrs.CHAINED_TO.value:
            None if order.triggered_by is None else order.triggered_by.order_id,
        trading_enums.TradingSignalOrdersAttrs.ADDITIONAL_ORDERS.value: [],
    }
