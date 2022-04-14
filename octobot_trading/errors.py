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


class MissingFunds(Exception):
    """
    Raised upon placing an order while having insufficient funds
    """


class MissingMinimalExchangeTradeVolume(Exception):
    """
    Raised when a new order is impossible to create due to exchange minimal funds restrictions
    """


class TradingModeIncompatibility(Exception):
    """
    Raised when a trading mode is incompatible with the current situation
    """


class OrderCreationError(Exception):
    """
    Raised upon a failed order creation
    """


class OrderEditError(Exception):
    """
    Raised upon a failed order edition
    """


class NotSupported(Exception):
    """
    Raised when an exchange doesn't support the endpoint
    """


class FailedRequest(Exception):
    """
    Raised upon a failed request on an exchange API
    """


class AuthenticationError(Exception):
    """
    Raised when an exchange failed to authenticate
    """


class PortfolioNegativeValueError(Exception):
    """
    Raised when the portfolio is being updated with a negative value
    """


class PortfolioOperationError(Exception):
    """
    Raised when an invalid portfolio operation is asked for
    """


class MissingOrderException(Exception):
    """
    Raised when an order is missing
    """

    def __init__(self, order_id):
        super().__init__()
        self.order_id = order_id


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
