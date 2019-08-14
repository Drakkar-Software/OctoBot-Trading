import pytest
from octobot_commons.constants import CONFIG_TIME_FRAME, CONFIG_ENABLED_OPTION
from octobot_commons.enums import TimeFrames

from octobot_trading.cli.cli_tools import create_new_exchange, start_cli_exchange, start_exchange
from octobot_trading.constants import CONFIG_TRADING, CONFIG_TRADER, CONFIG_SIMULATOR

config = {
    "crypto-currencies": {
        "Bitcoin": {
            "pairs": [
                "BTC/USDT"
            ]
        }
    },
    "exchanges": {
        "binance": {}
    },
    CONFIG_TRADER: {
        CONFIG_ENABLED_OPTION: True
    },
    CONFIG_SIMULATOR: {
        CONFIG_ENABLED_OPTION: True,
        "fees": {
            "maker": 0.1,
            "taker": 0.1
        },
        "starting-portfolio": {
            "BTC": 10,
            "ETH": 50,
            "USDT": 1000
        }
    },
    CONFIG_TRADING: {
        "multi-session-profitability": False,
        "reference-market": "BTC",
        "risk": 0.5
    },
    CONFIG_TIME_FRAME: {
        TimeFrames.ONE_MINUTE,
        TimeFrames.ONE_HOUR
    }
}


@pytest.mark.asyncio
async def test_create_exchange():
    exchange_name = "binance"
    exchange_factory = create_new_exchange(config, exchange_name,
                                           is_simulated=True,
                                           is_rest_only=True,
                                           is_backtesting=False,
                                           is_sandboxed=False)
    await start_exchange(exchange_factory)
