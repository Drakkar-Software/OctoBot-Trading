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

import octobot_trading.errors as errors
import octobot_trading.enums as enums
import octobot_commons.logging as logging
import octobot_commons.constants as commons_constants


def _adapter(func):
    def adapter_wrapper(*args, **kwargs):
        try:
            if args[1] is None:
                # element to adapt is None, no need to go any further
                return None
            adapted = func(*args, **kwargs)
            # add any other common adapter function logic here
            return adapted
        except Exception as err:
            raise errors.UnexpectedAdapterError(
                f"Unexpected error when adapting exchange data: {err} (data: {args[1]})"
            ) from err
    return adapter_wrapper


class AbstractAdapter:
    def __init__(self, connector):
        self.logger = logging.get_logger(self.__class__.__name__)
        self.connector = connector

    @_adapter
    def adapt_orders(self, raw, cancelled_only=False, **kwargs):
        return [
            order
            for order in (
                self.adapt_order(element, **kwargs)
                for element in raw
            )
            if not cancelled_only or not order or (
                order[enums.ExchangeConstantsOrderColumns.STATUS.value] == enums.OrderStatus.CANCELED.value
            )
        ]

    @_adapter
    def adapt_order(self, raw, **kwargs):
        fixed = self.fix_order(raw, **kwargs)
        return self.parse_order(fixed, **kwargs)

    @_adapter
    def adapt_ohlcv(self, raw, **kwargs):
        fixed = self.fix_ohlcv(raw, **kwargs)
        return self.parse_ohlcv(fixed, **kwargs)

    @_adapter
    def adapt_kline(self, raw, **kwargs):
        fixed = self.fix_kline(raw, **kwargs)
        return self.parse_kline(fixed, **kwargs)

    @_adapter
    def adapt_ticker(self, raw, **kwargs):
        fixed = self.fix_ticker(raw, **kwargs)
        return self.parse_ticker(fixed, **kwargs)

    @_adapter
    def adapt_ticker_from_kline(self, raw, symbol, **kwargs):
        fixed = self.create_ticker_from_kline(raw, symbol, **kwargs)
        return self.parse_ticker(fixed, **kwargs)

    @_adapter
    def adapt_balance(self, raw, **kwargs):
        fixed = self.fix_balance(raw, **kwargs)
        return self.parse_balance(fixed, **kwargs)

    @_adapter
    def adapt_order_book(self, raw, **kwargs):
        fixed = self.fix_order_book(raw, **kwargs)
        return self.parse_order_book(fixed, **kwargs)

    @_adapter
    def adapt_public_recent_trades(self, raw, **kwargs):
        fixed = self.fix_public_recent_trades(raw, **kwargs)
        return self.parse_public_recent_trades(fixed, **kwargs)

    @_adapter
    def adapt_trades(self, raw, **kwargs):
        fixed = self.fix_trades(raw, **kwargs)
        return self.parse_trades(fixed, **kwargs)

    @_adapter
    def adapt_position(self, raw, **kwargs):
        fixed = self.fix_position(raw, **kwargs)
        return self.parse_position(fixed, **kwargs)

    @_adapter
    def adapt_funding_rate(self, raw, **kwargs):
        fixed = self.fix_funding_rate(raw, **kwargs)
        return self.parse_funding_rate(fixed, **kwargs)

    @_adapter
    def adapt_leverage_tiers(self, raw, **kwargs):
        fixed = self.fix_leverage_tiers(raw, **kwargs)
        return self.parse_leverage_tiers(fixed, **kwargs) 

    @_adapter
    def adapt_leverage(self, raw, **kwargs):
        fixed = self.fix_leverage(raw, **kwargs)
        return self.parse_leverage(fixed, **kwargs)

    @_adapter
    def adapt_funding_rate_history(self, raw, **kwargs):
        fixed = self.fix_funding_rate_history(raw, **kwargs)
        return self.parse_funding_rate_history(fixed, **kwargs)

    @_adapter
    def adapt_mark_price(self, raw, **kwargs):
        fixed = self.fix_mark_price(raw, **kwargs)
        return self.parse_mark_price(fixed, **kwargs)

    @_adapter
    def adapt_market_status(self, raw, remove_price_limits=False, **kwargs):
        fixed = self.fix_market_status(raw, remove_price_limits=remove_price_limits, **kwargs)
        return self.parse_market_status(fixed, remove_price_limits=remove_price_limits, **kwargs)

    def get_uniformized_timestamp(self, timestamp):
        # override if the exchange time is not a second timestamp or millisecond
        if timestamp is not None and timestamp > 16728292300:  # Friday 5 February 2500 11:51:40
            return timestamp / commons_constants.MSECONDS_TO_SECONDS
        return timestamp

    def safe_decimal(self, container, key, default):
        if (val := container.get(key, default)) is not None:
            return decimal.Decimal(str(val))
        return default

    def fix_order(self, raw, **kwargs):
        # id is reserved for octobot managed id. store exchange id in EXCHANGE_ID
        raw[enums.ExchangeConstantsOrderColumns.EXCHANGE_ID.value] = \
            raw.pop(enums.ExchangeConstantsOrderColumns.ID.value, None)
        # add generic logic if necessary
        return raw

    def parse_order(self, fixed, **kwargs):
        raise NotImplementedError("parse_order is not implemented")

    def fix_ohlcv(self, raw, **kwargs):
        # add generic logic if necessary
        return raw

    def parse_ohlcv(self, fixed, **kwargs):
        raise NotImplementedError("parse_ohlcv is not implemented")

    def fix_kline(self, raw, **kwargs):
        # add generic logic if necessary
        return raw

    def parse_kline(self, fixed, **kwargs):
        raise NotImplementedError("parse_kline is not implemented")

    def fix_ticker(self, raw, **kwargs):
        # add generic logic if necessary
        return raw

    def parse_ticker(self, fixed, **kwargs):
        raise NotImplementedError("parse_ticker is not implemented")

    def create_ticker_from_kline(self, kline, symbol, **kwargs):
        raise NotImplementedError("create_ticker_from_kline is not implemented")

    def fix_balance(self, raw, **kwargs):
        # add generic logic if necessary
        return raw

    def parse_balance(self, fixed, **kwargs):
        raise NotImplementedError("parse_balance is not implemented")

    def fix_order_book(self, raw, **kwargs):
        # add generic logic if necessary
        return raw

    def parse_order_book(self, fixed, **kwargs):
        raise NotImplementedError("parse_order_book is not implemented")

    def fix_public_recent_trades(self, raw, **kwargs):
        # add generic logic if necessary
        return raw

    def parse_public_recent_trades(self, fixed, **kwargs):
        raise NotImplementedError("parse_public_recent_trades is not implemented")

    def fix_trades(self, raw, **kwargs):
        for trade in raw:
            # id is reserved for octobot managed id. store exchange trade id in EXCHANGE_TRADE_ID
            trade[enums.ExchangeConstantsOrderColumns.EXCHANGE_TRADE_ID.value] = \
                trade.pop(enums.ExchangeConstantsOrderColumns.ID.value, None)
            # add generic logic if necessary
        return raw

    def parse_trades(self, fixed, **kwargs):
        raise NotImplementedError("parse_trades is not implemented")

    def fix_position(self, raw, **kwargs):
        # add generic logic if necessary
        return raw

    def parse_position(self, fixed, **kwargs):
        raise NotImplementedError("parse_position is not implemented")

    def fix_funding_rate(self, raw, **kwargs):
        # add generic logic if necessary
        return raw

    def parse_funding_rate(self, fixed, **kwargs):
        raise NotImplementedError("parse_funding_rate is not implemented")

    def fix_leverage(self, raw, **kwargs):
        # add generic logic if necessary
        return raw

    def parse_leverage(self, fixed, **kwargs):
        raise NotImplementedError("parse_leverage is not implemented")

    def fix_funding_rate_history(self, raw, **kwargs):
        # add generic logic if necessary
        return raw

    def parse_funding_rate_history(self, fixed, **kwargs):
        raise NotImplementedError("parse_funding_rate_history is not implemented")

    def fix_leverage_tiers(self, raw, **kwargs):
        # add generic logic if necessary
        return raw

    def parse_leverage_tiers(self, fixed, **kwargs):
        raise NotImplementedError("parse_leverage_tiers is not implemented")

    def fix_mark_price(self, raw, **kwargs):
        # add generic logic if necessary
        return raw

    def parse_mark_price(self, fixed, **kwargs):
        raise NotImplementedError("parse_mark_price is not implemented")

    def fix_market_status(self, raw, remove_price_limits=False, **kwargs):
        # add generic logic if necessary
        return raw

    def parse_market_status(self, fixed, remove_price_limits=False, **kwargs):
        raise NotImplementedError("parse_market_status is not implemented")
