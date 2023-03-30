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
import copy
import decimal
import time

import octobot_commons.channels_name as channels_name
import octobot_commons.enums as commons_enums
import octobot_commons.databases as commons_databases
import octobot_commons.logging as commons_logging

import octobot_trading.enums as enums
import octobot_trading.constants as constants
import octobot_trading.storage.abstract_storage as abstract_storage
import octobot_trading.storage.util as storage_util


class OrdersStorage(abstract_storage.AbstractStorage):
    LIVE_CHANNEL = channels_name.OctoBotTradingChannelsName.ORDERS_CHANNEL.value
    HISTORY_TABLE = commons_enums.DBTables.ORDERS.value
    HISTORICAL_OPEN_ORDERS_TABLE = commons_enums.DBTables.HISTORICAL_ORDERS_UPDATES.value
    IS_HISTORICAL = False
    ENABLE_HISTORICAL_ORDER_UPDATES_STORAGE = constants.ENABLE_HISTORICAL_ORDERS_UPDATES_STORAGE

    def __init__(self, exchange_manager, use_live_consumer_in_backtesting=None, is_historical=None):
        super().__init__(exchange_manager, plot_settings=None,
                         use_live_consumer_in_backtesting=use_live_consumer_in_backtesting, is_historical=is_historical)
        self.startup_orders = {}

    def should_register_live_consumer(self):
        # live orders should only be stored on real trading
        return self.should_store_date()

    def should_store_date(self):
        return not self.exchange_manager.is_trader_simulated \
            and not self.exchange_manager.is_backtesting

    async def on_start(self):
        await self._load_startup_orders()

    async def _live_callback(
        self,
        exchange: str,
        exchange_id: str,
        cryptocurrency: str,
        symbol: str,
        order: dict,
        update_type: str,
        is_from_bot: bool,
    ):
        # only store the current snapshot of open orders when order updates are received
        await self._update_history()
        if self.ENABLE_HISTORICAL_ORDER_UPDATES_STORAGE:
            await self._add_historical_open_orders(order, update_type)
        await self.trigger_debounced_flush()

    async def _update_history(self):
        await self._get_db().replace_all(
            self.HISTORY_TABLE,
            [
                _format_order(order, self.exchange_manager)
                for order in self.exchange_manager.exchange_personal_data.orders_manager.get_open_orders()
            ],
            cache=False,
        )

    async def _add_historical_open_orders(self, order_dict: dict, update_type: str):
        update_time = time.time()
        await self._get_db().log(
            self.HISTORICAL_OPEN_ORDERS_TABLE,
            _format_order_update(self.exchange_manager, order_dict, update_type, update_time),
            cache=False,
        )

    async def _store_history(self):
        await self._update_history()
        await self._get_db().flush()

    def _get_db(self):
        return commons_databases.RunDatabasesProvider.instance().get_orders_db(
            self.exchange_manager.bot_id,
            storage_util.get_account_type_suffix_from_exchange_manager(self.exchange_manager),
            self.exchange_manager.exchange_name,
        )

    async def get_historical_orders_updates(self):
        return copy.deepcopy(await self._get_db().all(self.HISTORICAL_OPEN_ORDERS_TABLE))

    async def get_startup_order_details(self, order_id):
        return self.startup_orders.get(order_id, None)

    async def _load_startup_orders(self):
        if self.should_store_date():
            self.startup_orders = {
                order[OrdersStorage.ORIGIN_VALUE_KEY][enums.ExchangeConstantsOrderColumns.ID.value]:
                    self._from_order_document(order)
                for order in copy.deepcopy(await self._get_db().all(self.HISTORY_TABLE))
                if order    # skip empty order details (error when serializing)
            }
        else:
            self.startup_orders = {}

    def get_startup_self_managed_orders_details_from_group(self, group_id):
        return [
            order
            for order in self.startup_orders.values()
            if order.get(enums.StoredOrdersAttr.GROUP.value, {}).get(enums.StoredOrdersAttr.GROUP_ID.value, None)
            == group_id
            and order.get(OrdersStorage.ORIGIN_VALUE_KEY, {})
            .get(enums.ExchangeConstantsOrderColumns.SELF_MANAGED.value, False)
        ]

    def _from_order_document(self, order_document):
        order_dict = dict(order_document)
        try:
            origin_val = order_dict[OrdersStorage.ORIGIN_VALUE_KEY]
            origin_val[enums.ExchangeConstantsOrderColumns.AMOUNT.value] = \
                decimal.Decimal(str(origin_val[enums.ExchangeConstantsOrderColumns.AMOUNT.value]))
            origin_val[enums.ExchangeConstantsOrderColumns.COST.value] = \
                decimal.Decimal(str(origin_val[enums.ExchangeConstantsOrderColumns.COST.value]))
            origin_val[enums.ExchangeConstantsOrderColumns.FILLED.value] = \
                decimal.Decimal(str(origin_val[enums.ExchangeConstantsOrderColumns.FILLED.value]))
            if origin_val[enums.ExchangeConstantsOrderColumns.FEE.value] and \
                    enums.FeePropertyColumns.COST.value in origin_val[enums.ExchangeConstantsOrderColumns.FEE.value]:
                origin_val[enums.ExchangeConstantsOrderColumns.FEE.value][enums.FeePropertyColumns.COST.value] = \
                    decimal.Decimal(str(
                        origin_val[enums.ExchangeConstantsOrderColumns.FEE.value][enums.FeePropertyColumns.COST.value]
                    ))
        except Exception as err:
            commons_logging.get_logger(OrdersStorage.__name__).exception(
                err, True, f"Error when reading: {err} order: {order_document}"
            )
        return order_dict

    @classmethod
    async def clear_database_history(cls, database, flush=True):
        await super().clear_database_history(database, flush=False)
        if cls.ENABLE_HISTORICAL_ORDER_UPDATES_STORAGE:
            await database.delete(cls.HISTORICAL_OPEN_ORDERS_TABLE, None)
        if flush:
            await database.flush()


def _get_group_dict(order):
    if not order.order_group:
        return {}
    try:
        return {
            enums.StoredOrdersAttr.GROUP_ID.value: order.order_group.name,
            enums.StoredOrdersAttr.GROUP_TYPE.value: order.order_group.__class__.__name__,
        }
    except KeyError:
        return {}


def _get_chained_orders(order, exchange_manager):
    if not order.chained_orders:
        return []
    return [
        _format_order(chained_order, exchange_manager)
        for chained_order in order.chained_orders
    ]


def _format_order(order, exchange_manager):
    try:
        return {
            OrdersStorage.ORIGIN_VALUE_KEY: OrdersStorage.sanitize_for_storage(order.to_dict()),
            enums.StoredOrdersAttr.EXCHANGE_CREATION_PARAMS.value:
                OrdersStorage.sanitize_for_storage(order.exchange_creation_params),
            enums.StoredOrdersAttr.TRADER_CREATION_KWARGS.value:
                OrdersStorage.sanitize_for_storage(order.trader_creation_kwargs),
            enums.StoredOrdersAttr.SHARED_SIGNAL_ORDER_ID.value: order.shared_signal_order_id,
            enums.StoredOrdersAttr.HAS_BEEN_BUNDLED.value: order.has_been_bundled,
            enums.StoredOrdersAttr.ENTRIES.value: order.associated_entry_ids,
            enums.StoredOrdersAttr.GROUP.value: _get_group_dict(order),
            enums.StoredOrdersAttr.CHAINED_ORDERS.value:
                _get_chained_orders(order, exchange_manager),
        }
    except Exception as err:
        commons_logging.get_logger(OrdersStorage.__name__).exception(err, True, f"Error when formatting order: {err}")
    return {}


def _format_order_update(exchange_manager, order_dict, update_type, update_time):
    order_id = order_dict[enums.ExchangeConstantsOrderColumns.ID.value]
    status = order_dict[enums.ExchangeConstantsOrderColumns.STATUS.value]
    order_update = {
        enums.StoredOrdersAttr.ORDER_ID.value: order_id,
        enums.StoredOrdersAttr.ORDER_STATUS.value: status,
        enums.StoredOrdersAttr.UPDATE_TIME.value: update_time,
        enums.StoredOrdersAttr.UPDATE_TYPE.value: update_type,
    }
    details = None
    try:
        details = _format_order(
            exchange_manager.exchange_personal_data.orders_manager.get_order(
                order_dict[enums.ExchangeConstantsOrderColumns.ID.value]
            ),
            exchange_manager
        )
    except KeyError:
        if status == enums.OrderStatus.OPEN.value:
            # ensure order details are present in open orders
            details = {
                OrdersStorage.ORIGIN_VALUE_KEY: OrdersStorage.sanitize_for_storage(order_dict),
            }
    order_update[enums.StoredOrdersAttr.ORDER_DETAILS.value] = details
    return order_update

