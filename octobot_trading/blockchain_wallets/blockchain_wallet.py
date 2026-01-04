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
import decimal

import octobot_trading.constants as constants
import octobot_trading.errors as errors
import octobot_trading.blockchain_wallets.blockchain_wallet_parameters as blockchain_wallet_parameters


class BlockchainWallet:
    """
    Base class for all blockchain wallets, to be implemented by specific blockchain wallet subclasses.
    """

    def __init__(self, parameters: blockchain_wallet_parameters.BlockchainWalletParameters):
        self.blockchain_descriptor: blockchain_wallet_parameters.BlockchainDescriptor = parameters.blockchain_descriptor
        self.wallet_descriptor: blockchain_wallet_parameters.WalletDescriptor = parameters.wallet_descriptor

    async def get_balance(self, token_symbol: str) -> decimal.Decimal:
        if token_symbol == self.blockchain_descriptor.native_coin_symbol:
            return await self.get_native_coin_balance()
        return await self.get_custom_token_balance(self._get_token_descriptor(token_symbol))

    async def transfer(self, token_symbol: str, amount: decimal.Decimal, to_address: str):
        if not constants.ALLOW_FUNDS_TRANSFER:
            raise errors.DisabledFundsTransferError("Funds transfer is not enabled")
        if token_symbol == self.blockchain_descriptor.native_coin_symbol:
            return await self.transfer_native_coin(amount, to_address)
        return await self.transfer_custom_token(self._get_token_descriptor(token_symbol), amount, to_address)

    @classmethod
    def get_blockchain_name(cls) -> str:
        raise NotImplementedError("get_blockchain_name is not implemented")

    async def get_native_coin_balance(self) -> decimal.Decimal:
        raise NotImplementedError("get_native_coin_balance is not implemented")

    async def get_custom_token_balance(self, token_descriptor: blockchain_wallet_parameters.TokenDescriptor) -> decimal.Decimal:
        raise NotImplementedError("get_custom_token_balance is not implemented")

    async def transfer_native_coin(self, amount: decimal.Decimal, to_address: str):
        raise NotImplementedError("transfer_native_coin is not implemented")

    async def transfer_custom_token(
        self,
        token_descriptor: blockchain_wallet_parameters.TokenDescriptor,
        amount: decimal.Decimal,
        to_address: str,
    ):
        raise NotImplementedError("transfer_custom_token is not implemented")

    def _get_token_descriptor(self, token_symbol: str) -> blockchain_wallet_parameters.TokenDescriptor:
        for token_parameter in self.blockchain_descriptor.tokens:
            if token_parameter.symbol == token_symbol:
                return token_parameter
        raise KeyError(
            f"Token {token_symbol} not found in {self.get_blockchain_name()} "
            f"wallet's {len(self.blockchain_descriptor.tokens)} pre-configured tokens."
        )
