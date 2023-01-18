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
import octobot_commons.authentication as authentication
import octobot_commons.constants as commons_constants
import octobot_commons.databases as commons_databases
import octobot_commons.tree as commons_tree

import octobot_trading.storage.abstract_storage as abstract_storage
import octobot_trading.personal_data.portfolios.history as portfolio_history


class PortfolioStorage(abstract_storage.AbstractStorage):
    IS_LIVE_CONSUMER = False
    IS_HISTORICAL = True
    PRICE_INIT_TIMEOUT = 30

    async def store_history(self):
        if not self.enabled:
            return
        portfolio_db = self.get_db()
        hist_portfolio_values_manager = self.exchange_manager.exchange_personal_data.\
            portfolio_manager.historical_portfolio_value_manager
        metadata = hist_portfolio_values_manager.get_metadata()
        # replace the whole table to ensure consistency
        history = hist_portfolio_values_manager.get_dict_historical_values()
        await portfolio_db.upsert(commons_enums.RunDatabases.METADATA.value, metadata, None, uuid=1)
        await portfolio_db.replace_all(
            commons_enums.RunDatabases.HISTORICAL_PORTFOLIO_VALUE.value,
            history,
            cache=False
        )
        await portfolio_db.flush()
        await self.trigger_debounced_update_auth_data()

    async def _update_auth_data(self):
        hist_portfolio_values_manager = self.exchange_manager.exchange_personal_data. \
            portfolio_manager.historical_portfolio_value_manager
        authenticator = authentication.Authenticator.instance()
        history = hist_portfolio_values_manager.get_dict_historical_values()
        if history and authenticator.is_initialized():
            if hist_portfolio_values_manager.portfolio_manager.portfolio_value_holder.initializing_symbol_prices_pairs:
                for symbol in hist_portfolio_values_manager.portfolio_manager.portfolio_value_holder.initializing_symbol_prices_pairs:
                    await commons_tree.EventProvider.instance().wait_for_event(
                        self.exchange_manager.bot_id,
                        commons_tree.get_exchange_path(
                            self.exchange_manager.exchange_name,
                            commons_enums.InitializationEventExchangeTopics.PRICE.value,
                            symbol=symbol,
                        ),
                        self.PRICE_INIT_TIMEOUT
                    )
            await authenticator.update_portfolio(
                history[-1][portfolio_history.HistoricalAssetValue.VALUES_KEY],
                history[0][portfolio_history.HistoricalAssetValue.VALUES_KEY],
                hist_portfolio_values_manager.portfolio_manager.reference_market,
                hist_portfolio_values_manager.ending_portfolio,
                {
                    history_val[portfolio_history.HistoricalAssetValue.TIMESTAMP_KEY]: history_val[portfolio_history.HistoricalAssetValue.VALUES_KEY]
                    for history_val in history
                },
                hist_portfolio_values_manager.portfolio_manager.portfolio_value_holder.current_crypto_currencies_values
            )

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
