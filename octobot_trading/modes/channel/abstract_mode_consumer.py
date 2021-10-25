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
import octobot_commons.symbol_util as symbol_util

import octobot_trading.exchange_channel as exchange_channel
import octobot_trading.modes.channel as modes_channel
import octobot_trading.enums as enums
import octobot_trading.errors as errors
import octobot_trading.constants as constants
from octobot_trading.enums import ExchangeConstantsMarketStatusColumns as Ecmsc


class AbstractTradingModeConsumer(modes_channel.ModeChannelConsumer):
    def __init__(self, trading_mode):
        super().__init__()
        self.trading_mode = trading_mode
        self.exchange_manager = trading_mode.exchange_manager

    def flush(self):
        self.trading_mode = None
        self.exchange_manager = None

    async def internal_callback(self, trading_mode_name, cryptocurrency, symbol, time_frame, final_note, state, data):
        # creates a new order (or multiple split orders), always check self.can_create_order() first.
        try:
            await self.create_order_if_possible(symbol, final_note, state, data=data)
        except errors.MissingMinimalExchangeTradeVolume:
            self.logger.info(f"Not enough funds to create a new order: {self.exchange_manager.exchange_name} "
                             f"exchange minimal order volume has not been reached.")

    async def create_new_orders(self, symbol, final_note, state, **kwargs):
        raise NotImplementedError("create_new_orders is not implemented")

    async def create_order_if_possible(self, symbol, final_note, state, **kwargs) -> list:
        """
        For each trader call the creator to check if order creation is possible and create it.
        Will retry once on failure
        :return: None
        """
        self.logger.debug(f"Entering create_order_if_possible for {symbol}")
        try:
            async with self.exchange_manager.exchange_personal_data.portfolio_manager.portfolio.lock:
                if await self.can_create_order(symbol, state):
                    try:
                        return await self.create_new_orders(symbol, final_note, state, **kwargs)
                    except errors.MissingMinimalExchangeTradeVolume:
                        raise
                    except errors.MissingFunds:
                        try:
                            # second chance: force portfolio update and retry
                            await exchange_channel.get_chan(constants.BALANCE_CHANNEL,
                                                     self.exchange_manager.id).get_internal_producer(). \
                                refresh_real_trader_portfolio(True)

                            return await self.create_new_orders(symbol, final_note, state, **kwargs)
                        except errors.MissingFunds as e:
                            self.logger.error(f"Failed to create order on second attempt : {e})")
                    except Exception as e:
                        self.logger.exception(e, True, f"Error when creating order: {e}")
            self.logger.debug(f"Skipping order creation for {symbol}: not enough available funds")
            return []
        finally:
            self.logger.debug(f"Exiting create_order_if_possible for {symbol}")

    # Can be overwritten
    async def can_create_order(self, symbol, state):
        currency, market = symbol_util.split_symbol(symbol)
        portfolio = self.exchange_manager.exchange_personal_data.portfolio_manager.portfolio

        # get symbol min amount when creating order
        symbol_limit = self.exchange_manager.exchange.get_market_status(symbol)[Ecmsc.LIMITS.value]
        symbol_min_amount = symbol_limit[Ecmsc.LIMITS_AMOUNT.value][Ecmsc.LIMITS_AMOUNT_MIN.value]
        order_min_amount = symbol_limit[Ecmsc.LIMITS_COST.value][Ecmsc.LIMITS_COST_MIN.value]

        if symbol_min_amount is None:
            symbol_min_amount = 0

        # short cases => sell => need this currency
        if state == enums.EvaluatorStates.VERY_SHORT.value or state == enums.EvaluatorStates.SHORT.value:
            return portfolio.get_currency_portfolio(currency).available > symbol_min_amount

        # long cases => buy => need money(aka other currency in the pair) to buy this currency
        elif state == enums.EvaluatorStates.LONG.value or state == enums.EvaluatorStates.VERY_LONG.value:
            return portfolio.get_currency_portfolio(market).available > order_min_amount

        # other cases like neutral state or unfulfilled previous conditions
        return False

    def get_holdings_ratio(self, currency):
        return self.exchange_manager.exchange_personal_data.portfolio_manager.portfolio_value_holder \
            .get_currency_holding_ratio(currency)

    def get_number_of_traded_assets(self):
        return len(self.exchange_manager.exchange_personal_data.portfolio_manager.portfolio_value_holder
                   .origin_crypto_currencies_values)


def check_factor(min_val, max_val, factor):
    """
    Checks if factor is min_val < factor < max_val
    :param min_val:
    :param max_val:
    :param factor:
    :return:
    """
    if factor > max_val:
        return max_val
    if factor < min_val:
        return min_val
    return factor
