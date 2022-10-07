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


async def clear_trades_storage_history(exchange_manager, flush=True):
    await exchange_manager.storage_manager.trades_storage.clear_history(flush=flush)


async def clear_orders_storage_history(exchange_manager, flush=True):
    await exchange_manager.storage_manager.orders_storage.clear_history(flush=flush)


async def clear_transactions_storage_history(exchange_manager, flush=True):
    await exchange_manager.storage_manager.transactions_storage.clear_history(flush=flush)


async def clear_portfolio_storage_history(exchange_manager, flush=True):
    await exchange_manager.storage_manager.portfolio_storage.clear_history(flush=flush)


async def clear_candles_storage_history(exchange_manager, flush=True):
    await exchange_manager.storage_manager.candles_storage.clear_history(flush=flush)
