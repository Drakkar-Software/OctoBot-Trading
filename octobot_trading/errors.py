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


class OctoBotExchangeError(Exception):
    """
    Parent class of local exceptions raised when communicating with exchanges
    """


class MissingFunds(OctoBotExchangeError):
    """
    Raised upon placing an order while having insufficient funds
    """


class MissingMinimalExchangeTradeVolume(OctoBotExchangeError):
    """
    Raised when a new order is impossible to create due to exchange minimal funds restrictions
    """


class ExchangeProxyError(OctoBotExchangeError):
    """
    Raised when an issue related to an exchange proxy is encountered
    """


class TradingModeIncompatibility(Exception):
    """
    Raised when a trading mode is incompatible with the current situation
    """


class OrderCreationError(OctoBotExchangeError):
    """
    Raised upon a failed order creation
    """


class UnsupportedOrderTypeError(OrderCreationError):
    """
    Raised when asking for an order type that is not supported by the exchange
    """


class UntradableSymbolError(OrderCreationError):
    """
    Raised when a symbol can't currently be traded on the exchange (not in exchange.get_all_tradable_symbols)
    """


class OrderEditError(OctoBotExchangeError):
    """
    Raised upon a failed order edition
    """


class OrderCancelError(OctoBotExchangeError):
    """
    Raised upon a failed order cancel
    """


class ExchangeOrderCancelError(OrderCancelError):
    """
    Raised when an exchange failed to execute the given request because the associated order can't be cancelled
    """


class OrderNotFoundOnCancelError(ExchangeOrderCancelError):
    """
    Raised upon a failed order cancel because order is not found
    """


class UnexpectedExchangeSideOrderStateError(Exception):
    """
    Raised when an order is in an unexpected state when fetched from exchange
    """


class OpenOrderError(UnexpectedExchangeSideOrderStateError):
    """
    Raised when an order is unexpectedly open
    """


class FilledOrderError(UnexpectedExchangeSideOrderStateError):
    """
    Raised when an order is unexpectedly filled
    """


class CancellingOrderError(UnexpectedExchangeSideOrderStateError):
    """
    Raised when an order is unexpectedly cancelling
    """


class ClosedOrderError(UnexpectedExchangeSideOrderStateError):
    """
    Raised when an order is unexpectedly closed
    """


class NotSupported(Exception):
    """
    Raised when an exchange doesn't support the required element
    """


class FailedRequest(OctoBotExchangeError):
    """
    Raised upon a failed request on an exchange API
    """


class RateLimitExceeded(OctoBotExchangeError):
    """
    Raised upon an exchange API rate limit error
    """


class UnavailableOrderTypeForMarketError(OctoBotExchangeError):
    """
    Raised when an exchange refuses to create a given type of order that should normally be supported
    """


class AuthenticationError(OctoBotExchangeError):
    """
    Raised when an exchange failed to authenticate
    """


class InvalidAPIKeyIPWhitelistError(AuthenticationError):
    """
    Raised when an exchange failed to authenticate due to an IP whitelist issue
    """


class ExchangeInternalSyncError(OctoBotExchangeError):
    """
    Raised when an exchange is returning an error due to its internal sync process
    (ex: when an order is filled but portfolio has not yet been updated)
    """


class ExchangeCompliancyError(OctoBotExchangeError):
    """
    Raised when an exchange failed to execute the given request because of compliance rules for the current user account
    """


class ExchangeAccountSymbolPermissionError(OctoBotExchangeError):
    """
    Raised when an exchange failed to execute the given request because of allowed traded symbols
    on the current user account
    """


class ExchangeClosedPositionError(OctoBotExchangeError):
    """
    Raised when an exchange failed to execute the given request because the associated position is closed.
    Can happen with reduce-only orders
    """


class ExchangeOrderInstantTriggerError(OctoBotExchangeError):
    """
    Raised when an exchange failed to execute the given request because the associated order would immediately trigger.
    Can happen with stop orders
    """


class PortfolioNegativeValueError(Exception):
    """
    Raised when the portfolio is being updated with a negative value
    """


class PortfolioOperationError(Exception):
    """
    Raised when an invalid portfolio operation is asked for
    """


class InvalidOrderState(Exception):
    """
    Raised when an order state is handled on a previously cleared order
    (cleared orders should never be touched)
    """


class InvalidLeverageValue(Exception):
    """
    Raised when a leverage is being updated with an invalid value
    """


class InvalidPositionSide(Exception):
    """
    Raised when an order with an invalid position side is triggering a position update
    """


class InvalidPosition(Exception):
    """
    Raised when an invalid position is created
    """


class ContractExistsError(Exception):
    """
    Raised when asking for a contract that doesn't exist
    """


class UnhandledContractError(Exception):
    """
    Raised when trying to use a contract that is not supported / implemented
    """


class UnsupportedContractConfigurationError(Exception):
    """
    Raised when a contract configuration is not supported
    """


class UnsupportedHedgeContractError(UnsupportedContractConfigurationError):
    """
    Raised when a hedge contract configuration is not supported
    """


class TooManyOpenPositionError(Exception):
    """
    Raised when changing future contract attributes without closing positions first
    """


class DuplicateTransactionIdError(Exception):
    """
    Raised when trying to add a new transaction with a duplicate id
    """


class LiquidationPriceReached(Exception):
    """
    Raised when the liquidation price has been reach
    """


class ConflictingOrdersError(Exception):
    """
    Raised when an order is that would create an order conflict is created
    """


class OrderGroupTriggerArgumentError(Exception):
    """
    Raised when an order triggered with invalid arguments
    """


class ConflictingOrderGroupError(Exception):
    """
    Raised when creating a group with an existing name
    """


class MissingPriceDataError(Exception):
    """
    Raised when a price info is missing
    """


class PendingPriceDataError(Exception):
    """
    Raised when a price info is waiting to be updated
    """


class UnreachableExchange(Exception):
    """
    Raised when an exchange cant be reached (likely when it's offline)
    """


class InvalidArgumentError(Exception):
    """
    Raised when a keyword is called with invalid arguments
    """


class OrderDescriptionNotFoundError(Exception):
    """
    Raised when an order description is not found
    """


class PositionDescriptionNotFoundError(Exception):
    """
    Raised when a position description is not found
    """


class AdapterError(Exception):
    """
    Raised when an error occurs in an adapter
    """


class UnexpectedAdapterError(Exception):
    """
    Raised when an unexpected error occurs in an adapter
    """


class IncompletePNLError(Exception):
    """
    Raised when a pnl computation is asked on a invalid pnl
    """


class InitializingError(Exception):
    """
    Raised when OctoBot is still in initialization
    """
