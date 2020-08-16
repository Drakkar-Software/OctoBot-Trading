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
from octobot_commons.symbol_util import split_symbol
from octobot_commons.time_frame_manager import get_config_time_frame, find_min_time_frame, sort_time_frames
from octobot_commons.constants import CONFIG_WILDCARD, MIN_EVAL_TIME_FRAME, CONFIG_TIME_FRAME, \
    CONFIG_CRYPTO_CURRENCIES, CONFIG_CRYPTO_PAIRS, CONFIG_CRYPTO_ADD, CONFIG_CRYPTO_QUOTE
from octobot_commons.logging.logging_util import get_logger
from octobot_trading.util.initializable import Initializable


class ExchangeConfig(Initializable):
    def __init__(self, exchange_manager):
        super().__init__()
        self._logger = get_logger(self.__class__.__name__)

        self.exchange_manager = exchange_manager
        self.config = exchange_manager.config

        self.traded_cryptocurrencies = {}
        self.traded_symbol_pairs = []
        self.traded_time_frames = []
        self.real_time_time_frames = []

    async def initialize_impl(self):
        pass

    def set_config_traded_pairs(self):  # TODO
        self._set_config_traded_pairs()

    def set_config_time_frame(self):  # TODO
        self._set_config_time_frame()

    def get_shortest_time_frame(self):
        return self.traded_time_frames[-1]

    def get_traded_pairs(self, cryptocurrency=None):
        if cryptocurrency:
            if cryptocurrency in self.traded_cryptocurrencies:
                return self.traded_cryptocurrencies[cryptocurrency]
            else:
                return []
        return self.traded_symbol_pairs

    async def handle_symbol_update(self, exchange: str, exchange_id: str, crypto_currency: str, symbols: list) -> tuple:
        try:
            return self._add_tradable_symbols(crypto_currency, symbols)
        except Exception as e:
            self._logger.exception(e, True, f"Fail to handle symbol update : {e}")

    async def handle_time_frame_update(self, exchange: str, exchange_id: str, time_frames: list) -> list:
        try:
            return self._add_tradable_time_frames(time_frames)
        except Exception as e:
            self._logger.exception(e, True, f"Fail to handle time frame update : {e}")

    def _set_config_traded_pairs(self):
        self.traded_cryptocurrencies = {}
        for cryptocurrency in self.config[CONFIG_CRYPTO_CURRENCIES]:
            if self.config[CONFIG_CRYPTO_CURRENCIES][cryptocurrency][CONFIG_CRYPTO_PAIRS]:
                if self.config[CONFIG_CRYPTO_CURRENCIES][cryptocurrency][CONFIG_CRYPTO_PAIRS] != CONFIG_WILDCARD:
                    self.traded_cryptocurrencies[cryptocurrency] = []
                    for symbol in self.config[CONFIG_CRYPTO_CURRENCIES][cryptocurrency][CONFIG_CRYPTO_PAIRS]:
                        if self.exchange_manager.symbol_exists(symbol):
                            self.traded_cryptocurrencies[cryptocurrency].append(symbol)
                        else:
                            self._logger.error(f"{self.exchange_manager.exchange_name} is not supporting the "
                                               f"{symbol} trading pair.")

                else:
                    self.traded_cryptocurrencies[cryptocurrency] = \
                        self._create_wildcard_symbol_list(
                            self.config[CONFIG_CRYPTO_CURRENCIES][cryptocurrency][CONFIG_CRYPTO_QUOTE])

                    # additional pairs
                    if CONFIG_CRYPTO_ADD in self.config[CONFIG_CRYPTO_CURRENCIES][cryptocurrency]:
                        self.traded_cryptocurrencies[cryptocurrency] += \
                            self._add_tradable_symbols_from_config(cryptocurrency)

                # add to global traded pairs
                if not self.traded_cryptocurrencies[cryptocurrency]:
                    self._logger.error(
                        f"{self.exchange_manager.exchange_name} is not supporting any {cryptocurrency} trading pair "
                        f"from the current configuration.")
                self.traded_symbol_pairs += self.traded_cryptocurrencies[cryptocurrency]
            else:
                self._logger.error(f"Current configuration for {cryptocurrency} is not including any trading pair, "
                                   f"this asset can't be traded and related orders won't be loaded. "
                                   f"OctoBot requires at least one trading pair in configuration to handle an asset. "
                                   f"You can add trading pair(s) for each asset in the configuration section.")

    def _set_config_time_frame(self):
        for time_frame in get_config_time_frame(self.config):
            if self.exchange_manager.time_frame_exists(time_frame.value):
                self.traded_time_frames.append(time_frame)
        if not self.exchange_manager.is_backtesting or not self.traded_time_frames:
            # add shortest time frame for realtime evaluators or if no time frame at all has
            # been registered in backtesting
            client_shortest_time_frame = find_min_time_frame(self.exchange_manager.client_time_frames,
                                                             MIN_EVAL_TIME_FRAME)
            self.real_time_time_frames.append(client_shortest_time_frame)
        self.traded_time_frames = list(set().union(self.traded_time_frames, self.real_time_time_frames))
        self.traded_time_frames = sort_time_frames(self.traded_time_frames, reverse=True)

    @staticmethod
    def _is_tradable_with_cryptocurrency(symbol, cryptocurrency):
        return symbol if split_symbol(symbol)[1] == cryptocurrency else None

    def _add_tradable_symbols_from_config(self, cryptocurrency):
        return [
            symbol
            for symbol in self.config[CONFIG_CRYPTO_CURRENCIES][cryptocurrency][CONFIG_CRYPTO_ADD]
            if self.exchange_manager.symbol_exists(symbol)
            and symbol not in self.traded_cryptocurrencies[cryptocurrency]
        ]

    def _create_wildcard_symbol_list(self, cryptocurrency):
        return [s for s in [ExchangeConfig._is_tradable_with_cryptocurrency(symbol, cryptocurrency)
                            for symbol in self.exchange_manager.client_symbols]
                if s is not None]

    def _add_tradable_symbols(self, cryptocurrency, symbols):
        if cryptocurrency not in self.config[CONFIG_CRYPTO_CURRENCIES]:
            # TODO use exchange config
            self.config[CONFIG_CRYPTO_CURRENCIES][cryptocurrency] = {}
            self.config[CONFIG_CRYPTO_CURRENCIES][cryptocurrency][CONFIG_CRYPTO_PAIRS] = symbols
            return cryptocurrency, symbols

        # TODO manage wildcard
        symbols_to_add = [s for s in symbols
                          if self.exchange_manager.symbol_exists(s)
                          and s not in self.config[CONFIG_CRYPTO_CURRENCIES][cryptocurrency][CONFIG_CRYPTO_PAIRS]]

        # TODO use exchange config
        self.config[CONFIG_CRYPTO_CURRENCIES][cryptocurrency][CONFIG_CRYPTO_PAIRS] += symbols_to_add

        return None, symbols_to_add

    def _add_tradable_time_frames(self, time_frames):
        # TODO use exchange config
        time_frames_to_add = [tf for tf in time_frames
                              if self.exchange_manager.time_frame_exists(tf)
                              and tf not in self.config[CONFIG_TIME_FRAME]]
        return time_frames_to_add
