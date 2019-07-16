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
import copy

from ccxt.base.errors import InsufficientFunds

from octobot_trading.channels import RECENT_TRADES_CHANNEL, ORDERS_CHANNEL
from octobot_trading.channels.exchange_channel import ExchangeChannels

from octobot_trading.data.order import Order
from octobot_trading.enums import OrderStatus
from octobot_trading.producers import MissingOrderException
from octobot_trading.producers.orders_updater import OpenOrdersUpdater, CloseOrdersUpdater


class OpenOrdersUpdaterSimulator(OpenOrdersUpdater):
    SIMULATOR_LAST_PRICES_TO_CHECK = 50

    def __init__(self, channel):
        super().__init__(channel)
        self.exchange_personal_data = self.channel.exchange_manager.exchange_personal_data

        ExchangeChannels.get_chan(RECENT_TRADES_CHANNEL, self.channel.exchange.name).new_consumer(
            self.handle_recent_trade,
            filter_size=True)

    """
    Recent trade channel consumer callback
    """

    async def handle_recent_trade(self, exchange: str, symbol: str, recent_trades: list):
        failed_order_updates = await self._update_orders_status(symbol=symbol, last_prices=recent_trades)

        if failed_order_updates:
            self.logger.info(f"Forcing real trader refresh.")
            self.channel.exchange_manager.trader.force_refresh_orders_and_portfolio()

    """
    Ask orders to check their status
    Ask cancellation and filling process if it is required
    """

    async def _update_orders_status(self,
                                    symbol: str,
                                    last_prices: list,
                                    simulated_time: bool = False) -> list:
        failed_order_updates = []
        for order in copy.copy(self.exchange_personal_data.orders.get_open_orders(symbol=symbol)):
            order_filled = False
            try:
                # ask orders to update their status
                async with order.lock:
                    order_filled = await self._update_order_status(order,
                                                                   failed_order_updates,
                                                                   last_prices,
                                                                   simulated_time=simulated_time)
            except Exception as e:
                raise e
            finally:
                # ensure always call fill callback
                if order_filled:
                    await ExchangeChannels.get_chan(ORDERS_CHANNEL, self.channel.exchange.name).get_global_producer() \
                        .send_with_wildcard(symbol=order.symbol,
                                            order=order,
                                            is_from_bot=True,
                                            is_closed=True,
                                            is_updated=False)
        return failed_order_updates

    """
    Call order status update
    """

    async def _update_order_status(self,
                                   order: Order,
                                   failed_order_updates: list,
                                   last_prices: list,
                                   simulated_time: bool = False):
        order_filled = False
        try:
            await order.update_order_status(last_prices, simulated_time=simulated_time)

            if order.status == OrderStatus.FILLED:
                order_filled = True
                self.logger.info(f"{order.symbol} {order.get_name()} (ID : {order.order_id})"
                                 f" filled on {self.channel.exchange.name} "
                                 f"at {order.filled_price}")
                await order.close_order()
        except MissingOrderException as e:
            self.logger.error(f"Missing exchange order when updating order with id: {e.order_id}. "
                              f"Will force a real trader refresh. ({e})")
            failed_order_updates.append(e.order_id)
        except InsufficientFunds as e:
            self.logger.error(f"Not enough funds to create order: {e} (updating {order}).")
        finally:
            return order_filled


class CloseOrdersUpdaterSimulator(CloseOrdersUpdater):
    pass
