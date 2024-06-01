from __future__ import annotations
from typing import TYPE_CHECKING

from web3 import Web3
from eth_typing import ChecksumAddress

from .models import TokenAmount

if TYPE_CHECKING:
    from .client import Client


class Wallet:
    def __init__(self, client: Client) -> None:
        self.client = client

    async def balance(
            self,
            token_address: str | ChecksumAddress | None = None,
            address: str | ChecksumAddress | None = None,
            decimals: int = 18
    ) -> TokenAmount:
        address = self.client.get_checksum_address(address or self.client.account.address)

        if not token_address:
            return await self._get_eth_balance(address, decimals)
        return await self._get_token_balance(token_address, address)

    async def nonce(self, address: ChecksumAddress | None = None) -> int:
        address = address or self.client.account.address
        return await self.client.w3.eth.get_transaction_count(address)

    async def _get_eth_balance(self, address: ChecksumAddress, decimals: int) -> TokenAmount:
        balance = await self.client.w3.eth.get_balance(account=address)
        return TokenAmount(amount=balance, decimals=decimals, wei=True)

    async def _get_token_balance(self, token_address: str | ChecksumAddress, address: ChecksumAddress) -> TokenAmount:
        token_address = self.client.get_checksum_address(token_address)
        contract = await self.client.contracts.get_default_contract_instance(contract_address=token_address)
        balance = await contract.functions.balanceOf(address).call()
        token_decimals = await contract.functions.decimals().call()
        return TokenAmount(amount=balance, decimals=token_decimals, wei=True)
