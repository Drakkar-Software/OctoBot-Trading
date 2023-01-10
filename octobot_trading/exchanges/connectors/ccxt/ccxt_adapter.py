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

import octobot_trading.exchanges.adapters as adapters
import octobot_trading.exchanges.connectors.ccxt.enums as ccxt_enums
import octobot_trading.exchanges.connectors.ccxt.constants as ccxt_constants
import octobot_trading.personal_data as personal_data
import octobot_trading.constants as constants
import octobot_trading.enums as enums
from octobot_trading.enums import ExchangeConstantsOrderColumns as ecoc
import octobot_commons.enums as common_enums


class CCXTAdapter(adapters.AbstractAdapter):
    def fix_order(self, raw, **kwargs):
        fixed = super().fix_order(raw, **kwargs)
        try:
            exchange_timestamp = fixed[ecoc.TIMESTAMP.value]
            fixed[ecoc.TIMESTAMP.value] = \
                self.get_uniformized_timestamp(exchange_timestamp)
        except KeyError as e:
            self.logger.error(f"Fail to cleanup order dict ({e})")
        return fixed

    def parse_order(self, fixed, **kwargs):
        # CCXT standard order parsing logic
        fixed.pop(ecoc.INFO.value)
        return fixed

    def fix_ohlcv(self, raw, **kwargs):
        fixed = super().fix_ohlcv(raw, **kwargs)
        try:
            for ohlcv in fixed:
                ohlcv[common_enums.PriceIndexes.IND_PRICE_TIME.value] = \
                    int(self.get_uniformized_timestamp(ohlcv[common_enums.PriceIndexes.IND_PRICE_TIME.value]))
                for index, value in enumerate(ohlcv[common_enums.PriceIndexes.IND_PRICE_TIME.value + 1:]):
                    ohlcv[index + 1] = float(value)
        except KeyError as e:
            self.logger.error(f"Fail to fix ohlcv ({e})")
        return fixed

    def parse_ohlcv(self, fixed, **kwargs):
        # CCXT standard ohlcv parsing logic
        return fixed

    def fix_ticker(self, raw, **kwargs):
        fixed = super().fix_ticker(raw, **kwargs)
        # CCXT standard ticker fixing logic
        return fixed

    def parse_ticker(self, fixed, **kwargs):
        # CCXT standard ticker parsing logic
        return fixed

    def fix_balance(self, raw, **kwargs):
        fixed = super().fix_balance(raw, **kwargs)
        # remove not currency specific keys
        return fixed

    def parse_balance(self, fixed, **kwargs):
        fixed.pop(constants.CONFIG_PORTFOLIO_FREE, None)
        fixed.pop(constants.CONFIG_PORTFOLIO_USED, None)
        fixed.pop(constants.CONFIG_PORTFOLIO_TOTAL, None)
        fixed.pop(ccxt_constants.CCXT_INFO, None)
        fixed.pop(ccxt_enums.ExchangeConstantsCCXTColumns.DATETIME.value, None)
        fixed.pop(ccxt_enums.ExchangeConstantsCCXTColumns.TIMESTAMP.value, None)
        return personal_data.parse_decimal_portfolio(fixed)

    def fix_order_book(self, raw, **kwargs):
        fixed = super().fix_order_book(raw, **kwargs)
        # CCXT standard order_book fixing logic
        return fixed

    def parse_order_book(self, fixed, **kwargs):
        # CCXT standard order_book parsing logic
        return fixed

    def fix_public_recent_trades(self, raw, **kwargs):
        fixed = super().fix_public_recent_trades(raw, **kwargs)
        # CCXT standard public_recent_trades fixing logic
        for recent_trade in fixed:
            try:
                recent_trade[ecoc.TIMESTAMP.value] = \
                    self.get_uniformized_timestamp(recent_trade[ecoc.TIMESTAMP.value])
            except KeyError as e:
                self.logger.error(f"Fail to clean recent_trade dict ({e})")
        return fixed

    def parse_public_recent_trades(self, fixed, **kwargs):
        # CCXT standard public_recent_trades parsing logic
        for recent_trade in fixed:
            recent_trade.pop(ecoc.INFO.value, None)
            recent_trade.pop(ecoc.DATETIME.value, None)
            recent_trade.pop(ecoc.ID.value, None)
            recent_trade.pop(ecoc.ORDER.value, None)
            recent_trade.pop(ecoc.FEE.value, None)
            recent_trade.pop(ecoc.TYPE.value, None)
            recent_trade.pop(ecoc.TAKER_OR_MAKER.value, None)
        return fixed

    def fix_trades(self, raw, **kwargs):
        fixed = super().fix_trades(raw, **kwargs)
        # CCXT standard trades fixing logic
        for trade in fixed:
            try:
                trade[ecoc.TIMESTAMP.value] = \
                    self.get_uniformized_timestamp(trade[ecoc.TIMESTAMP.value])
            except KeyError as e:
                self.logger.error(f"Fail to clean trade dict ({e})")
        return fixed

    def parse_trades(self, fixed, **kwargs):
        # CCXT standard trades parsing logic
        for trade in fixed:
            trade.pop(ecoc.INFO.value, None)
        return fixed

    def fix_position(self, raw, **kwargs):
        fixed = super().fix_position(raw, **kwargs)
        # CCXT standard position fixing logic
        return fixed

    def parse_position(self, fixed, **kwargs):
        # CCXT standard position parsing logic
        # if mode is enums.PositionMode.ONE_WAY:
        position_side = enums.PositionSide.BOTH
        # todo when handling cross positions
        # side = fixed.get(ccxt_enums.ExchangePositionCCXTColumns.SIDE.value, enums.PositionSide.UNKNOWN.value)
        # position_side = enums.PositionSide.LONG \
        #     if side == enums.PositionSide.LONG.value else enums.PositionSide.SHORT
        try:
            fixed.update({
                enums.ExchangeConstantsPositionColumns.SYMBOL.value:
                    fixed.get(fixed[ccxt_enums.ExchangePositionCCXTColumns.SYMBOL.value]),
                enums.ExchangeConstantsPositionColumns.TIMESTAMP.value:
                    fixed.get(ccxt_enums.ExchangePositionCCXTColumns.TIMESTAMP.value,
                              self.connector.get_exchange_current_time()),
                enums.ExchangeConstantsPositionColumns.SIDE.value: position_side,
                enums.ExchangeConstantsPositionColumns.MARGIN_TYPE.value:
                    fixed.get(ccxt_enums.ExchangePositionCCXTColumns.MARGIN_TYPE.value, None),
                enums.ExchangeConstantsPositionColumns.QUANTITY.value:
                    decimal.Decimal(
                        f"{fixed.get(ccxt_enums.ExchangePositionCCXTColumns.CONTRACT_SIZE.value, 0)}"),
                enums.ExchangeConstantsPositionColumns.COLLATERAL.value:
                    decimal.Decimal(
                        f"{fixed.get(ccxt_enums.ExchangePositionCCXTColumns.COLLATERAL.value, 0)}"),
                enums.ExchangeConstantsPositionColumns.NOTIONAL.value:
                    decimal.Decimal(
                        f"{fixed.get(ccxt_enums.ExchangePositionCCXTColumns.NOTIONAL.value, 0)}"),
                enums.ExchangeConstantsPositionColumns.LEVERAGE.value:
                    decimal.Decimal(
                        f"{fixed.get(ccxt_enums.ExchangePositionCCXTColumns.LEVERAGE.value, 0)}"),
                enums.ExchangeConstantsPositionColumns.UNREALIZED_PNL.value:
                    decimal.Decimal(
                        f"{fixed.get(ccxt_enums.ExchangePositionCCXTColumns.UNREALISED_PNL.value, 0)}"),
                enums.ExchangeConstantsPositionColumns.REALISED_PNL.value:
                    decimal.Decimal(
                        f"{fixed.get(ccxt_enums.ExchangePositionCCXTColumns.REALISED_PNL.value, 0)}"),
                enums.ExchangeConstantsPositionColumns.LIQUIDATION_PRICE.value:
                    decimal.Decimal(
                        f"{fixed.get(ccxt_enums.ExchangePositionCCXTColumns.LIQUIDATION_PRICE.value, 0)}"),
                enums.ExchangeConstantsPositionColumns.MARK_PRICE.value:
                    decimal.Decimal(
                        f"{fixed.get(ccxt_enums.ExchangePositionCCXTColumns.MARK_PRICE.value, 0)}"),
                enums.ExchangeConstantsPositionColumns.ENTRY_PRICE.value:
                    decimal.Decimal(
                        f"{fixed.get(ccxt_enums.ExchangePositionCCXTColumns.ENTRY_PRICE.value, 0)}"),
            })
        except KeyError as e:
            self.logger.error(f"Fail to parse position dict ({e})")
        return fixed

    def fix_funding_rate(self, raw, **kwargs):
        fixed = super().fix_funding_rate(raw, **kwargs)
        # CCXT standard funding_rate fixing logic
        return fixed

    def parse_funding_rate(self, fixed, **kwargs):
        # CCXT standard funding_rate parsing logic
        return fixed

    def fix_funding_rate_history(self, raw, **kwargs):
        fixed = super().fix_funding_rate_history(raw, **kwargs)
        # CCXT standard funding_rate_history fixing logic
        return fixed

    def parse_funding_rate_history(self, fixed, **kwargs):
        # CCXT standard funding_rate_history parsing logic
        return fixed

    def fix_mark_price(self, raw, **kwargs):
        fixed = super().fix_mark_price(raw, **kwargs)
        # CCXT standard mark_price fixing logic
        return fixed

    def parse_mark_price(self, fixed, **kwargs):
        # CCXT standard mark_price parsing logic
        return fixed

    def fix_market_status(self, raw, **kwargs):
        fixed = super().fix_market_status(raw, **kwargs)
        # CCXT standard market_status fixing logic
        return fixed

    def parse_market_status(self, fixed, **kwargs):
        # CCXT standard market_status parsing logic
        return fixed
