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
from octobot_commons.channels_name import OctoBotEvaluatorsChannelsName
from octobot_commons.constants import INIT_EVAL_NOTE, CONFIG_WILDCARD
from octobot_commons.enums import ChannelConsumerPriorityLevels
from octobot_commons.logging.logging_util import get_logger
from octobot_trading.channels.mode import ModeChannelProducer
from octobot_trading.enums import EvaluatorStates
from octobot_trading.exchanges.exchanges import Exchanges


class AbstractTradingModeProducer(ModeChannelProducer):
    def __init__(self, channel, config, trading_mode, exchange_manager):
        super().__init__(channel)
        # the trading mode instance logger
        self.logger = get_logger(self.__class__.__name__)

        # the trading mode instance
        self.trading_mode = trading_mode

        # the global bot config
        self.config = config

        # the trading mode exchange manager
        self.exchange_manager = exchange_manager

        # shortcut
        self.exchange_name = self.exchange_manager.exchange_name

        # the final eval used by TradingModeConsumers, default value is INIT_EVAL_NOTE
        self.final_eval = INIT_EVAL_NOTE

        # the producer state used by TradingModeConsumers
        self.state = None

        # the matrix consumer instance
        self.matrix_consumer = None

        # Define trading modes default consumer priority level
        self.priority_level: int = ChannelConsumerPriorityLevels.MEDIUM.value

    # noinspection PyArgumentList
    async def start(self) -> None:
        """
        Start trading mode channels subscriptions
        """
        try:
            from octobot_evaluators.channels.evaluator_channel import get_chan as get_evaluator_chan
            from octobot_evaluators.enums import EvaluatorMatrixTypes
            matrix_id = Exchanges.instance().get_exchange(self.exchange_manager.exchange_name,
                                                          self.exchange_manager.id).matrix_id
            self.matrix_consumer = await get_evaluator_chan(OctoBotEvaluatorsChannelsName.MATRIX_CHANNEL.value,
                                                            matrix_id).new_consumer(
                callback=self.matrix_callback,
                priority_level=self.priority_level,
                matrix_id=Exchanges.instance().get_exchange(self.exchange_manager.exchange_name,
                                                            self.exchange_manager.id).matrix_id,
                cryptocurrency=self.trading_mode.cryptocurrency if self.trading_mode.cryptocurrency else CONFIG_WILDCARD,
                symbol=self.trading_mode.symbol if self.trading_mode.symbol else CONFIG_WILDCARD,
                evaluator_type=EvaluatorMatrixTypes.STRATEGIES.value,
                exchange_name=self.exchange_name,
                time_frame=self.trading_mode.time_frame if self.trading_mode.time_frame else CONFIG_WILDCARD)
        except (KeyError, ImportError):
            self.logger.error(f"Can't connect matrix channel on {self.exchange_name}")

    async def stop(self) -> None:
        """
        Stop trading mode channels subscriptions
        """
        await super().stop()
        if self.exchange_manager is not None:
            try:
                from octobot_evaluators.channels.evaluator_channel import get_chan as get_evaluator_chan
                await get_evaluator_chan(OctoBotEvaluatorsChannelsName.MATRIX_CHANNEL.value,
                                         Exchanges.instance().get_exchange(self.exchange_manager.exchange_name,
                                                                           self.exchange_manager.id).matrix_id
                                         ).remove_consumer(self.matrix_consumer)
            except (KeyError, ImportError):
                self.logger.error(f"Can't unregister matrix channel on {self.exchange_name}")
        self.flush()

    def flush(self) -> None:
        """
        Flush all instance objects reference
        """
        self.trading_mode = None
        self.exchange_manager = None
        self.matrix_consumer = None

    async def matrix_callback(self, matrix_id, evaluator_name, evaluator_type,
                              eval_note, eval_note_type, exchange_name, cryptocurrency, symbol, time_frame) -> None:
        """
        Called when a strategy updates the matrix
        :param matrix_id: the matrix_id
        :param evaluator_name: the evaluator name, should be the strategy name
        :param evaluator_type: the evaluator type, should be EvaluatorMatrixTypes.STRATEGIES.value
        :param eval_note: the eval note, should be the strategy eval note
        :param eval_note_type: the eval note type
        :param exchange_name: the exchange name
        :param cryptocurrency: the cryptocurrency
        :param symbol: the symbol
        :param time_frame: the time frame
        """
        await self.finalize(exchange_name=exchange_name, matrix_id=matrix_id, cryptocurrency=cryptocurrency,
                            symbol=symbol, time_frame=time_frame)

    async def finalize(self, exchange_name: str,
                       matrix_id: str,
                       cryptocurrency: str = None,
                       symbol: str = None,
                       time_frame=None) -> None:
        """
        Finalize evaluation
        """
        if exchange_name != self.exchange_name or not self.exchange_manager.trader.is_enabled:
            # Do nothing if not its exchange
            return

        try:
            await self.set_final_eval(matrix_id=matrix_id,
                                      cryptocurrency=cryptocurrency,
                                      symbol=symbol,
                                      time_frame=time_frame)
        except Exception as e:
            self.logger.exception(e, True, f"Error when finalizing: {e}")

    async def set_final_eval(self, matrix_id: str, cryptocurrency: str, symbol: str, time_frame) -> None:
        """
        Called to calculate the final note or state => when any notification appears
        """
        raise NotImplementedError("set_final_eval not implemented")

    async def submit_trading_evaluation(self, cryptocurrency, symbol, time_frame,
                                        final_note=INIT_EVAL_NOTE,
                                        state=EvaluatorStates.NEUTRAL,
                                        data=None) -> None:
        await self.send(trading_mode_name=self.trading_mode.get_name(),
                        cryptocurrency=cryptocurrency,
                        symbol=symbol,
                        time_frame=time_frame,
                        final_note=final_note,
                        state=state.value,
                        data=data if data is not None else {})

    @classmethod
    def get_should_cancel_loaded_orders(cls) -> bool:
        """
        Called by cancel_symbol_open_orders => return true if OctoBot should cancel all orders for a symbol including
        orders already existing when OctoBot started up
        """
        raise NotImplementedError("get_should_cancel_loaded_orders not implemented")

    async def cancel_symbol_open_orders(self, symbol) -> None:
        """
        Cancel all trader open orders
        """
        cancel_loaded_orders = self.get_should_cancel_loaded_orders()

        if self.exchange_manager.trader.is_enabled:
            await self.exchange_manager.trader.cancel_open_orders(symbol, cancel_loaded_orders)
