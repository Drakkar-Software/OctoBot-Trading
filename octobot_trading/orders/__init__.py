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
import octobot_trading
from octobot_trading.orders import order
from octobot_trading.orders import order_adapter
from octobot_trading.orders import order_factory
from octobot_trading.orders import order_state
from octobot_trading.orders import order_util
from octobot_trading.orders import orders_manager
from octobot_trading.orders import states
from octobot_trading.orders import types

from octobot_trading.orders.order import (Order, parse_order_type, )
from octobot_trading.orders.order_adapter import (adapt_order_quantity_because_price,
                                                  adapt_order_quantity_because_quantity,
                                                  adapt_price, adapt_quantity,
                                                  add_dusts_to_quantity_if_necessary,
                                                  check_and_adapt_order_details_if_necessary,
                                                  split_orders,
                                                  trunc_with_n_decimal_digits, )
from octobot_trading.orders.order_factory import (create_order_from_raw,
                                                  create_order_from_type,
                                                  create_order_instance,
                                                  create_order_instance_from_raw, )
from octobot_trading.orders.order_state import (OrderState, )
from octobot_trading.orders.order_util import (check_cost,
                                               get_fees_for_currency,
                                               get_min_max_amounts, is_valid,
                                               parse_is_cancelled,
                                               parse_order_status,
                                               get_pre_order_data,
                                               total_fees_from_order_dict, )
from octobot_trading.orders.orders_manager import (OrdersManager, )
from octobot_trading.orders.states import (CancelOrderState, CloseOrderState,
                                           FillOrderState, OpenOrderState,
                                           cancel_order_state,
                                           close_order_state, fill_order_state,
                                           open_order_state,
                                           order_state_factory,
                                           create_order_state,)
from octobot_trading.orders.types import (BuyLimitOrder, BuyMarketOrder,
                                          LimitOrder, MarketOrder,
                                          SellLimitOrder, SellMarketOrder,
                                          StopLossLimitOrder, StopLossOrder,
                                          TakeProfitLimitOrder,
                                          TakeProfitOrder,
                                          TrailingStopLimitOrder,
                                          TrailingStopOrder, UnknownOrder,
                                          buy_limit_order, buy_market_order,
                                          limit, limit_order, market,
                                          market_order, sell_limit_order,
                                          sell_market_order,
                                          stop_loss_limit_order,
                                          stop_loss_order,
                                          take_profit_limit_order,
                                          take_profit_order, trailing,
                                          trailing_stop_limit_order,
                                          trailing_stop_order, unknown_order, )

__all__ = ['BuyLimitOrder', 'BuyMarketOrder', 'CancelOrderState',
           'CloseOrderState', 'FillOrderState', 'LimitOrder', 'MarketOrder',
           'OpenOrderState', 'Order', 'OrderState', 'OrdersManager',
           'SellLimitOrder', 'SellMarketOrder', 'StopLossLimitOrder',
           'StopLossOrder', 'TakeProfitLimitOrder', 'TakeProfitOrder',
           'TrailingStopLimitOrder', 'TrailingStopOrder', 'UnknownOrder',
           'adapt_order_quantity_because_price',
           'adapt_order_quantity_because_quantity', 'adapt_price',
           'adapt_quantity', 'add_dusts_to_quantity_if_necessary',
           'buy_limit_order', 'buy_market_order', 'cancel_order_state',
           'check_and_adapt_order_details_if_necessary', 'check_cost',
           'close_order_state', 'create_order_from_raw',
           'create_order_from_type', 'create_order_instance',
           'create_order_instance_from_raw', 'fill_order_state',
           'get_fees_for_currency', 'get_min_max_amounts', 'is_valid', 'limit',
           'limit_order', 'market', 'market_order',
           'open_order_state', 'order', 'order_adapter', 'create_order_state',
           'order_factory', 'order_state', 'order_state_factory', 'order_util',
           'orders_manager', 'parse_is_cancelled', 'parse_order_status',
           'parse_order_type', 'sell_limit_order', 'sell_market_order',
           'split_orders', 'states', 'stop_loss_limit_order',
           'stop_loss_order', 'take_profit_limit_order',
           'take_profit_order', 'get_pre_order_data', 'total_fees_from_order_dict', 'trailing',
           'trailing_stop_limit_order', 'trailing_stop_order',
           'trunc_with_n_decimal_digits', 'types', 'unknown_order']

TraderOrderTypeClasses = {
    octobot_trading.TraderOrderType.BUY_MARKET: BuyMarketOrder,
    octobot_trading.TraderOrderType.BUY_LIMIT: BuyLimitOrder,
    octobot_trading.TraderOrderType.TAKE_PROFIT: TakeProfitOrder,
    octobot_trading.TraderOrderType.TAKE_PROFIT_LIMIT: TakeProfitLimitOrder,
    octobot_trading.TraderOrderType.TRAILING_STOP: TrailingStopOrder,
    octobot_trading.TraderOrderType.TRAILING_STOP_LIMIT: TrailingStopLimitOrder,
    octobot_trading.TraderOrderType.STOP_LOSS: StopLossOrder,
    octobot_trading.TraderOrderType.STOP_LOSS_LIMIT: StopLossLimitOrder,
    octobot_trading.TraderOrderType.SELL_MARKET: SellMarketOrder,
    octobot_trading.TraderOrderType.SELL_LIMIT: SellLimitOrder,
    octobot_trading.TraderOrderType.UNKNOWN: UnknownOrder,
}
