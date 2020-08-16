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
#  Lesser General License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
from enum import Enum

from octobot_channels.channels.channel_instances import get_chan_at_id
from octobot_commons.channels_name import OctoBotChannelsName
from octobot_commons.logging.logging_util import get_logger

from octobot_trading.api.trader import is_trader_enabled_in_config, is_trader_simulator_enabled_in_config
from octobot_trading.api.exchange import create_exchange_builder

from octobot_commons.enums import OctoBotChannelSubjects
from octobot_trading.constants import CONFIG_EXCHANGE_SANDBOXED, CONFIG_EXCHANGES, CONFIG_EXCHANGE_FUTURE, \
    CONFIG_EXCHANGE_MARGIN, CONFIG_EXCHANGE_SPOT, CONFIG_EXCHANGE_REST_ONLY
from octobot_trading.errors import TradingModeIncompatibility

OCTOBOT_CHANNEL_TRADING_CONSUMER_LOGGER_TAG = "OctoBotChannelTradingConsumer"


class OctoBotChannelTradingActions(Enum):
    """
    OctoBot Channel consumer supported actions
    """

    EXCHANGE = "exchange"


class OctoBotChannelTradingDataKeys(Enum):
    """
    OctoBot Channel consumer supported data keys
    """

    EXCHANGE_NAME = "exchange_name"
    EXCHANGE_CONFIG = "exchange_config"
    EXCHANGE_ID = "exchange_id"
    BACKTESTING = "backtesting"
    MATRIX_ID = "matrix_id"
    TENTACLES_SETUP_CONFIG = "tentacles_setup_config"


async def octobot_channel_callback(bot_id, subject, action, data) -> None:
    """
    OctoBot channel consumer callback
    :param bot_id: the callback bot id
    :param subject: the callback subject
    :param action: the callback action
    :param data: the callback data
    """
    if subject == OctoBotChannelSubjects.CREATION.value:
        await _handle_creation(bot_id, action, data)


async def _handle_creation(bot_id, action, data):
    if action == OctoBotChannelTradingActions.EXCHANGE.value:
        try:
            config = data[OctoBotChannelTradingDataKeys.EXCHANGE_CONFIG.value]
            exchange_builder = create_exchange_builder(config,
                                                       data[OctoBotChannelTradingDataKeys.EXCHANGE_NAME.value]) \
                .has_matrix(data[OctoBotChannelTradingDataKeys.MATRIX_ID.value]) \
                .use_tentacles_setup_config(data[OctoBotChannelTradingDataKeys.TENTACLES_SETUP_CONFIG.value]) \
                .set_bot_id(bot_id)
            _set_exchange_type_details(exchange_builder, config, data[OctoBotChannelTradingDataKeys.BACKTESTING.value])
            await exchange_builder.build()
            await get_chan_at_id(OctoBotChannelsName.OCTOBOT_CHANNEL.value, bot_id).get_internal_producer() \
                .send(bot_id=bot_id,
                      subject=OctoBotChannelSubjects.NOTIFICATION.value,
                      action=action,
                      data={OctoBotChannelTradingDataKeys.EXCHANGE_ID.value: exchange_builder.exchange_manager.id})
        except TradingModeIncompatibility as e:
            get_logger(OCTOBOT_CHANNEL_TRADING_CONSUMER_LOGGER_TAG).error(
                f"Error when initializing trading mode, {data[OctoBotChannelTradingDataKeys.EXCHANGE_NAME.value]} "
                f"exchange connection is closed to increase performances: {e}")
        except Exception as e:
            get_logger(OCTOBOT_CHANNEL_TRADING_CONSUMER_LOGGER_TAG).error(f"Error when creating new exchange: {e}")


def _set_exchange_type_details(exchange_builder, config, backtesting):
    # real, simulator, backtesting
    if is_trader_enabled_in_config(config):
        exchange_builder.is_real()
    elif is_trader_simulator_enabled_in_config(config):
        exchange_builder.is_simulated()
    if backtesting is not None:
        exchange_builder.is_backtesting(backtesting)
    # use exchange sandbox
    exchange_builder.is_sandboxed(
        config[CONFIG_EXCHANGES][exchange_builder.exchange_name].get(CONFIG_EXCHANGE_SANDBOXED, False)
    )
    # exchange trading type
    if config[CONFIG_EXCHANGES][exchange_builder.exchange_name].get(CONFIG_EXCHANGE_FUTURE, False):
        exchange_builder.is_future(True)
    elif config[CONFIG_EXCHANGES][exchange_builder.exchange_name].get(CONFIG_EXCHANGE_MARGIN, False):
        exchange_builder.is_margin(True)
    elif config[CONFIG_EXCHANGES][exchange_builder.exchange_name].get(CONFIG_EXCHANGE_SPOT, True):
        # Use spot trading as default trading type
        exchange_builder.is_spot_only(True)

    # rest, web socket
    if config[CONFIG_EXCHANGES][exchange_builder.exchange_name].get(CONFIG_EXCHANGE_REST_ONLY, False):
        exchange_builder.is_rest_only()
