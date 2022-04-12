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
import octobot_trading.signals.trading_signal as trading_signal
import octobot_trading.enums as enums
import octobot_commons.enums as commons_enums


def create_trading_signal(dict_signal):
    signal_value = dict_signal[commons_enums.CommunityFeedAttrs.VALUE.value]
    return trading_signal.TradingSignal(
        signal_value.get(enums.TradingSignalAttrs.STRATEGY.value),
        signal_value.get(enums.TradingSignalAttrs.EXCHANGE.value),
        signal_value.get(enums.TradingSignalAttrs.EXCHANGE_TYPE.value),
        signal_value.get(enums.TradingSignalAttrs.SYMBOL.value),
        signal_value.get(enums.TradingSignalAttrs.DESCRIPTION.value),
        signal_value.get(enums.TradingSignalAttrs.STATE.value),
        signal_value.get(enums.TradingSignalAttrs.ORDERS.value),
        identifier=dict_signal[commons_enums.CommunityFeedAttrs.ID.value],
        version=dict_signal[commons_enums.CommunityFeedAttrs.VERSION.value],
    )
