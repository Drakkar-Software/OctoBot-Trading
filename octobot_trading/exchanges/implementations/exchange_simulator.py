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
import octobot_trading.constants as constants
import octobot_trading.exchanges.util as exchange_util
import octobot_trading.exchanges.connectors.simulator.exchange_simulator_connector as exchange_simulator_connector
import octobot_trading.exchanges.types.rest_exchange as rest_exchange


class ExchangeSimulator(rest_exchange.RestExchange):
    DEFAULT_CONNECTOR_CLASS = exchange_simulator_connector.ExchangeSimulatorConnector

    def __init__(self, config, exchange_manager, backtesting):
        self.backtesting = backtesting
        self.exchange_importers = []
        self.exchange_tentacle = None
        super().__init__(config, exchange_manager)

    def _create_connector(self, config, exchange_manager, connector_class):
        return (connector_class or self.DEFAULT_CONNECTOR_CLASS)(
            config,
            exchange_manager,
            self.backtesting,
            adapter_class=self.get_adapter_class(),
        )

    async def initialize_impl(self):
        await super().initialize_impl()
        self.exchange_importers = self.connector.exchange_importers
        if self.connector.should_adapt_market_statuses():
            await self._init_exchange_tentacle()

    async def _init_exchange_tentacle(self):
        origin_ignore_config = self.exchange_manager.ignore_config
        try:
            self.exchange_tentacle = None
            self.exchange_manager.ignore_config = True
            # initialize a locale exchange_tentacle to be able to access adapters for market statuses
            if exchange_class := exchange_util.get_rest_exchange_class(
                self.exchange_manager.exchange_name, self.exchange_manager.tentacles_setup_config
            ):
                self.exchange_tentacle = exchange_class(self.exchange_manager.config, self.exchange_manager)
        finally:
            self.exchange_manager.ignore_config = origin_ignore_config
            # reset ignore_config as soon as possible
        if self.exchange_tentacle:
            if adapter_class := self.exchange_tentacle.get_adapter_class():
                self.connector.adapter.set_tentacles_adapter_proxy(adapter_class)
            # do not keep the created ccxt exchange
            await self.exchange_tentacle.stop()

    async def stop(self) -> None:
        await super().stop()
        self.backtesting = None
        self.exchange_importers = None
        self.exchange_tentacle = None

    @classmethod
    def is_supporting_exchange(cls, exchange_candidate_name) -> bool:
        return exchange_simulator_connector.ExchangeSimulatorConnector.is_supporting_exchange(exchange_candidate_name)

    @classmethod
    def is_simulated_exchange(cls) -> bool:
        return exchange_simulator_connector.ExchangeSimulatorConnector.is_simulated_exchange()

    async def create_backtesting_exchange_producers(self):
        return await self.connector.create_backtesting_exchange_producers()

    def _should_fix_market_status(self):
        return (self.exchange_tentacle or self).FIX_MARKET_STATUS

    def _should_remove_market_status_limits(self):
        return (self.exchange_tentacle or self).REMOVE_MARKET_STATUS_PRICE_LIMITS

    def _should_adapt_market_status_for_contract_size(self):
        return (self.exchange_tentacle or self).ADAPT_MARKET_STATUS_FOR_CONTRACT_SIZE

    def get_available_time_frames(self):
        return self.connector.get_available_time_frames()

    def get_time_frames(self, importer):
        return self.connector.get_time_frames(importer)

    def use_accurate_price_time_frame(self) -> bool:
        return self.connector.use_accurate_price_time_frame()

    def get_current_future_candles(self):
        return self.connector.current_future_candles

    def get_backtesting_data_files(self):
        return self.connector.get_backtesting_data_files()

    async def load_pair_future_contract(self, pair: str):
        """
        Create a new FutureContract for the pair
        :param pair: the pair
        """
        return self.create_pair_contract(
            pair=pair,
            current_leverage=constants.DEFAULT_SYMBOL_LEVERAGE,
            contract_size=constants.DEFAULT_SYMBOL_CONTRACT_SIZE,
            margin_type=constants.DEFAULT_SYMBOL_MARGIN_TYPE,
            contract_type=self.exchange_manager.exchange_config.backtesting_exchange_config.future_contract_type,
            position_mode=constants.DEFAULT_SYMBOL_POSITION_MODE,
            maintenance_margin_rate=constants.DEFAULT_SYMBOL_MAINTENANCE_MARGIN_RATE,
            maximum_leverage=constants.DEFAULT_SYMBOL_MAX_LEVERAGE
        )

    async def get_symbol_leverage(self, symbol: str, **kwargs: dict):
        return constants.DEFAULT_SYMBOL_LEVERAGE

    async def get_margin_type(self, symbol: str):
        return constants.DEFAULT_SYMBOL_MARGIN_TYPE

    def get_contract_type(self, symbol: str):
        return self.exchange_manager.exchange_config.backtesting_exchange_config.future_contract_type

    async def get_funding_rate(self, symbol: str, **kwargs: dict):
        return self.exchange_manager.exchange_config.backtesting_exchange_config.funding_rate

    async def get_position_mode(self, symbol: str, **kwargs: dict):
        return constants.DEFAULT_SYMBOL_POSITION_MODE

    async def set_symbol_leverage(self, symbol: str, leverage: float, **kwargs):
        pass  # let trader update the contract

    async def set_symbol_margin_type(self, symbol: str, isolated: bool, **kwargs: dict):
        pass  # let trader update the contract

    async def set_symbol_position_mode(self, symbol: str, one_way: bool):
        pass  # let trader update the contract
