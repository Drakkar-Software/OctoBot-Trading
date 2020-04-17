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

from octobot_commons.channels_name import OctoBotEvaluatorsChannelsName
from octobot_commons.constants import INIT_EVAL_NOTE, CONFIG_WILDCARD
from octobot_commons.logging.logging_util import get_logger
from octobot_trading.channels.mode import ModeChannelProducer
from octobot_trading.enums import EvaluatorStates
from octobot_trading.exchanges.exchanges import Exchanges


class AbstractTradingModeProducer(ModeChannelProducer):
    def __init__(self, channel, config, trading_mode, exchange_manager):
        super().__init__(channel)
        self.logger = get_logger(self.__class__.__name__)
        self.trading_mode = trading_mode
        self.config = config
        self.exchange_manager = exchange_manager

        # shortcut
        self.exchange_name = self.exchange_manager.exchange_name

        self.final_eval = INIT_EVAL_NOTE

        self.state = None
        self.consumer = None

    def flush(self):
        self.trading_mode = None
        self.exchange_manager = None
        self.consumer = None

    # noinspection PyArgumentList
    async def start(self) -> None:
        try:
            from octobot_evaluators.channels.evaluator_channel import get_chan as get_evaluator_chan
            matrix_id = Exchanges.instance().get_exchange(self.exchange_manager.exchange_name,
                                                          self.exchange_manager.id).matrix_id
            self.consumer = await get_evaluator_chan(OctoBotEvaluatorsChannelsName.MATRIX.value,
                                                     matrix_id).new_consumer(
                callback=self.matrix_callback,
                matrix_id=Exchanges.instance().get_exchange(self.exchange_manager.exchange_name,
                                                            self.exchange_manager.id).matrix_id,
                cryptocurrency=self.trading_mode.cryptocurrency if self.trading_mode.cryptocurrency else CONFIG_WILDCARD,
                symbol=self.trading_mode.symbol if self.trading_mode.symbol else CONFIG_WILDCARD,
                time_frame=self.trading_mode.time_frame if self.trading_mode.time_frame else CONFIG_WILDCARD)
        except (KeyError, ImportError):
            self.logger.error(f"Can't connect matrix channel on {self.exchange_name}")

    async def stop(self):
        await super().stop()
        try:
            from octobot_evaluators.channels.evaluator_channel import get_chan as get_evaluator_chan
            await get_evaluator_chan(OctoBotEvaluatorsChannelsName.MATRIX.value,
                                     Exchanges.instance().get_exchange(self.exchange_manager.exchange_name,
                                                                       self.exchange_manager.id).matrix_id
                                     ).remove_consumer(self.consumer)
        except (KeyError, ImportError):
            self.logger.error(f"Can't unregister matrix channel on {self.exchange_name}")
        self.flush()

    async def matrix_callback(self, matrix_id, evaluator_name, evaluator_type,
                              eval_note, eval_note_type, exchange_name, cryptocurrency, symbol, time_frame):
        await self.finalize(exchange_name=exchange_name, matrix_id=matrix_id, cryptocurrency=cryptocurrency,
                            symbol=symbol, time_frame=time_frame)

    async def finalize(self, exchange_name: str,
                       matrix_id: str,
                       cryptocurrency: str = None,
                       symbol: str = None,
                       time_frame=None) -> None:
        """
        Finalize evaluation
        :return: None
        """
        if exchange_name != self.exchange_name:
            # Do nothing if not its exchange
            return

        try:
            await self.set_final_eval(matrix_id=matrix_id,
                                      cryptocurrency=cryptocurrency,
                                      symbol=symbol,
                                      time_frame=time_frame)
        except Exception as e:
            self.logger.exception(e, True, f"Error when finalizing: {e}")

    async def set_final_eval(self, matrix_id: str, cryptocurrency: str, symbol: str, time_frame):
        """
        Called to calculate the final note or state => when any notification appears
        :return:
        """
        raise NotImplementedError("set_final_eval not implemented")

    async def submit_trading_evaluation(self, cryptocurrency, symbol, time_frame,
                                        final_note=INIT_EVAL_NOTE,
                                        state=EvaluatorStates.NEUTRAL,
                                        data=None):
        await self.send(trading_mode_name=self.trading_mode.get_name(),
                        cryptocurrency=cryptocurrency,
                        symbol=symbol,
                        time_frame=time_frame,
                        final_note=final_note,
                        state=state,
                        data=data if data is not None else {})

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
                order_creator = self.trading_mode.get_creator(self.trading_mode.symbol)
                if await order_creator.can_create_order(self.trading_mode.symbol, self.exchange_manager, self.state, pf):
                    try:
                        _ = await order_creator.create_new_order(
                            self.final_eval,
                            self.trading_mode.symbol,
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
                                    self.trading_mode.symbol,
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
