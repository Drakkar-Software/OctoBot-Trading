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
import dataclasses
import octobot_commons.dataclasses


@dataclasses.dataclass
class TokenDescriptor(octobot_commons.dataclasses.FlexibleDataclass):
    """
    Descriptor of a token
    """
    symbol: str
    decimals: int
    contract_address: str


@dataclasses.dataclass
class BlockchainDescriptor(octobot_commons.dataclasses.FlexibleDataclass):
    """
    Descriptor for a blockchain
    """
    name: str
    native_coin_symbol: str = ""
    network: str = ""
    chain_id: str = ""
    tokens: list[TokenDescriptor] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        if self.tokens and isinstance(self.tokens[0], dict):
            self.tokens = [TokenDescriptor.from_dict(token) for token in self.tokens]


@dataclasses.dataclass
class WalletDescriptor(octobot_commons.dataclasses.FlexibleDataclass):
    """
    Descriptor for a wallet
    """
    wallet_address: str
    wallet_private_key: str


@dataclasses.dataclass
class BlockchainWalletParameters(octobot_commons.dataclasses.FlexibleDataclass):
    """
    Parameters for a blockchain wallet
    """
    blockchain_descriptor: BlockchainDescriptor
    wallet_descriptor: WalletDescriptor

    def __post_init__(self):
        if self.blockchain_descriptor and isinstance(self.blockchain_descriptor, dict):
            self.blockchain_descriptor = BlockchainDescriptor.from_dict(self.blockchain_descriptor)
        if self.wallet_descriptor and isinstance(self.wallet_descriptor, dict):
            self.wallet_descriptor = WalletDescriptor.from_dict(self.wallet_descriptor)
