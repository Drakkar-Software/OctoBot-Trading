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
import octobot_commons.databases as commons_databases
import octobot_commons.tree as commons_tree

import octobot_trading.storage.abstract_storage as abstract_storage
import octobot_trading.storage.util as storage_util
import octobot_trading.personal_data.portfolios.history as portfolio_history


class PortfolioStorage(abstract_storage.AbstractStorage):
    IS_LIVE_CONSUMER = False
    IS_HISTORICAL = True
    PRICE_INIT_TIMEOUT = 30
    HISTORY_TABLE = commons_enums.RunDatabases.HISTORICAL_PORTFOLIO_VALUE.value

    @abstract_storage.AbstractStorage.hard_reset_and_retry_if_necessary
    async def store_history(self, reset=False):
        if not self.enabled:
            return
        portfolio_db = self.get_db()
        hist_portfolio_values_manager = self.exchange_manager.exchange_personal_data.\
            portfolio_manager.historical_portfolio_value_manager
        metadata = hist_portfolio_values_manager.get_metadata()
        # replace the whole table to ensure consistency
        history = hist_portfolio_values_manager.get_dict_historical_values()
        existing_history = await portfolio_db.all(self.HISTORY_TABLE)
        self._to_update_auth_data_ids_buffer.update(
            (
                history_val[portfolio_history.HistoricalAssetValue.TIMESTAMP_KEY]
                for history_val in history
                if history_val not in existing_history
            )
        )
        await portfolio_db.upsert(commons_enums.RunDatabases.METADATA.value, metadata, None, uuid=1)
        await portfolio_db.replace_all(
            self.HISTORY_TABLE,
            history,
            cache=False
        )
        await self.trigger_debounced_flush()
        await self.trigger_debounced_update_auth_data(reset)

    async def _update_auth_data(self, reset):
        hist_portfolio_values_manager = self.exchange_manager.exchange_personal_data. \
            portfolio_manager.historical_portfolio_value_manager
        authenticator = authentication.Authenticator.instance()
        full_history = hist_portfolio_values_manager.get_dict_historical_values()
        history = [
            history_val
            for history_val in full_history
            if history_val[portfolio_history.HistoricalAssetValue.TIMESTAMP_KEY] in self._to_update_auth_data_ids_buffer
        ]
        if full_history and authenticator.is_initialized():
            initializing_prices = hist_portfolio_values_manager.portfolio_manager.portfolio_value_holder.\
                value_converter.initializing_symbol_prices_pairs
            if initializing_prices:
                for symbol in initializing_prices:
                    await commons_tree.EventProvider.instance().wait_for_event(
                        self.exchange_manager.bot_id,
                        commons_tree.get_exchange_path(
                            self.exchange_manager.exchange_name,
                            commons_enums.InitializationEventExchangeTopics.PRICE.value,
                            symbol=symbol,
                        ),
                        self.PRICE_INIT_TIMEOUT
                    )
            # skip portfolio history on simulated trading
            histories = {} if self.exchange_manager.is_trader_simulated else {
                history_val[portfolio_history.HistoricalAssetValue.TIMESTAMP_KEY]:
                    history_val[portfolio_history.HistoricalAssetValue.VALUES_KEY]
                for history_val in history
            }
            await authenticator.update_portfolio(
                full_history[-1][portfolio_history.HistoricalAssetValue.VALUES_KEY],
                full_history[0][portfolio_history.HistoricalAssetValue.VALUES_KEY],
                float(hist_portfolio_values_manager.portfolio_manager.portfolio_profitability.profitability_percent),
                hist_portfolio_values_manager.portfolio_manager.reference_market,
                hist_portfolio_values_manager.ending_portfolio,
                histories,
                hist_portfolio_values_manager.portfolio_manager.portfolio_value_holder.current_crypto_currencies_values,
                reset
            )
            self._to_update_auth_data_ids_buffer.clear()

    def get_db(self):
        return self._get_db()

    def _get_db(self):
        return commons_databases.RunDatabasesProvider.instance().get_historical_portfolio_value_db(
            self.exchange_manager.bot_id,
            storage_util.get_account_type_suffix_from_exchange_manager(self.exchange_manager),
            self.exchange_manager.exchange_name,
        )
