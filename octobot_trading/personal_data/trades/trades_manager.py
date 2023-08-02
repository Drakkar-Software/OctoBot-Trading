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
import collections

import octobot_commons.logging as logging
import octobot_commons.tree as commons_tree
import octobot_commons.enums as commons_enums

import octobot_trading.enums as enums
import octobot_trading.personal_data as personal_data
import octobot_trading.personal_data.trades.trade_pnl as trade_pnl
import octobot_trading.util as util


class TradesManager(util.Initializable):
    # memory usage for 100000 trades: approx 180 Mo
    MAX_TRADES_COUNT = 100000

    def __init__(self, trader):
        super().__init__()
        self.logger = logging.get_logger(self.__class__.__name__)
        self.trader = trader
        self.trades_initialized = False
        self.trades = collections.OrderedDict()

    async def initialize_impl(self):
        await self.reload_history(False)
        self.trades_initialized = True
        if self.trader.simulate:
            # force init as there is no trade updater simulator
            for symbol in self.trader.exchange_manager.exchange_config.traded_symbol_pairs:
                self._set_initialized_event(symbol)

    async def reload_history(self, reset):
        self._reset_trades()
        await self._load_trades_history(reset)

    def upsert_trade(self, trade_id, raw_trade):
        if trade_id not in self.trades:
            created_trade = personal_data.create_trade_instance_from_raw(self.trader, raw_trade)
            if created_trade:
                if trade_id in self.trades:
                    self.logger.debug(f"Replacement of an existing trade: {self.trades[trade_id].to_dict()} "
                                      f"by {created_trade.to_dict()} on id: {trade_id}")
                self.trades[trade_id] = created_trade
                self._check_trades_size()
                return True
        return False

    def upsert_trade_instance(self, trade):
        if trade.trade_id not in self.trades:
            self.trades[trade.trade_id] = trade
            self._check_trades_size()

    def has_closing_trade_with_exchange_order_id(self, exchange_order_id) -> bool:
        for trade in self.get_trades(exchange_order_id=exchange_order_id):
            if trade.is_closing_order:
                return True
        return False

    def get_total_paid_fees(self):
        total_fees = {}
        for trade in self.trades.values():
            if trade.fee is not None:
                fee_cost = trade.fee[enums.FeePropertyColumns.COST.value]
                fee_currency = trade.fee[enums.FeePropertyColumns.CURRENCY.value]
                if fee_currency in total_fees:
                    total_fees[fee_currency] += fee_cost
                else:
                    total_fees[fee_currency] = fee_cost
            elif trade.status is not enums.OrderStatus.CANCELED:
                self.logger.warning(f"Trade without any registered fee: {trade.to_dict()}")
        return total_fees

    def get_completed_trades_pnl(self, trades=None) -> list:
        trades = trades or self.get_trades()
        trades_by_order_id = {
            trade.origin_order_id: trade
            for trade in trades
        }
        exits_by_entry_id = {}
        for trade in trades:
            if trade.status is not enums.OrderStatus.CANCELED and trade.associated_entry_ids:
                for entry_id in trade.associated_entry_ids:
                    if entry_id not in trades_by_order_id:
                        continue
                    if entry_id not in exits_by_entry_id:
                        exits_by_entry_id[entry_id] = []
                    exits_by_entry_id[entry_id].append(trade)
        return [
            trade_pnl.TradePnl(
                [trades_by_order_id[entry_id]],
                exit_trade,
            )
            for entry_id, exit_trade in exits_by_entry_id.items()
        ]

    def get_trade(self, trade_id):
        return self.trades[trade_id]

    def get_trades(self, origin_order_id=None, exchange_order_id=None):
        return [
            trade
            for trade in self.trades.values()
            if (
                (not origin_order_id or trade.origin_order_id == origin_order_id)
                and (not exchange_order_id or trade.exchange_order_id == exchange_order_id)
            )
        ]

    # private
    def _check_trades_size(self):
        if len(self.trades) > self.MAX_TRADES_COUNT:
            self._remove_oldest_trades(int(self.MAX_TRADES_COUNT / 10))

    def _reset_trades(self):
        self.trades_initialized = False
        self.trades = collections.OrderedDict()

    async def _load_trades_history(self, reset):
        if self.trader.exchange_manager.is_backtesting:
            # don't load history on backtesting
            return
        try:
            if self.trader.exchange_manager.storage_manager.trades_storage:
                for trade_dict in await self.trader.exchange_manager.storage_manager.trades_storage.get_history():
                    self.upsert_trade_instance(personal_data.Trade.from_dict(self.trader, trade_dict))
                if reset:
                    # reset uploaded trades history
                    await self.trader.exchange_manager.storage_manager.trades_storage.trigger_debounced_update_auth_data(
                        True
                    )
        except Exception as err:
            self.logger.exception(err, True, f"Error when loading local trade history {err}")

    def _remove_oldest_trades(self, nb_to_remove):
        for _ in range(nb_to_remove):
            self.trades.popitem(last=False)

    def _set_initialized_event(self, symbol):
        # set init in updater as it's the only place we know if we fetched trades or not regardless of trades existence
        commons_tree.EventProvider.instance().trigger_event(
            self.trader.exchange_manager.bot_id, commons_tree.get_exchange_path(
                self.trader.exchange_manager.exchange_name,
                commons_enums.InitializationEventExchangeTopics.TRADES.value
            )
        )

    def clear(self):
        for trade in self.trades.values():
            trade.clear()
        self._reset_trades()
