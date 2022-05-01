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
import uuid

import octobot_commons.logging as logging

import octobot_trading.exchange_channel as exchange_channel
import octobot_trading.constants as constants
import octobot_trading.errors as errors
import octobot_trading.enums as enums
import octobot_trading.personal_data.portfolios.portfolio_manager as portfolio_manager
import octobot_trading.personal_data.positions.positions_manager as positions_manager
import octobot_trading.personal_data.orders.orders_manager as orders_manager
import octobot_trading.personal_data.trades.trades_manager as trades_manager
import octobot_trading.personal_data.transactions.transactions_manager as transactions_manager
import octobot_trading.personal_data.transactions.transaction_factory as transaction_factory
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
        self.transactions_manager = None

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
                self.transactions_manager = transactions_manager.TransactionsManager()
                await self.portfolio_manager.initialize()
                await self.trades_manager.initialize()
                await self.orders_manager.initialize()
                await self.positions_manager.initialize()
                await self.transactions_manager.initialize()
            except Exception as e:
                self.logger.exception(e, True, f"Error when initializing : {e}. "
                                               f"{self.exchange.name} personal data disabled.")

    # updates
    async def handle_portfolio_update(self, balance, should_notify: bool = True, is_diff_update=False) -> bool:
        try:
            changed: bool = self.portfolio_manager.handle_balance_update(balance, is_diff_update=is_diff_update)
            if should_notify:
                await self.handle_portfolio_update_notification(balance)
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
                await self.handle_portfolio_update_notification(self.portfolio_manager.portfolio.portfolio)

                if self.exchange_manager.is_future:
                    # should this be done only "if should_notify" ?
                    await self.handle_position_instance_update(
                        order.exchange_manager.exchange_personal_data.positions_manager.get_order_position(order),
                        should_notify=True)
                elif self.exchange_manager.is_margin:
                    pass  # TODO : nothing for now
            return changed
        except AttributeError as e:
            self.logger.exception(e, True, f"Failed to update balance : {e}")
            return False

    async def handle_portfolio_update_from_funding(self, position, funding_rate,
                                                   require_exchange_update: bool = True,
                                                   should_notify: bool = True) -> bool:
        try:
            try:
                changed = await self.portfolio_manager.handle_balance_update_from_funding(
                    position=position, funding_rate=funding_rate, require_exchange_update=require_exchange_update)
            except errors.PortfolioNegativeValueError:
                self.logger.warning("Not enough available balance to handle funding. Reducing position margin...")
                await position.update(update_margin=-position.value * funding_rate)
                changed = True
            transaction_factory.create_fee_transaction(self.exchange_manager, position.get_currency(), position.symbol,
                                                       quantity=-abs(position.value) * funding_rate,
                                                       funding_rate=funding_rate)
            if should_notify:
                await self.handle_portfolio_update_notification(self.portfolio_manager.portfolio.portfolio)
            return changed
        except AttributeError as e:
            self.logger.exception(e, True, f"Failed to update balance : {e}")
            return False

    async def handle_portfolio_update_from_withdrawal(self, amount, currency, should_notify: bool = True) -> bool:
        changed = await self.portfolio_manager.handle_balance_update_from_withdrawal(amount, currency)
        transaction_factory.create_blockchain_transaction(
            self.exchange_manager, is_deposit=False, currency=currency, quantity=amount,
            blockchain_type=enums.BlockchainTypes.SIMULATED_WITHDRAWAL.value,
            blockchain_transaction_id=str(uuid.uuid4())
        )
        if should_notify:
            await self.handle_portfolio_update_notification(self.portfolio_manager.portfolio.portfolio)
        return changed

    async def handle_portfolio_update_notification(self, balance):
        """
        Notify Balance channel from portfolio update
        :param balance: the updated balance
        """
        try:
            await exchange_channel.get_chan(constants.BALANCE_CHANNEL, self.exchange_manager.id). \
                get_internal_producer().send(balance)
        except ValueError as e:
            self.logger.error(f"Failed to send balance update notification : {e}")

    async def handle_portfolio_profitability_update(self, balance, mark_price, symbol, should_notify: bool = True):
        try:
            portfolio_profitability = self.portfolio_manager.portfolio_profitability

            if balance is not None:
                self.portfolio_manager.handle_balance_updated()

            if mark_price is not None and symbol is not None:
                self.portfolio_manager.handle_mark_price_update(symbol=symbol, mark_price=mark_price)
                # update historical portfolio value after mark price update
                await self.portfolio_manager.update_historical_portfolio_values()

            if should_notify:
                await exchange_channel.get_chan(constants.BALANCE_PROFITABILITY_CHANNEL,
                                                self.exchange_manager.id).get_internal_producer() \
                    .send(profitability=portfolio_profitability.profitability,
                          profitability_percent=portfolio_profitability.profitability_percent,
                          market_profitability_percent=portfolio_profitability.market_profitability_percent,
                          initial_portfolio_current_profitability=portfolio_profitability.initial_portfolio_current_profitability)
        except Exception as e:
            self.logger.exception(e, True, f"Failed to update portfolio profitability : {e}")

    async def handle_order_update_from_raw(self, order_id, raw_order,
                                           is_new_order: bool = False,
                                           should_notify: bool = True,
                                           is_from_exchange=True) -> bool:
        # Orders can sometimes be out of sync between different exchange endpoints (ex: binance order API vs
        # open_orders API which is slower).
        # Always check if this order has not already been closed previously (most likely during the last
        # seconds/minutes)
        if self._is_out_of_sync_order(order_id):
            self.logger.debug(f"Ignored update for order with {order_id}: this order has already been closed "
                              f"(received raw order: {raw_order})")
        else:
            try:
                changed: bool = await self.orders_manager.upsert_order_from_raw(order_id, raw_order, is_from_exchange)

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
            changed: bool = await self.orders_manager.upsert_order_instance(order)

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
            await exchange_channel.get_chan(constants.ORDERS_CHANNEL,
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

    async def handle_trade_update(self, symbol, trade_id, trade,
                                  is_old_trade: bool = False, should_notify: bool = True):
        try:
            changed: bool = self.trades_manager.upsert_trade(trade_id, trade)
            if changed and should_notify:
                updated_trade = self.trades_manager.get_trade(trade_id)
                await self.handle_trade_update_notification(updated_trade, is_old_trade=is_old_trade)
            return changed
        except Exception as e:
            self.logger.exception(e, True, f"Failed to update trade : {e}")
            return False

    async def handle_trade_instance_update(self, trade, should_notify: bool = True):
        try:
            changed: bool = self.trades_manager.upsert_trade_instance(trade)
            if should_notify:
                await self.handle_trade_update_notification(trade, is_old_trade=False)
            return changed
        except Exception as e:
            self.logger.exception(e, True, f"Failed to update trade instance : {e}")
            return False

    async def handle_trade_update_notification(self, trade, is_old_trade=False):
        """
        Notify Trade channel from Trade update
        :param trade: the updated trade
        :param is_old_trade: if the trade has already been loaded
        """
        try:
            await exchange_channel.get_chan(constants.TRADES_CHANNEL,
                                            self.exchange_manager.id).get_internal_producer() \
                .send(cryptocurrency=self.exchange_manager.exchange.get_pair_cryptocurrency(trade.symbol),
                      symbol=trade.symbol,
                      trade=trade.to_dict(),
                      old_trade=is_old_trade)
        except ValueError as e:
            self.logger.error(f"Failed to send trade update notification : {e}")

    async def handle_position_update(self, symbol, side, position, should_notify: bool = True):
        try:
            changed: bool = await self.positions_manager.upsert_position(symbol, side, position)
            if should_notify:
                position_instance = self.positions_manager.get_symbol_position(
                    symbol=symbol, side=None if position.symbol_contract.is_one_way_position_mode() else side)
                await self.handle_position_update_notification(position_instance, is_updated=changed)
            return changed
        except Exception as e:
            self.logger.exception(e, True, f"Failed to update position : {e}")
            return False

    async def handle_position_instance_update(self, position, should_notify: bool = True):
        try:
            changed: bool = self.positions_manager.upsert_position_instance(position)
            if should_notify:
                await self.handle_position_update_notification(position, is_updated=changed)
            return changed
        except Exception as e:
            self.logger.exception(e, True, f"Failed to update position instance : {e}")
            return False

    async def handle_position_update_notification(self, position, is_updated=True):
        """
        Notify Positions channel for Position update
        TODO send position dict
        :param position: the updated position
        :param is_updated: if the position has been updated
        """
        try:
            await exchange_channel.get_chan(constants.POSITIONS_CHANNEL,
                                            self.exchange_manager.id).get_internal_producer() \
                .send(cryptocurrency=self.exchange_manager.exchange.get_pair_cryptocurrency(position.symbol),
                      symbol=position.symbol,
                      position=position,
                      is_updated=is_updated)
        except ValueError as e:
            self.logger.error(f"Failed to send position update notification : {e}")

    async def stop(self):
        if self.portfolio_manager is not None:
            await self.portfolio_manager.stop()
        self.clear()

    def clear(self):
        if self.portfolio_manager is not None:
            self.portfolio_manager.clear()
        if self.orders_manager is not None:
            self.orders_manager.clear()
        if self.positions_manager is not None:
            self.positions_manager.clear()
        if self.trades_manager is not None:
            self.trades_manager.clear()
        if self.transactions_manager is not None:
            self.transactions_manager.clear()
