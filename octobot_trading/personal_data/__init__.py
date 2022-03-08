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

import octobot_trading.enums

from octobot_trading.personal_data import state
from octobot_trading.personal_data.state import (
    State,
)
from octobot_trading.personal_data import orders
from octobot_trading.personal_data.orders import (
    Order,
    parse_order_type,
    is_valid,
    get_min_max_amounts,
    check_cost,
    get_max_order_quantity_for_price,
    total_fees_from_order_dict,
    get_fees_for_currency,
    parse_raw_fees,
    parse_order_status,
    parse_is_cancelled,
    get_up_to_date_price,
    get_pnl_transaction_source_from_order,
    is_stop_order,
    create_as_chained_order,
    get_pre_order_data,
    OrderState,
    OrderGroup,
    BalancedTakeProfitAndStopOrderGroup,
    OneCancelsTheOtherOrderGroup,
    OrdersUpdater,
    adapt_price,
    decimal_adapt_price,
    adapt_quantity,
    decimal_adapt_quantity,
    trunc_with_n_decimal_digits,
    decimal_trunc_with_n_decimal_digits,
    adapt_order_quantity_because_quantity,
    decimal_adapt_order_quantity_because_quantity,
    adapt_order_quantity_because_price,
    decimal_adapt_order_quantity_because_price,
    split_orders,
    decimal_split_orders,
    check_and_adapt_order_details_if_necessary,
    decimal_check_and_adapt_order_details_if_necessary,
    add_dusts_to_quantity_if_necessary,
    decimal_add_dusts_to_quantity_if_necessary,
    create_order_from_raw,
    create_order_instance_from_raw,
    create_order_from_type,
    create_order_instance,
    OrdersProducer,
    OrdersChannel,
    OrdersManager,
    OrdersUpdaterSimulator,
    CloseOrderState,
    CancelOrderState,
    OpenOrderState,
    create_order_state,
    FillOrderState,
    UnknownOrder,
    MarketOrder,
    SellMarketOrder,
    BuyMarketOrder,
    BuyLimitOrder,
    SellLimitOrder,
    LimitOrder,
    TakeProfitOrder,
    StopLossOrder,
    StopLossLimitOrder,
    TakeProfitLimitOrder,
    TrailingStopOrder,
    TrailingStopLimitOrder,
)
from octobot_trading.personal_data import portfolios
from octobot_trading.personal_data.portfolios import (
    BalanceUpdaterSimulator,
    BalanceProfitabilityUpdaterSimulator,
    create_portfolio_from_exchange_manager,
    BalanceUpdater,
    BalanceProfitabilityUpdater,
    PortfolioProfitability,
    Portfolio,
    BalanceProducer,
    BalanceChannel,
    BalanceProfitabilityProducer,
    BalanceProfitabilityChannel,
    SubPortfolio,
    PortfolioManager,
    PortfolioValueHolder,
    FuturePortfolio,
    MarginPortfolio,
    SpotPortfolio,
    Asset,
    FutureAsset,
    MarginAsset,
    SpotAsset,
    parse_decimal_portfolio,
    parse_decimal_config_portfolio,
    portfolio_to_float,
)
from octobot_trading.personal_data import positions
from octobot_trading.personal_data.positions import (
    PositionState,
    PositionsProducer,
    PositionsChannel,
    PositionsUpdaterSimulator,
    Position,
    LinearPosition,
    InversePosition,
    PositionsUpdater,
    PositionsManager,
    create_position_instance_from_raw,
    create_position_from_type,
    create_symbol_position,
    parse_position_status,
    LiquidatePositionState,
    OpenPositionState,
    create_position_state,
)
from octobot_trading.personal_data import trades
from octobot_trading.personal_data.trades import (
    TradesManager,
    TradesProducer,
    TradesChannel,
    create_trade_instance_from_raw,
    create_trade_from_order,
    create_trade_instance,
    TradesUpdater,
    Trade,
    compute_win_rate,
)
from octobot_trading.personal_data import transactions
from octobot_trading.personal_data.transactions import (
    TransactionsManager,
    Transaction,
    BlockchainTransaction,
    FeeTransaction,
    RealisedPnlTransaction,
    TransferTransaction,
    create_blockchain_transaction,
    create_realised_pnl_transaction,
    create_fee_transaction,
    create_transfer_transaction,
)
from octobot_trading.personal_data import exchange_personal_data
from octobot_trading.personal_data.exchange_personal_data import (
    ExchangePersonalData,
)

AUTHENTICATED_UPDATER_PRODUCERS = [
    BalanceUpdater,
    OrdersUpdater,
    TradesUpdater,
    PositionsUpdater,
    BalanceProfitabilityUpdater
]
AUTHENTICATED_UPDATER_SIMULATOR_PRODUCERS = [
    OrdersUpdaterSimulator,
    BalanceProfitabilityUpdater,
    PositionsUpdaterSimulator
]

TraderOrderTypeClasses = {
    octobot_trading.enums.TraderOrderType.BUY_MARKET: BuyMarketOrder,
    octobot_trading.enums.TraderOrderType.BUY_LIMIT: BuyLimitOrder,
    octobot_trading.enums.TraderOrderType.TAKE_PROFIT: TakeProfitOrder,
    octobot_trading.enums.TraderOrderType.TAKE_PROFIT_LIMIT: TakeProfitLimitOrder,
    octobot_trading.enums.TraderOrderType.TRAILING_STOP: TrailingStopOrder,
    octobot_trading.enums.TraderOrderType.TRAILING_STOP_LIMIT: TrailingStopLimitOrder,
    octobot_trading.enums.TraderOrderType.STOP_LOSS: StopLossOrder,
    octobot_trading.enums.TraderOrderType.STOP_LOSS_LIMIT: StopLossLimitOrder,
    octobot_trading.enums.TraderOrderType.SELL_MARKET: SellMarketOrder,
    octobot_trading.enums.TraderOrderType.SELL_LIMIT: SellLimitOrder,
    octobot_trading.enums.TraderOrderType.UNKNOWN: UnknownOrder,
}

TraderPositionTypeClasses = {
    octobot_trading.enums.FutureContractType.LINEAR_PERPETUAL: LinearPosition,
    octobot_trading.enums.FutureContractType.INVERSE_PERPETUAL: InversePosition,
    octobot_trading.enums.FutureContractType.LINEAR_EXPIRABLE: LinearPosition,
    octobot_trading.enums.FutureContractType.INVERSE_EXPIRABLE: InversePosition,
}

__all__ = [
    "State",
    "Order",
    "parse_order_type",
    "is_valid",
    "get_min_max_amounts",
    "check_cost",
    "get_max_order_quantity_for_price",
    "total_fees_from_order_dict",
    "get_fees_for_currency",
    "parse_raw_fees",
    "parse_order_status",
    "parse_is_cancelled",
    "get_up_to_date_price",
    "get_pnl_transaction_source_from_order",
    "is_stop_order",
    "create_as_chained_order",
    "get_pre_order_data",
    "OrderState",
    "OrderGroup",
    "BalancedTakeProfitAndStopOrderGroup",
    "OneCancelsTheOtherOrderGroup",
    "OrdersUpdater",
    "adapt_price",
    "decimal_adapt_price",
    "adapt_quantity",
    "decimal_adapt_quantity",
    "trunc_with_n_decimal_digits",
    "decimal_trunc_with_n_decimal_digits",
    "adapt_order_quantity_because_quantity",
    "decimal_adapt_order_quantity_because_quantity",
    "adapt_order_quantity_because_price",
    "decimal_adapt_order_quantity_because_price",
    "split_orders",
    "decimal_split_orders",
    "check_and_adapt_order_details_if_necessary",
    "decimal_check_and_adapt_order_details_if_necessary",
    "add_dusts_to_quantity_if_necessary",
    "decimal_add_dusts_to_quantity_if_necessary",
    "create_order_from_raw",
    "create_order_instance_from_raw",
    "create_order_from_type",
    "create_order_instance",
    "OrdersProducer",
    "OrdersChannel",
    "OrdersManager",
    "OrdersUpdaterSimulator",
    "CloseOrderState",
    "CancelOrderState",
    "OpenOrderState",
    "create_order_state",
    "FillOrderState",
    "UnknownOrder",
    "MarketOrder",
    "SellMarketOrder",
    "BuyMarketOrder",
    "BuyLimitOrder",
    "SellLimitOrder",
    "LimitOrder",
    "TakeProfitOrder",
    "StopLossOrder",
    "StopLossLimitOrder",
    "TakeProfitLimitOrder",
    "TrailingStopOrder",
    "TrailingStopLimitOrder",
    "PositionsProducer",
    "PositionsChannel",
    "BalanceUpdaterSimulator",
    "BalanceProfitabilityUpdaterSimulator",
    "create_portfolio_from_exchange_manager",
    "BalanceUpdater",
    "BalanceProfitabilityUpdater",
    "PortfolioProfitability",
    "Portfolio",
    "BalanceProducer",
    "BalanceChannel",
    "BalanceProfitabilityProducer",
    "BalanceProfitabilityChannel",
    "SubPortfolio",
    "PortfolioManager",
    "PortfolioValueHolder",
    "FuturePortfolio",
    "MarginPortfolio",
    "SpotPortfolio",
    "Asset",
    "FutureAsset",
    "MarginAsset",
    "SpotAsset",
    "parse_decimal_portfolio",
    "parse_decimal_config_portfolio",
    "portfolio_to_float",
    "PositionsUpdaterSimulator",
    "Position",
    "LinearPosition",
    "InversePosition",
    "PositionState",
    "LiquidatePositionState",
    "OpenPositionState",
    "create_position_state",
    "PositionsUpdater",
    "PositionsManager",
    "create_position_instance_from_raw",
    "create_position_from_type",
    "create_symbol_position",
    "parse_position_status",
    "TradesManager",
    "TradesProducer",
    "TradesChannel",
    "create_trade_instance_from_raw",
    "create_trade_from_order",
    "create_trade_instance",
    "TradesUpdater",
    "Trade",
    "compute_win_rate",
    "ExchangePersonalData",
    "AUTHENTICATED_UPDATER_PRODUCERS",
    "AUTHENTICATED_UPDATER_SIMULATOR_PRODUCERS",
    "TraderOrderTypeClasses",
    "TraderPositionTypeClasses",
    "TransactionsManager",
    "Transaction",
    "BlockchainTransaction",
    "FeeTransaction",
    "RealisedPnlTransaction",
    "TransferTransaction",
    "create_blockchain_transaction",
    "create_realised_pnl_transaction",
    "create_fee_transaction",
    "create_transfer_transaction",
]
