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

import octobot_trading.enums as enums
import octobot_trading.constants as constants
import octobot_trading.personal_data as personal_data

from tests import event_loop
from tests.exchanges import future_simulated_exchange_manager
from tests.exchanges.traders import future_trader_simulator_with_default_linear, \
    future_trader_simulator_with_default_inverse, DEFAULT_FUTURE_SYMBOL, DEFAULT_FUTURE_FUNDING_RATE


def test_get_min_max_amounts():
    # normal values
    symbol_market = {
        enums.ExchangeConstantsMarketStatusColumns.LIMITS.value: {
            enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT_MIN.value: 0.5,
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT_MAX.value: 100,
            },
            enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST_MIN.value: None,
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST_MAX.value: None
            },
            enums.ExchangeConstantsMarketStatusColumns.LIMITS_PRICE.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_PRICE_MIN.value: 0.5,
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_PRICE_MAX.value: 50
            },
        }
    }
    min_quantity, max_quantity, min_cost, max_cost, min_price, max_price = personal_data.get_min_max_amounts(
        symbol_market)
    assert min_quantity == 0.5
    assert max_quantity == 100
    assert min_cost is None
    assert max_cost is None
    assert min_price == 0.5
    assert max_price == 50

    # missing all values
    min_quantity, max_quantity, min_cost, max_cost, min_price, max_price = personal_data.get_min_max_amounts({})
    assert min_quantity is None
    assert max_quantity is None
    assert min_cost is None
    assert max_cost is None
    assert min_price is None
    assert max_price is None

    # missing all values: asign default
    min_quantity, max_quantity, min_cost, max_cost, min_price, max_price = personal_data.get_min_max_amounts({}, "xyz")
    assert min_quantity == "xyz"
    assert max_quantity == "xyz"
    assert min_cost == "xyz"
    assert max_cost == "xyz"
    assert min_price == "xyz"
    assert max_price == "xyz"

    # missing values: assign default

    symbol_market = {
        enums.ExchangeConstantsMarketStatusColumns.LIMITS.value: {
            enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT_MIN.value: 0.5,
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT_MAX.value: 100,
            },
            enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST_MIN.value: None,
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST_MAX.value: None
            }
        }
    }
    min_quantity, max_quantity, min_cost, max_cost, min_price, max_price = personal_data.get_min_max_amounts(symbol_market, "xyz")
    assert min_quantity == 0.5
    assert max_quantity == 100
    assert min_cost == "xyz"  # None is not a valid value => assign default
    assert max_cost == "xyz"  # None is not a valid value => assign default
    assert min_price == "xyz"
    assert max_price == "xyz"


def test_get_fees_for_currency():
    fee1 = {
        enums.FeePropertyColumns.CURRENCY.value: "BTC",
        enums.FeePropertyColumns.COST.value: 1
    }
    assert personal_data.get_fees_for_currency(fee1, "BTC") == 1
    assert personal_data.get_fees_for_currency(fee1, "BTC1") == 0

    fee2 = {
        enums.FeePropertyColumns.CURRENCY.value: "BTC",
        enums.FeePropertyColumns.COST.value: 0
    }
    assert personal_data.get_fees_for_currency(fee2, "BTC") == 0
    assert personal_data.get_fees_for_currency(fee2, "BTC1") == 0

    assert personal_data.get_fees_for_currency({}, "BTC") == 0
    assert personal_data.get_fees_for_currency(None, "BTC") == 0


def test_get_max_order_quantity_for_price_long_linear(future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear

    # no need to initialize the position
    default_contract.set_current_leverage(constants.ONE)
    # at price = 37000 and 9961.7672 USDT in stock, if there were no fees,
    # max quantity would be 9961.7672 / 37000 = 0.269236951351,
    # it is actually less to allow fees
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.LinearPosition(trader_inst, default_contract),
        decimal.Decimal("9961.7672"), decimal.Decimal("37000"), enums.PositionSide.LONG
    ) == decimal.Decimal('0.2689679833679833679833679834')
    #  0.269 on Bybit UI, TODO figure out the formula, this one seems not 100% accurate

    default_contract.set_current_leverage(decimal.Decimal("2"))
    # at price = 37000 and 9961.7672 USDT in stock, if there were no fees,
    # max quantity would be 9961.7672 / 37000 * 2 = 0.538473902703,
    # it is actually less to allow fees
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.LinearPosition(trader_inst, default_contract),
        decimal.Decimal("9961.7672"), decimal.Decimal("37000"), enums.PositionSide.LONG
    ) == decimal.Decimal('0.5368633127644094742798631134')
    #  0.537 on Bybit UI, TODO figure out the formula, this one seems not 100% accurate

    default_contract.set_current_leverage(constants.ONE_HUNDRED)
    # at price = 37000 and 9961.7672 USDT in stock, if there were no fees,
    # max quantity would be 9961.7672 / 37000 * 100 = 26.9236951351,
    # it is actually less to allow fees (which are huge on 100x)
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.LinearPosition(trader_inst, default_contract),
        decimal.Decimal("9961.7672"), decimal.Decimal("37000"), enums.PositionSide.LONG
    ) == decimal.Decimal('22.45512521696007934540044632')
    # no Bybit preview


def test_get_max_order_quantity_for_price_short_linear(future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear

    # no need to initialize the position
    # Differs from long due to the position closing fees at liquidation price which are higher (price is higher)
    # Therefore to open the same position size, more funds are required than for longs
    # (max quantity is lower than for longs)
    default_contract.set_current_leverage(constants.ONE)
    # at price = 37000 and 9961.7672 USDT in stock, if there were no fees,
    # max quantity would be 9961.7672 / 37000 = 0.269236951351,
    # it is actually less to allow fees
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.LinearPosition(trader_inst, default_contract),
        decimal.Decimal("9961.7672"), decimal.Decimal("37000"), enums.PositionSide.SHORT
    ) == decimal.Decimal('0.2684316563822047371399315567')
    #  0.269 on Bybit UI, TODO figure out the formula, this one seems not 100% accurate

    default_contract.set_current_leverage(decimal.Decimal("2"))
    # at price = 37000 and 9961.7672 USDT in stock, if there were no fees,
    # max quantity would be 9961.7672 / 37000 * 2 = 0.538473902703,
    # it is actually less to allow fees
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.LinearPosition(trader_inst, default_contract),
        decimal.Decimal("9961.7672"), decimal.Decimal("37000"), enums.PositionSide.SHORT
    ) == decimal.Decimal('0.5357949280623907489579131370')
    #  0.536 on Bybit UI, TODO figure out the formula, this one seems not 100% accurate

    default_contract.set_current_leverage(constants.ONE_HUNDRED)
    # at price = 37000 and 9961.7672 USDT in stock, if there were no fees,
    # max quantity would be 9961.7672 / 37000 * 100 = 26.9236951351,
    # it is actually less to allow fees (which are huge on 100x)
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.LinearPosition(trader_inst, default_contract),
        decimal.Decimal("9961.7672"), decimal.Decimal("37000"), enums.PositionSide.SHORT
    ) == decimal.Decimal('22.41773116997097013749803092')
    # no Bybit preview


def test_get_max_order_quantity_for_price_long_inverse(future_trader_simulator_with_default_inverse):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_inverse

    # no need to initialize the position
    default_contract.set_current_leverage(constants.ONE)
    # at price = 36000 and 1 btc in stock, if there were no fees,
    # max quantity would be 1 * 36000 = 36000,
    # it is actually less to allow fees
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.InversePosition(trader_inst, default_contract),
        constants.ONE, decimal.Decimal("36000"), enums.PositionSide.LONG
    ) == decimal.Decimal('35892.32303090727816550348953')
    #  35918 on Bybit UI, TODO figure out the formula, this one seems not 100% accurate

    default_contract.set_current_leverage(decimal.Decimal("2"))
    # at price = 36000 and 1 btc in stock, if there were no fees,
    # max quantity would be 1 * 36000 * 2 = 72000,
    # it is actually less to allow fees
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.InversePosition(trader_inst, default_contract),
        constants.ONE, decimal.Decimal("36000"), enums.PositionSide.LONG
    ) == decimal.Decimal('71641.79104477611940298507463')
    #  71729 on Bybit UI, TODO figure out the formula, this one seems not 100% accurate

    default_contract.set_current_leverage(constants.ONE_HUNDRED)
    # at price = 36000 and 1 btc in stock, if there were no fees,
    # max quantity would be 1 * 36000 * 100 = 3600000,
    # it is actually less to allow fees (which are huge on 100x)
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.InversePosition(trader_inst, default_contract),
        constants.ONE, decimal.Decimal("36000"), enums.PositionSide.LONG
    ) == decimal.Decimal('2997502.081598667776852622814')
    # no Bybit preview


def test_get_max_order_quantity_for_price_short_inverse(future_trader_simulator_with_default_inverse):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_inverse

    # no need to initialize the position
    # Differs from long due to the position closing fees at liquidation price which are higher (price is higher)
    # Therefore to open the same position size, less funds are required than for longs
    # (max quantity is higher than for longs)
    default_contract.set_current_leverage(constants.ONE)
    # at price = 36000 and 1 btc in stock, if there were no fees,
    # max quantity would be 1 * 36000 = 36000,
    # it is actually less to allow fees
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.InversePosition(trader_inst, default_contract),
        constants.ONE, decimal.Decimal("36000"), enums.PositionSide.SHORT
    ) == decimal.Decimal('35964.03596403596403596403596')
    #  35972 on Bybit UI, TODO figure out the formula, this one seems not 100% accurate

    default_contract.set_current_leverage(decimal.Decimal("2"))
    # at price = 36000 and 1 btc in stock, if there were no fees,
    # max quantity would be 1 * 36000 * 2 = 72000,
    # it is actually less to allow fees
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.InversePosition(trader_inst, default_contract),
        constants.ONE, decimal.Decimal("36000"), enums.PositionSide.SHORT
    ) == decimal.Decimal('71784.64606181455633100697906')
    #  71837 on Bybit UI, TODO figure out the formula, this one seems not 100% accurate

    default_contract.set_current_leverage(constants.ONE_HUNDRED)
    # at price = 36000 and 1 btc in stock, if there were no fees,
    # max quantity would be 1 * 36000 * 100 = 3600000,
    # it is actually less to allow fees (which are huge on 100x)
    assert personal_data.get_max_order_quantity_for_price(
        personal_data.InversePosition(trader_inst, default_contract),
        constants.ONE, decimal.Decimal("36000"), enums.PositionSide.SHORT
    ) == decimal.Decimal('3002502.085070892410341951626')
    # no Bybit preview
