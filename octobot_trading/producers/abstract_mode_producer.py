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
from ccxt.async_support import InsufficientFunds
from octobot_channels.channels.channel import get_chan as get_channel
from octobot_commons.channels_name import OctoBotEvaluatorsChannelsName
from octobot_commons.constants import INIT_EVAL_NOTE
from octobot_commons.logging.logging_util import get_logger

from octobot_trading.constants import RECENT_TRADES_CHANNEL
from octobot_trading.channels.exchange_channel import ExchangeChannelProducer, get_chan


class AbstractTradingModeProducer(ExchangeChannelProducer):
    def __init__(self, channel, config, trading_mode, exchange_manager):
        super().__init__(channel)
        self.logger = get_logger(self.__class__.__name__)
        self.trading_mode = trading_mode
        self.config = config
        self.exchange_manager = exchange_manager

        # shortcut
        self.exchange_name = self.exchange_manager.exchange.name

        self.final_eval = INIT_EVAL_NOTE

    async def start(self) -> None:
        try:
            await get_channel(OctoBotEvaluatorsChannelsName.MATRIX.value).new_consumer(self.matrix_callback)
        except KeyError:
            self.logger.error(f"Can't connect matrix channel on {self.exchange_name}")

        await get_chan(RECENT_TRADES_CHANNEL, self.exchange_manager.exchange.name).new_consumer(
            self.recent_trades_callback)

    async def recent_trades_callback(self, exchange: str, exchange_id: str, symbol: str, recent_trades):
        await self.finalize(exchange_name=exchange, symbol=symbol)

    async def matrix_callback(self, evaluator_name, evaluator_type,
                              eval_note, eval_note_type, exchange_name, symbol, time_frame):
        await self.finalize(exchange_name=exchange_name, symbol=symbol, time_frame=time_frame)

    async def finalize(self, exchange_name, symbol, time_frame=None) -> None:
        """
        Finalize evaluation
        :return: None
        """
        if exchange_name != self.exchange_name:
            # Do nothing if not its exchange
            return

        # reset previous note
        self.final_eval = INIT_EVAL_NOTE

        try:
            await self.set_final_eval(symbol=symbol, time_frame=time_frame)
        except Exception as e:
            self.logger.error(f"Error when finalizing: {e}")
            self.logger.exception(e)

    async def set_final_eval(self, symbol, time_frame):
        """
        Called to calculate the final note or state => when any notification appears
        :return:
        """
        raise NotImplementedError("set_final_eval not implemented")

    async def submit_trading_evaluation(self, symbol, final_note=INIT_EVAL_NOTE):
        await super().send(trading_mode_name=self.trading_mode.get_name(),
                           symbol=symbol,
                           final_note=final_note)

    # def activate_deactivate_strategies(self, strategy_list, activate):
    #     for strategy in strategy_list:
    #         if strategy not in self.trading_mode.get_strategy_instances_by_classes(self.symbol):
    #             raise KeyError(f"{strategy} not in trading mode's strategy instances.")
    #
    #     strategy_instances_list = [self.trading_mode.get_strategy_instances_by_classes(self.symbol)[strategy_class]
    #                                for strategy_class in strategy_list]
    #
    #     self.symbol_evaluator.activate_deactivate_strategies(strategy_instances_list, self.exchange_manager, activate)
    #
    # def get_strategy_evaluation(self, strategy_class):
    #     for evaluated_strategies in self.symbol_evaluator.get_strategies_eval_list(self.exchange_manager):
    #         if isinstance(evaluated_strategies, strategy_class) or \
    #                 evaluated_strategies.has_class_in_parents(strategy_class):
    #             return evaluated_strategies.get_eval_note()

    @classmethod
    def get_should_cancel_loaded_orders(cls):
        """
        Called by cancel_symbol_open_orders => return true if OctoBot should cancel all orders for a symbol including
        orders already existing when OctoBot started up
        :return:
        """
        raise NotImplementedError("get_should_cancel_loaded_orders not implemented")

    async def create_order_if_possible(self) -> None:
        """
        For each trader call the creator to check if order creation is possible and create it
        :return: None
        """
        trader = self.exchange_manager.trader
        if trader.is_enabled():
            async with self.exchange_manager.exchange_personal_data.portfolio_manager.get_lock():
                pf = self.exchange_manager.exchange_personal_data.portfolio_manager
                order_creator = self.trading_mode.get_creator(self.symbol)
                if await order_creator.can_create_order(self.symbol, self.exchange_manager, self.state, pf):
                    try:
                        _ = await order_creator.create_new_order(
                            self.final_eval,
                            self.symbol,
                            self.exchange_manager,
                            trader,
                            pf,
                            self.state)
                    except InsufficientFunds:
                        if not trader.get_simulate():
                            try:
                                # second chance: force portfolio update and retry
                                await trader.force_refresh_orders_and_portfolio(pf)
                                _ = await order_creator.create_new_order(
                                    self.final_eval,
                                    self.symbol,
                                    self.exchange_manager,
                                    trader,
                                    pf,
                                    self.state)
                            except InsufficientFunds as e:
                                self.logger.error(f"Failed to create order on second attempt : {e})")

    async def cancel_symbol_open_orders(self, symbol) -> None:
        """
        Cancel all trader open orders
        :return: None
        """
        cancel_loaded_orders = self.get_should_cancel_loaded_orders()

        if self.exchange_manager.trader.is_enabled:
            await self.exchange_manager.trader.cancel_open_orders(symbol, cancel_loaded_orders)
