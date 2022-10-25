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
#  License along with this library
import octobot_commons.enums as commons_enums
import octobot_commons.constants as commons_constants
import octobot_commons.databases as commons_databases

import octobot_trading.storage.abstract_storage as abstract_storage


class PortfolioStorage(abstract_storage.AbstractStorage):
    IS_LIVE_CONSUMER = False
    IS_HISTORICAL = False

    async def save_historical_portfolio_value(self, metadata, historical_portfolio_value):
        if not self.enabled:
            return
        portfolio_db = self.get_db()
        # replace the whole table to ensure consistency
        await portfolio_db.upsert(commons_enums.RunDatabases.METADATA.value, metadata, None, uuid=1)
        await portfolio_db.replace_all(
            commons_enums.RunDatabases.HISTORICAL_PORTFOLIO_VALUE.value,
            historical_portfolio_value,
            cache=False
        )
        if not self.exchange_manager.is_backtesting:
            # in live move, flush database as soon as an update is provided
            await portfolio_db.flush()

    def get_db(self):
        return commons_databases.RunDatabasesProvider.instance().get_historical_portfolio_value_db(
            self.exchange_manager.bot_id,
            self.exchange_manager.exchange_name,
            self.get_portfolio_type_suffix()
        )

    def get_portfolio_type_suffix(self):
        suffix = ""
        if self.exchange_manager.is_future:
            suffix = f"{suffix}_{commons_constants.CONFIG_EXCHANGE_FUTURE}"
        elif self.exchange_manager.is_margin:
            suffix = f"{suffix}_{commons_constants.CONFIG_EXCHANGE_MARGIN}"
        else:
            suffix = f"{suffix}_{commons_constants.CONFIG_EXCHANGE_SPOT}"
        if self.exchange_manager.is_sandboxed:
            suffix = f"{suffix}_{commons_constants.CONFIG_EXCHANGE_SANDBOXED}"
        if self.exchange_manager.is_trader_simulated:
            suffix = f"{suffix}_{commons_constants.CONFIG_SIMULATOR}"
        return suffix
