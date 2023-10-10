#  Drakkar-Software OctoBot-Private-Tentacles
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
import asyncio
import decimal
import time

import octobot_commons.asyncio_tools as asyncio_tools
import octobot_commons.enums as common_enums
import octobot_commons.constants as commons_constants
import octobot_trading.enums as enums
import octobot_trading.api as trading_api
import octobot_trading.exchanges as exchanges
import octobot_tentacles_manager.api as tentacles_manager_api

import octobot_trading.personal_data as personal_data

import octobot_trading.util.test_tools.exchange_data as exchange_data_import


BASE_TIMEOUT = 10


async def create_test_exchange_manager(
        config: dict,
        exchange_name: str,
        is_spot_only: bool = True,
        is_margin: bool = False,
        is_future: bool = False,
        rest_only: bool = False,
        is_real: bool = True,
        is_sandboxed: bool = False,
        ignore_exchange_config: bool = True) -> exchanges.ExchangeManager:
    if ignore_exchange_config:
        # enable exchange name in config
        config[commons_constants.CONFIG_EXCHANGES][exchange_name] = {commons_constants.CONFIG_ENABLED_OPTION: True}

    builder = exchanges.create_exchange_builder_instance(config, exchange_name)
    builder.disable_trading_mode()
    builder.use_tentacles_setup_config(tentacles_manager_api.get_tentacles_setup_config())
    if is_spot_only:
        builder.is_spot_only()
    if is_margin:
        builder.is_margin()
    if is_future:
        builder.is_future()
    if rest_only:
        builder.is_rest_only()
    if is_sandboxed:
        builder.is_sandboxed(is_sandboxed)
    if is_real:
        builder.is_real()
    else:
        builder.is_simulated()
    await builder.build()
    return builder.exchange_manager


async def stop_test_exchange_manager(exchange_manager_instance: exchanges.ExchangeManager):
    trading_api.cancel_ccxt_throttle_task()
    await exchange_manager_instance.stop()
    # let updaters gracefully shutdown
    await asyncio_tools.wait_asyncio_next_cycle()


def update_symbol_market(exchange_manager, market_details: exchange_data_import.MarketDetails):
    market_details.id = exchange_manager.exchange.connector.update_symbol_details(
        market_details.details, market_details.symbol
    )


async def add_symbols_details(
        exchange_manager, symbols: list, time_frame: str, exchange_data: exchange_data_import.ExchangeData,
        history_size=1, forced_markets=None, start_time=0, end_time=0, close_price_only=False
) -> exchange_data_import.ExchangeData:
    parsed_tf = common_enums.TimeFrames(time_frame)

    async def _update_ohlcv(symbol):
        if start_time == 0:
            ohlcvs = await exchange_manager.exchange.get_symbol_prices(symbol, parsed_tf, limit=history_size)
        else:
            ohlcvs = []
            async for ohlcv in exchanges.get_historical_ohlcv(
                exchange_manager, symbol, parsed_tf, start_time * 1000, (end_time or time.time()) * 1000,
                request_retry_timeout=BASE_TIMEOUT
            ):
                ohlcvs.extend(ohlcv)
        details = exchange_data_import.MarketDetails(
            symbol=symbol,
            time_frame=time_frame,
            close=[ohlcv[common_enums.PriceIndexes.IND_PRICE_CLOSE.value] for ohlcv in ohlcvs],
            open=[ohlcv[common_enums.PriceIndexes.IND_PRICE_OPEN.value] for ohlcv in ohlcvs] if not close_price_only else [],
            high=[ohlcv[common_enums.PriceIndexes.IND_PRICE_HIGH.value] for ohlcv in ohlcvs] if not close_price_only else [],
            low=[ohlcv[common_enums.PriceIndexes.IND_PRICE_LOW.value] for ohlcv in ohlcvs] if not close_price_only else [],
            volume=[ohlcv[common_enums.PriceIndexes.IND_PRICE_VOL.value] for ohlcv in ohlcvs] if not close_price_only else [],
            time=[ohlcv[common_enums.PriceIndexes.IND_PRICE_TIME.value] for ohlcv in ohlcvs],
        )
        if not close_price_only:
            update_symbol_market(exchange_manager, details)
        exchange_data.markets.append(details)

    await exchange_manager.exchange.connector.load_symbol_markets(forced_markets=forced_markets)
    await asyncio.gather(*(_update_ohlcv(symbol) for symbol in symbols))
    return exchange_data


async def get_portfolio(exchange_manager, as_float=False) -> dict:
    balance = await exchange_manager.exchange.get_balance()
    # filter out 0 values
    return {
        asset: {key: float(val) if as_float else val for key, val in values.items()}  # use float for values
        for asset, values in balance.items()
        if any(value for value in values.values())
    }


async def get_open_orders(
    exchange_manager,
    exchange_data: exchange_data_import.ExchangeData,
    symbols: list = None
) -> list:
    open_orders = []

    async def _get_orders(symbol):
        orders = await exchange_manager.exchange.get_open_orders(symbol=symbol)
        open_orders.extend(
            personal_data.create_order_instance_from_raw(
                exchange_manager.trader, order, force_open_or_pending_creation=True
            ).to_dict()
            for order in orders
        )

    symbols = symbols or [market.symbol for market in exchange_data.markets]
    await asyncio.gather(*(_get_orders(symbol) for symbol in symbols))
    return open_orders


async def get_trades(
    exchange_manager,
    exchange_data: exchange_data_import.ExchangeData,
    symbols: list = None
) -> list:
    trades = []

    async def _get_trades(symbol):
        row_trades = await exchange_manager.exchange.get_my_recent_trades(symbol=symbol)
        trades.extend(
            personal_data.create_trade_instance_from_raw(exchange_manager.trader, raw_trade).to_dict()
            for raw_trade in row_trades
        )

    symbols = symbols or [market.symbol for market in exchange_data.markets]
    await asyncio.gather(*(_get_trades(symbol) for symbol in symbols))
    return trades


async def create_orders(exchange_manager, exchange_data: exchange_data_import.ExchangeData, orders: list) -> list:
    async def _create_order(order_dict) -> personal_data.Order:
        symbol = order_dict[enums.ExchangeConstantsOrderColumns.SYMBOL.value]
        side, order_type = personal_data.parse_order_type(order_dict)
        created_order = await exchange_manager.exchange.create_order(
            order_type,
            symbol,
            decimal.Decimal(str(order_dict[enums.ExchangeConstantsOrderColumns.AMOUNT.value])),
            price=decimal.Decimal(str(order_dict[enums.ExchangeConstantsOrderColumns.PRICE.value])),
            side=side,
            current_price=decimal.Decimal(str(exchange_data.get_price(symbol))),
            reduce_only=order_dict[enums.ExchangeConstantsOrderColumns.REDUCE_ONLY.value],
        )
        # is private, to use in tests context only
        return personal_data.create_order_instance_from_raw(
            exchange_manager.trader, created_order, force_open_or_pending_creation=True
        ) if created_order else None

    return await asyncio.gather(*(_create_order(order_dict) for order_dict in orders))
