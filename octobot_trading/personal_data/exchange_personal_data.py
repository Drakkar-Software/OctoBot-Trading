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

import octobot_commons.logging as logging

import octobot_trading.exchange_channel as exchange_channel
import octobot_trading.constants
import octobot_trading.personal_data.portfolios.portfolio_manager as portfolio_manager
import octobot_trading.personal_data.positions.positions_manager as positions_manager
import octobot_trading.personal_data.orders.orders_manager as orders_manager
import octobot_trading.personal_data.trades.trades_manager as trades_manager
import octobot_trading.util as util


class ExchangePersonalData(util.Initializable):
    # note: symbol keys are without /
    def __init__(self, exchange_manager):
        super().__init__()
        self.logger = logging.get_logger(self.__class__.__name__)
        self.exchange_manager = exchange_manager
        self.config = exchange_manager.config

        self.trader = None
        self.exchange = None
        self.portfolio_manager = None
        self.trades_manager = None
        self.orders_manager = None
        self.positions_manager = None

    async def initialize_impl(self):
        self.trader = self.exchange_manager.trader
        self.exchange = self.exchange_manager.exchange
        if self.trader.is_enabled:
            try:
                self.portfolio_manager = portfolio_manager.PortfolioManager(self.config, self.trader,
                                                                            self.exchange_manager)
                self.trades_manager = trades_manager.TradesManager(self.trader)
                self.orders_manager = orders_manager.OrdersManager(self.trader)
                self.positions_manager = positions_manager.PositionsManager(self.trader)
                await self.portfolio_manager.initialize()
                await self.trades_manager.initialize()
                await self.orders_manager.initialize()
                await self.positions_manager.initialize()
            except Exception as e:
                self.logger.exception(e, True, f"Error when initializing : {e}. "
                                               f"{self.exchange.name} personal data disabled.")

    # updates
    async def handle_portfolio_update(self, balance, should_notify: bool = True, is_diff_update=False) -> bool:
        try:
            changed: bool = self.portfolio_manager.handle_balance_update(balance, is_diff_update=is_diff_update)
            if should_notify:
                await exchange_channel.get_chan(octobot_trading.constants.BALANCE_CHANNEL,
                                         self.exchange_manager.id).get_internal_producer().send(balance)
            return changed
        except AttributeError as e:
            self.logger.exception(e, True, f"Failed to update balance : {e}")
            return False

    async def handle_portfolio_update_from_order(self, order,
                                                 require_exchange_update: bool = True,
                                                 should_notify: bool = True) -> bool:
        try:
            changed: bool = await self.portfolio_manager.handle_balance_update_from_order(order,
                                                                                          require_exchange_update)
            if should_notify:
                await exchange_channel.get_chan(octobot_trading.constants.BALANCE_CHANNEL, self.exchange_manager.id). \
                    get_internal_producer().send(self.portfolio_manager.portfolio.portfolio)
            return changed
        except AttributeError as e:
            self.logger.exception(e, True, f"Failed to update balance : {e}")
            return False

    async def handle_portfolio_profitability_update(self, balance, mark_price, symbol, should_notify: bool = True):
        try:
            portfolio_profitability = self.portfolio_manager.portfolio_profitability

            if balance is not None:
                await self.portfolio_manager.handle_balance_updated()

            if mark_price is not None and symbol is not None:
                await self.portfolio_manager.handle_mark_price_update(symbol=symbol, mark_price=mark_price)

            if should_notify:
                await exchange_channel.get_chan(octobot_trading.constants.BALANCE_PROFITABILITY_CHANNEL,
                                                self.exchange_manager.id).get_internal_producer() \
                    .send(profitability=portfolio_profitability.profitability,
                          profitability_percent=portfolio_profitability.profitability_percent,
                          market_profitability_percent=portfolio_profitability.market_profitability_percent,
                          initial_portfolio_current_profitability=portfolio_profitability.initial_portfolio_current_profitability)
        except Exception as e:
            self.logger.exception(e, True, f"Failed to update portfolio profitability : {e}")

    async def handle_order_update_from_raw(self, order_id, raw_order,
                                           is_new_order: bool = False,
                                           should_notify: bool = True) -> bool:
        # Orders can sometimes be out of sync between different exchange endpoints (ex: binance order API vs
        # open_orders API which is slower).
        # Always check if this order has not already been closed previously (most likely during the last
        # seconds/minutes)
        if self._is_out_of_sync_order(order_id):
            self.logger.debug(f"Ignored update for order with {order_id}: this order has already been closed "
                              f"(received raw order: {raw_order})")
        else:
            try:
                changed: bool = await self.orders_manager.upsert_order_from_raw(order_id, raw_order)

                if changed:
                    updated_order = self.orders_manager.get_order(order_id)
                    asyncio.create_task(updated_order.state.on_refresh_successful())

                    if should_notify:
                        await self.handle_order_update_notification(updated_order, is_new_order)

                return changed
            except KeyError as ke:
                self.logger.debug(f"Failed to update order : Order was not found ({ke})")
            except Exception as e:
                self.logger.exception(e, True, f"Failed to update order : {e}")
        return False

    def _is_out_of_sync_order(self, order_id) -> bool:
        return self.trades_manager.has_closing_trade_with_order_id(order_id)

    async def handle_order_instance_update(self, order, is_new_order: bool = False, should_notify: bool = True):
        try:
            changed: bool = self.orders_manager.upsert_order_instance(order)

            if changed:
                asyncio.create_task(order.state.on_refresh_successful())

                if should_notify:
                    await self.handle_order_update_notification(order, is_new_order)

            return changed
        except Exception as e:
            self.logger.exception(e, True, f"Failed to update order instance : {e}")
            return False

    async def handle_order_update_notification(self, order, is_new_order):
        """
        Notify Orders channel for Order update
        :param order: the updated order
        :param is_new_order: True if the order was created during update
        """
        try:
            await exchange_channel.get_chan(octobot_trading.constants.ORDERS_CHANNEL,
                                     self.exchange_manager.id).get_internal_producer() \
                .send(cryptocurrency=self.exchange_manager.exchange.get_pair_cryptocurrency(order.symbol),
                      symbol=order.symbol,
                      order=order.to_dict(),
                      is_from_bot=order.is_from_this_octobot,
                      is_new=is_new_order,
                      is_closed=order.is_closed())
        except ValueError as e:
            self.logger.error(f"Failed to send order update notification : {e}")

    async def handle_closed_order_update(self, order_id, raw_order) -> bool:
        """
        Handle closed order creation or update
        :param order_id: the closed order id
        :param raw_order: the closed order dict
        :return: True if the closed order has been created or updated
        """
        try:
            return await self.orders_manager.upsert_order_close_from_raw(order_id, raw_order) is not None
        except Exception as e:
            self.logger.exception(e, True, f"Failed to update order : {e}")
            return False

    async def handle_trade_update(self, symbol, trade_id, trade, should_notify: bool = True):
        try:
            changed: bool = self.trades_manager.upsert_trade(trade_id, trade)
            if should_notify:
                await exchange_channel.get_chan(octobot_trading.constants.TRADES_CHANNEL,
                                         self.exchange_manager.id).get_internal_producer() \
                    .send(cryptocurrency=self.exchange_manager.exchange.get_pair_cryptocurrency(symbol),
                          symbol=symbol,
                          trade=trade.to_dict(),
                          old_trade=False)
            return changed
        except Exception as e:
            self.logger.exception(e, True, f"Failed to update trade : {e}")
            return False

    async def handle_trade_instance_update(self, trade, should_notify: bool = True):
        try:
            changed: bool = self.trades_manager.upsert_trade_instance(trade)
            if should_notify:
                await exchange_channel.get_chan(octobot_trading.constants.TRADES_CHANNEL,
                               self.exchange_manager.id).get_internal_producer() \
                    .send(cryptocurrency=self.exchange_manager.exchange.get_pair_cryptocurrency(trade.symbol),
                          symbol=trade.symbol,
                          trade=trade.to_dict(),
                          old_trade=False)
            return changed
        except Exception as e:
            self.logger.exception(e, True, f"Failed to update trade instance : {e}")
            return False

    async def handle_position_update(self, symbol, position_id, position, should_notify: bool = True):
        try:
            changed: bool = await self.positions_manager.upsert_position(position_id, position)
            if should_notify:
                position_instance = self.positions_manager[position_id]
                await exchange_channel.get_chan(octobot_trading.constants.POSITIONS_CHANNEL,
                                         self.exchange_manager.id).get_internal_producer() \
                    .send(cryptocurrency=self.exchange_manager.exchange.get_pair_cryptocurrency(symbol),
                          symbol=symbol,
                          position=position_instance.to_dict(),
                          is_updated=changed,
                          is_liquidated=position_instance.is_liquidated())
            return changed
        except Exception as e:
            self.logger.exception(e, True, f"Failed to update position : {e}")
            return False

    async def handle_position_instance_update(self, position, should_notify: bool = True):
        try:
            changed: bool = self.positions_manager.upsert_position_instance(position)
            if should_notify:
                await exchange_channel.get_chan(octobot_trading.constants.POSITIONS_CHANNEL,
                                         self.exchange_manager.id).get_internal_producer() \
                    .send(cryptocurrency=self.exchange_manager.exchange.get_pair_cryptocurrency(position.symbol),
                          symbol=position.symbol,
                          position=position,
                          is_updated=changed,
                          is_liquidated=position.is_liquidated())
            return changed
        except Exception as e:
            self.logger.exception(e, True, f"Failed to update position instance : {e}")
            return False

    def get_order_portfolio(self, order):
        return order.linked_portfolio if order.linked_portfolio is not None else self.portfolio_manager.portfolio

    def clear(self):
        if self.portfolio_manager is not None:
            self.portfolio_manager.clear()
        if self.orders_manager is not None:
            self.orders_manager.clear()
        if self.positions_manager is not None:
            self.positions_manager.clear()
        if self.trades_manager is not None:
            self.trades_manager.clear()
