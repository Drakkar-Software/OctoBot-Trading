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
import octobot_commons.constants as common_constants


class CCXTAdapter(adapters.AbstractAdapter):
    def fix_order(self, raw, **kwargs):
        fixed = super().fix_order(raw, **kwargs)
        try:
            exchange_timestamp = fixed[ecoc.TIMESTAMP.value]
            fixed[ecoc.TIMESTAMP.value] = \
                self.get_uniformized_timestamp(exchange_timestamp)
        except KeyError as e:
            self.logger.error(f"Fail to cleanup order dict ({e})")
        self._register_exchange_fees(fixed)
        return fixed

    def parse_order(self, fixed, **kwargs):
        # CCXT standard order parsing logic
        fixed.pop(ecoc.INFO.value)
        return fixed

    def _register_exchange_fees(self, order_or_trade):
        try:
            fees = order_or_trade[enums.ExchangeConstantsOrderColumns.FEE.value]
            fees[enums.FeePropertyColumns.EXCHANGE_ORIGINAL_COST.value] = fees[enums.FeePropertyColumns.COST.value]
            fees[enums.FeePropertyColumns.IS_FROM_EXCHANGE.value] = True
        except (KeyError, TypeError):
            pass

    def _fix_ohlcv_prices(self, ohlcv):
        for index, value in enumerate(ohlcv[common_enums.PriceIndexes.IND_PRICE_TIME.value + 1:]):
            ohlcv[index + 1] = float(value)

    def fix_ohlcv(self, raw, **kwargs):
        fixed = super().fix_ohlcv(raw, **kwargs)
        # ensure open time is not the current time but the actual candle open time
        # time_frame kwarg has to be passed to parse candle time
        candles_s = 1
        if "time_frame" in kwargs:
            candles_s = common_enums.TimeFramesMinutes[common_enums.TimeFrames(kwargs["time_frame"])] * \
                        common_constants.MINUTE_TO_SECONDS
        for index, ohlcv in enumerate(fixed):
            try:
                int_val = int(self.get_uniformized_timestamp(ohlcv[common_enums.PriceIndexes.IND_PRICE_TIME.value]))
                ohlcv[common_enums.PriceIndexes.IND_PRICE_TIME.value] = int_val - (int_val % candles_s)
                self._fix_ohlcv_prices(ohlcv)
            except TypeError:
                # the last candle might not be properly set
                if self.connector.exchange_manager.exchange.DUMP_INCOMPLETE_LAST_CANDLE and index == len(fixed) - 1:
                    return fixed[:-1]
                raise
            except KeyError as e:
                self.logger.error(f"Fail to fix ohlcv ({e})")
        return fixed

    def parse_ohlcv(self, fixed, **kwargs):
        # CCXT standard ohlcv parsing logic
        return fixed

    def fix_kline(self, raw, **kwargs):
        fixed = super().fix_kline(raw, **kwargs)
        for index, kline in enumerate(fixed):
            try:
                kline[common_enums.PriceIndexes.IND_PRICE_TIME.value] = \
                    int(self.get_uniformized_timestamp(kline[common_enums.PriceIndexes.IND_PRICE_TIME.value]))
                self._fix_ohlcv_prices(kline)
            except TypeError:
                # the last candle might not be properly set
                if self.connector.exchange_manager.exchange.DUMP_INCOMPLETE_LAST_CANDLE and index == len(fixed) - 1:
                    return fixed[:-1]
                raise
            except KeyError as e:
                self.logger.error(f"Fail to fix kline ({e})")
        return fixed

    def parse_kline(self, fixed, **kwargs):
        # CCXT standard kline parsing logic
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
                if trade[enums.ExchangeConstantsOrderColumns.TYPE.value] is None:
                    trade[enums.ExchangeConstantsOrderColumns.TYPE.value] = enums.TradeOrderType.MARKET.value \
                        if trade[ccxt_enums.ExchangeOrderCCXTColumns.TAKER_OR_MAKER.value] \
                        == enums.ExchangeConstantsMarketPropertyColumns.TAKER.value \
                        else enums.TradeOrderType.LIMIT.value
            except KeyError as e:
                self.logger.error(f"Fail to clean trade dict ({e})")
            self._register_exchange_fees(trade)
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

    def parse_position(self, fixed, force_empty=False, **kwargs):
        # CCXT standard position parsing logic
        # if mode is enums.PositionMode.ONE_WAY:
        original_side = fixed.get(ccxt_enums.ExchangePositionCCXTColumns.SIDE.value)
        position_side = enums.PositionSide.BOTH
        # todo when handling cross positions
        # side = fixed.get(ccxt_enums.ExchangePositionCCXTColumns.SIDE.value, enums.PositionSide.UNKNOWN.value)
        # position_side = enums.PositionSide.LONG \
        #     if side == enums.PositionSide.LONG.value else enums.PositionSide.
        symbol = fixed.get(ccxt_enums.ExchangePositionCCXTColumns.SYMBOL.value)
        contract_size = decimal.Decimal(str(fixed.get(ccxt_enums.ExchangePositionCCXTColumns.CONTRACT_SIZE.value, 0)))
        contracts = constants.ZERO if force_empty \
            else decimal.Decimal(str(fixed.get(ccxt_enums.ExchangePositionCCXTColumns.CONTRACTS.value, 0)))
        is_empty = contracts == constants.ZERO
        liquidation_price = fixed.get(ccxt_enums.ExchangePositionCCXTColumns.LIQUIDATION_PRICE.value, 0)
        if force_empty or liquidation_price is None:
            liquidation_price = constants.NaN
        else:
            liquidation_price = decimal.Decimal(str(liquidation_price))
        try:
            fixed.update({
                enums.ExchangeConstantsPositionColumns.SYMBOL.value: symbol,
                enums.ExchangeConstantsPositionColumns.TIMESTAMP.value:
                    fixed.get(ccxt_enums.ExchangePositionCCXTColumns.TIMESTAMP.value,
                              self.connector.get_exchange_current_time()),
                enums.ExchangeConstantsPositionColumns.SIDE.value: position_side,
                enums.ExchangeConstantsPositionColumns.MARGIN_TYPE.value:
                    fixed.get(ccxt_enums.ExchangePositionCCXTColumns.MARGIN_TYPE.value, None),
                enums.ExchangeConstantsPositionColumns.SIZE.value:
                    contract_size * contracts if original_side == enums.PositionSide.LONG.value
                    else -contract_size * contracts,
                enums.ExchangeConstantsPositionColumns.CONTRACT_TYPE.value:
                    self.connector.exchange_manager.exchange.get_contract_type(symbol),
                enums.ExchangeConstantsPositionColumns.LEVERAGE.value:
                    self.safe_decimal(fixed, ccxt_enums.ExchangePositionCCXTColumns.LEVERAGE.value,
                                      constants.DEFAULT_SYMBOL_LEVERAGE),
                enums.ExchangeConstantsPositionColumns.POSITION_MODE.value: None if is_empty else
                enums.PositionMode.HEDGE if fixed.get(ccxt_enums.ExchangePositionCCXTColumns.HEDGED.value, True)
                else enums.PositionMode.ONE_WAY,
                # next values are always 0 when the position empty (0 contracts)
                enums.ExchangeConstantsPositionColumns.COLLATERAL.value: constants.ZERO if is_empty else
                decimal.Decimal(
                    f"{fixed.get(ccxt_enums.ExchangePositionCCXTColumns.COLLATERAL.value, 0)}"),
                enums.ExchangeConstantsPositionColumns.NOTIONAL.value: constants.ZERO if is_empty else
                decimal.Decimal(
                    f"{fixed.get(ccxt_enums.ExchangePositionCCXTColumns.NOTIONAL.value, 0)}"),
                enums.ExchangeConstantsPositionColumns.INITIAL_MARGIN.value: constants.ZERO if is_empty else
                decimal.Decimal(
                    f"{fixed.get(ccxt_enums.ExchangePositionCCXTColumns.INITIAL_MARGIN.value, 0)}"),
                enums.ExchangeConstantsPositionColumns.UNREALIZED_PNL.value: constants.ZERO if is_empty else
                decimal.Decimal(
                    f"{fixed.get(ccxt_enums.ExchangePositionCCXTColumns.UNREALISED_PNL.value, 0)}"),
                enums.ExchangeConstantsPositionColumns.REALISED_PNL.value: constants.ZERO if is_empty else
                decimal.Decimal(
                    f"{fixed.get(ccxt_enums.ExchangePositionCCXTColumns.REALISED_PNL.value, 0)}"),
                enums.ExchangeConstantsPositionColumns.LIQUIDATION_PRICE.value: liquidation_price,
                enums.ExchangeConstantsPositionColumns.MARK_PRICE.value: constants.ZERO if is_empty else
                decimal.Decimal(
                    f"{fixed.get(ccxt_enums.ExchangePositionCCXTColumns.MARK_PRICE.value, 0)}"),
                enums.ExchangeConstantsPositionColumns.ENTRY_PRICE.value: constants.ZERO if is_empty else
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

    def parse_funding_rate(self, fixed, from_ticker=False, **kwargs):
        # CCXT standard funding_rate parsing logic
        fixed.update({
            enums.ExchangeConstantsFundingColumns.FUNDING_RATE.value:
                self.safe_decimal(
                    fixed, ccxt_enums.ExchangeFundingCCXTColumns.PREVIOUS_FUNDING_RATE.value, constants.NaN
                ),
            enums.ExchangeConstantsFundingColumns.LAST_FUNDING_TIME.value:
                self.get_uniformized_timestamp(
                    fixed.get(ccxt_enums.ExchangeFundingCCXTColumns.PREVIOUS_FUNDING_TIMESTAMP.value, 0)
                    or constants.ZERO
                ),
            enums.ExchangeConstantsFundingColumns.PREDICTED_FUNDING_RATE.value:
                self.safe_decimal(
                    fixed, ccxt_enums.ExchangeFundingCCXTColumns.FUNDING_RATE.value, constants.NaN
                ),
            enums.ExchangeConstantsFundingColumns.NEXT_FUNDING_TIME.value:
                self.get_uniformized_timestamp(
                    fixed.get(ccxt_enums.ExchangeFundingCCXTColumns.FUNDING_TIMESTAMP.value, 0) or constants.ZERO
                ),
        })
        return fixed

    def fix_leverage(self, raw, **kwargs):
        fixed = super().fix_leverage(raw, **kwargs)
        # CCXT standard leverage fixing logic
        return fixed

    def parse_leverage(self, fixed, **kwargs):
        # WARNING no CCXT standard leverage parsing logic
        # HAS TO BE IMPLEMENTED IN EACH EXCHANGE IMPLEMENTATION
        return {
            enums.ExchangeConstantsLeveragePropertyColumns.RAW.value: fixed,
        }

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
