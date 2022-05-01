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

import octobot_backtesting.api as backtesting_api
import octobot_backtesting.importers as importers

import octobot_commons.number_util as number_util
import octobot_commons.symbol_util as symbol_util
import octobot_commons.time_frame_manager as time_frame_manager
import octobot_commons.constants as commons_constants

import octobot_trading.exchange_channel as exchange_channel
import octobot_trading.constants as constants
import octobot_trading.enums as enums
import octobot_trading.exchanges.abstract_exchange as abstract_exchange
import octobot_trading.exchange_data as exchange_data
import octobot_trading.exchanges.util as util


class ExchangeSimulator(abstract_exchange.AbstractExchange):
    def __init__(self, config, exchange_manager, backtesting):
        super().__init__(config, exchange_manager)
        self.backtesting = backtesting
        self.allowed_time_lag = constants.DEFAULT_BACKTESTING_TIME_LAG

        self.exchange_importers = []

        self.current_future_candles = {}

        self.is_authenticated = False

    async def initialize_impl(self):
        self.exchange_importers = self.backtesting.get_importers(importers.ExchangeDataImporter)
        # load symbols and time frames
        for importer in self.exchange_importers:
            self.symbols.update(importer.symbols)
            self.time_frames.update(importer.time_frames)

        # remove duplicates
        self.current_future_candles = {
            symbol: {}
            for symbol in self.symbols
        }

        # set exchange manager attributes
        self.exchange_manager.client_symbols = list(self.symbols)

    @classmethod
    def is_supporting_exchange(cls, exchange_candidate_name) -> bool:
        return True

    @classmethod
    def is_simulated_exchange(cls) -> bool:
        return True

    @staticmethod
    def handles_real_data_for_updater(channel_type, available_data):
        if channel_type in exchange_data.SIMULATOR_PRODUCERS_TO_REAL_DATA_TYPE:
            return all(data_type in available_data
                       for data_type in exchange_data.SIMULATOR_PRODUCERS_TO_REAL_DATA_TYPE[channel_type])
        return True

    async def create_backtesting_exchange_producers(self):
        for importer in self.exchange_importers:
            available_data_types = backtesting_api.get_available_data_types(importer)
            at_least_one_updater = False
            for channel_type, updater in exchange_data.UNAUTHENTICATED_UPDATER_SIMULATOR_PRODUCERS.items():
                if self._are_required_data_available(channel_type, available_data_types):
                    await updater(exchange_channel.get_chan(updater.CHANNEL_NAME,
                                                            self.exchange_manager.id), importer).run()
                    at_least_one_updater = True
            if not at_least_one_updater:
                self.logger.error(f"No updater created for {importer.symbols} backtesting")

    @staticmethod
    def _are_required_data_available(channel_type, available_data_types):
        if channel_type not in exchange_data.SIMULATOR_PRODUCERS_TO_POSSIBLE_DATA_TYPE:
            # no required data if updater is not in SIMULATOR_PRODUCERS_TO_DATA_TYPE keys
            return True
        else:
            # if updater is in SIMULATOR_PRODUCERS_TO_DATA_TYPE keys: check that at least one of the required data is
            # available
            return any(required_data_type in available_data_types
                       for required_data_type in exchange_data.SIMULATOR_PRODUCERS_TO_POSSIBLE_DATA_TYPE[channel_type])

    async def stop(self):
        self.backtesting = None
        self.exchange_importers = []
        self.exchange_manager = None

    def get_exchange_current_time(self):
        return backtesting_api.get_backtesting_current_time(self.backtesting)

    def get_available_time_frames(self):
        if self.exchange_importers:
            return [time_frame.value
                    for time_frame in backtesting_api.get_available_time_frames(next(iter(self.exchange_importers)))]
        return []

    def get_backtesting_data_files(self):
        return [backtesting_api.get_data_file_path(importer) for importer in self.exchange_importers]

    def get_market_status(self, symbol, price_example=0, with_fixer=True):
        return {
            # number of decimal digits "after the dot"
            enums.ExchangeConstantsMarketStatusColumns.PRECISION.value: {
                enums.ExchangeConstantsMarketStatusColumns.PRECISION_AMOUNT.value: 8,
                enums.ExchangeConstantsMarketStatusColumns.PRECISION_COST.value: 8,
                enums.ExchangeConstantsMarketStatusColumns.PRECISION_PRICE.value: 8,
            },
            enums.ExchangeConstantsMarketStatusColumns.LIMITS.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT.value: {
                    enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT_MIN.value: 0.00001,
                    enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT_MAX.value: 1000000000000,
                },
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_PRICE.value: {
                    enums.ExchangeConstantsMarketStatusColumns.LIMITS_PRICE_MIN.value: 0.000001,
                    enums.ExchangeConstantsMarketStatusColumns.LIMITS_PRICE_MAX.value: 1000000000000,
                },
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST.value: {
                    enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST_MIN.value: 0.001,
                    enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST_MAX.value: 1000000000000,
                },
            },
        }

    def get_uniform_timestamp(self, timestamp):
        return timestamp / 1000

    def get_fees(self, symbol):
        result_fees = {
            enums.ExchangeConstantsMarketPropertyColumns.TAKER.value: constants.CONFIG_DEFAULT_SIMULATOR_FEES,
            enums.ExchangeConstantsMarketPropertyColumns.MAKER.value: constants.CONFIG_DEFAULT_SIMULATOR_FEES,
            enums.ExchangeConstantsMarketPropertyColumns.FEE.value: constants.CONFIG_DEFAULT_SIMULATOR_FEES
        }

        if commons_constants.CONFIG_SIMULATOR in self.config and \
                commons_constants.CONFIG_SIMULATOR_FEES in self.config[commons_constants.CONFIG_SIMULATOR]:
            self._read_fees_from_config(result_fees)

        return result_fees

    def _read_fees_from_config(self, result_fees):
        # in configuration, fees are in %, convert them to decimal
        if commons_constants.CONFIG_SIMULATOR_FEES_MAKER in \
                self.config[commons_constants.CONFIG_SIMULATOR][commons_constants.CONFIG_SIMULATOR_FEES]:
            result_fees[enums.ExchangeConstantsMarketPropertyColumns.MAKER.value] = \
                self.config[commons_constants.CONFIG_SIMULATOR][commons_constants.CONFIG_SIMULATOR_FEES][
                    commons_constants.CONFIG_SIMULATOR_FEES_MAKER] / 100

        if commons_constants.CONFIG_SIMULATOR_FEES_MAKER in self.config[commons_constants.CONFIG_SIMULATOR][
           commons_constants.CONFIG_SIMULATOR_FEES]:
            result_fees[enums.ExchangeConstantsMarketPropertyColumns.TAKER.value] = \
                self.config[commons_constants.CONFIG_SIMULATOR][commons_constants.CONFIG_SIMULATOR_FEES][
                    commons_constants.CONFIG_SIMULATOR_FEES_TAKER] / 100

        if commons_constants.CONFIG_SIMULATOR_FEES_WITHDRAW in self.config[commons_constants.CONFIG_SIMULATOR][
           commons_constants.CONFIG_SIMULATOR_FEES]:
            result_fees[enums.ExchangeConstantsMarketPropertyColumns.FEE.value] = \
                self.config[commons_constants.CONFIG_SIMULATOR][commons_constants.CONFIG_SIMULATOR_FEES][
                    commons_constants.CONFIG_SIMULATOR_FEES_WITHDRAW] / 100

    # returns {
    #     'type': takerOrMaker,
    #     'currency': 'BTC', // the unified fee currency code
    #     'rate': percentage, // the fee rate, 0.05% = 0.0005, 1% = 0.01, ...
    #     'cost': feePaid, // the fee cost (amount * fee rate)
    # }
    def get_trade_fee(self, symbol, order_type, quantity, price, taker_or_maker):
        if not taker_or_maker:
            taker_or_maker = enums.ExchangeConstantsMarketPropertyColumns.TAKER.value
        symbol_fees = self.get_fees(symbol)
        rate = symbol_fees[taker_or_maker]
        currency, market = symbol_util.split_symbol(symbol)
        fee_currency = currency

        precision = self.get_market_status(symbol)[enums.ExchangeConstantsMarketStatusColumns.PRECISION.value] \
            [enums.ExchangeConstantsMarketStatusColumns.PRECISION_PRICE.value]
        cost = float(number_util.round_into_str_with_max_digits(float(quantity) * rate, precision))

        if util.get_order_side(order_type) == enums.TradeOrderSide.SELL.value:
            cost = float(number_util.round_into_str_with_max_digits(cost * float(price), precision))
            fee_currency = market

        return {
            enums.FeePropertyColumns.TYPE.value: taker_or_maker,
            enums.FeePropertyColumns.CURRENCY.value: fee_currency,
            enums.FeePropertyColumns.RATE.value: rate,
            enums.FeePropertyColumns.COST.value: decimal.Decimal(str(cost)),
        }

    def get_time_frames(self, importer):
        return time_frame_manager.sort_time_frames(list(set(backtesting_api.get_available_time_frames(importer)) &
                                                        set(self.exchange_manager.exchange_config.traded_time_frames)),
                                                   reverse=True)

    def get_split_pair_from_exchange(self, pair) -> (str, str):
        return symbol_util.split_symbol(pair)

    def get_pair_cryptocurrency(self, pair) -> str:
        return self.get_split_pair_from_exchange(pair)[0]

    @staticmethod
    def get_real_available_data(exchange_importers):
        available_data = set()
        for importer in exchange_importers:
            available_data = available_data.union(backtesting_api.get_available_data_types(importer))
        return available_data

    def get_max_handled_pair_with_time_frame(self) -> int:
        """
        :return: the maximum number of simultaneous pairs * time_frame that this exchange can handle.
        """
        return constants.INFINITE_MAX_HANDLED_PAIRS_WITH_TIMEFRAME
