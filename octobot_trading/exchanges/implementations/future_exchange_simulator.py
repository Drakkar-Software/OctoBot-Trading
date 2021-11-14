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
import decimal

import octobot_trading.constants as constants
import octobot_trading.enums as enums
import octobot_trading.exchange_data.contracts as contracts
import octobot_trading.exchanges.connectors as exchange_connectors
import octobot_trading.exchanges.types as exchanges_types


class FutureExchangeSimulator(exchanges_types.FutureExchange):
    DEFAULT_SYMBOL_LEVERAGE = constants.ONE
    DEFAULT_SYMBOL_MAX_LEVERAGE = constants.ONE_HUNDRED
    DEFAULT_SYMBOL_MARGIN_TYPE = enums.MarginType.ISOLATED
    DEFAULT_SYMBOL_CONTRACT_TYPE = enums.FutureContractType.LINEAR_PERPETUAL
    DEFAULT_SYMBOL_POSITION_MODE = enums.PositionMode.ONE_WAY
    DEFAULT_SYMBOL_FUNDING_RATE = decimal.Decimal("0.00005")

    def __init__(self, config, exchange_manager, backtesting):
        super().__init__(config, exchange_manager)
        self.exchange_importers = []
        self.backtesting = backtesting
        self.connector = exchange_connectors.ExchangeSimulator(config, exchange_manager, backtesting=backtesting)

    async def initialize_impl(self):
        await self.connector.initialize()
        self.symbols = self.connector.symbols
        self.time_frames = self.connector.time_frames
        self.exchange_importers = self.connector.exchange_importers

    async def stop(self) -> None:
        await self.connector.stop()
        self.exchange_manager = None
        self.backtesting = None
        self.exchange_importers = None

    @classmethod
    def get_name(cls) -> str:
        return cls.__name__

    @classmethod
    def is_supporting_exchange(cls, exchange_candidate_name) -> bool:
        return exchange_connectors.ExchangeSimulator.is_supporting_exchange(exchange_candidate_name)

    @classmethod
    def is_simulated_exchange(cls) -> bool:
        return exchange_connectors.ExchangeSimulator.is_simulated_exchange()

    def get_exchange_current_time(self):
        return self.connector.get_exchange_current_time()

    def get_available_time_frames(self):
        return self.connector.get_available_time_frames()

    def get_split_pair_from_exchange(self, pair) -> (str, str):
        return self.connector.get_split_pair_from_exchange(pair)

    def get_pair_cryptocurrency(self, pair) -> str:
        return self.connector.get_pair_cryptocurrency(pair)

    @staticmethod
    def get_real_available_data(exchange_importers):
        return exchange_connectors.ExchangeSimulator.get_real_available_data(exchange_importers)

    @staticmethod
    def handles_real_data_for_updater(channel_type, available_data):
        return exchange_connectors.ExchangeSimulator.handles_real_data_for_updater(channel_type=channel_type,
                                                                                   available_data=available_data)

    async def create_backtesting_exchange_producers(self):
        return await self.connector.create_backtesting_exchange_producers()

    def get_market_status(self, symbol, price_example=None, with_fixer=True):
        return self.connector.get_market_status(symbol, price_example=price_example, with_fixer=with_fixer)

    def get_uniform_timestamp(self, timestamp):
        return self.connector.get_uniform_timestamp(timestamp)

    def get_fees(self, symbol):
        return self.connector.get_fees(symbol)

    def get_trade_fee(self, symbol, order_type, quantity, price, taker_or_maker):
        return self.connector.get_trade_fee(symbol, order_type, quantity, price, taker_or_maker)

    def get_time_frames(self, importer):
        return self.connector.get_time_frames(importer)

    def get_current_future_candles(self):
        return self.connector.current_future_candles

    async def load_pair_future_contract(self, pair: str):
        """
        Create a new FutureContract for the pair
        :param pair: the pair
        """
        self.logger.debug(f"Loading {pair} contract...")
        self.pair_contracts[pair] = contracts.FutureContract(
            pair=pair,
            current_leverage=self.DEFAULT_SYMBOL_LEVERAGE,
            maximum_leverage=self.DEFAULT_SYMBOL_MAX_LEVERAGE,
            margin_type=self.DEFAULT_SYMBOL_MARGIN_TYPE,
            contract_type=self.DEFAULT_SYMBOL_CONTRACT_TYPE,
            position_mode=self.DEFAULT_SYMBOL_POSITION_MODE)

    async def get_symbol_leverage(self, symbol: str):
        return self.DEFAULT_SYMBOL_LEVERAGE

    async def get_margin_type(self, symbol: str):
        return self.DEFAULT_SYMBOL_MARGIN_TYPE

    async def get_contract_type(self, symbol: str):
        return self.DEFAULT_SYMBOL_CONTRACT_TYPE

    async def get_funding_rate(self, symbol: str, **kwargs: dict):
        return self.DEFAULT_SYMBOL_FUNDING_RATE

    async def get_position_mode(self, symbol: str, **kwargs: dict):
        return self.DEFAULT_SYMBOL_POSITION_MODE

    async def set_symbol_leverage(self, symbol: str, leverage: int):
        pair_contract = self.get_pair_future_contract(symbol)
        pair_contract.set_current_leverage(leverage)

    async def set_symbol_margin_type(self, symbol: str, isolated: bool):
        pair_contract = self.get_pair_future_contract(symbol)
        pair_contract.set_margin_type(is_isolated=isolated)

    async def set_symbol_position_mode(self, symbol: str, one_way: bool):
        pair_contract = self.get_pair_future_contract(symbol)
        pair_contract.set_position_mode(is_one_way=one_way)
