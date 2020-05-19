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
from octobot_trading.api.exchange import get_exchange_ids
from octobot_trading.channels.exchange_channel import get_chan
from octobot_trading.channels.trades import TradesChannel
from octobot_trading.enums import TraderOrderType
from octobot_trading.data.order import parse_order_type as order_parse_order_type


def get_trade_history(exchange_manager, symbol=None, since=None, as_dict=False) -> list:
    return [trade.to_dict() if as_dict else trade
            for trade in exchange_manager.exchange_personal_data.trades_manager.trades.values()
            if _trade_filter(trade, symbol, since)]


def _trade_filter(trade, symbol=None, timestamp=None) -> bool:
    if symbol is None and timestamp is None:
        return True
    elif symbol is None and timestamp is not None:
        return _is_trade_after(trade, timestamp)
    elif symbol is not None and timestamp is None:
        return trade.symbol == symbol
    else:
        return trade.symbol == symbol and _is_trade_after(trade, timestamp)


def _is_trade_after(trade, timestamp) -> bool:
    return trade.executed_time > timestamp or trade.canceled_time > timestamp


def get_total_paid_trading_fees(exchange_manager) -> dict:
    return exchange_manager.exchange_personal_data.trades_manager.get_total_paid_fees()


def get_trade_exchange_name(trade) -> str:
    return trade.exchange_manager.get_exchange_name()


def parse_trade_type(dict_trade) -> TraderOrderType:
    # can use parse_order_type since format is compatible
    return order_parse_order_type(dict_trade)[1]


def trade_to_dict(trade) -> dict:
    return trade.to_dict()


async def subscribe_to_trades_channel(callback, exchange_id):
    trades_channel_name = TradesChannel.get_name()
    channel = get_chan(trades_channel_name, exchange_id)
    await channel.new_consumer(callback)
