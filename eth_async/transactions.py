from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict

from hexbytes import HexBytes
from web3.contract import Contract, AsyncContract
from web3.types import _Hash32, TxParams
from eth_account.datastructures import SignedTransaction

from .classes import AutoRepr
from .models import TokenAmount, CommonValues, TxArgs
from . import exceptions, types

if TYPE_CHECKING:
    from .client import Client


class Tx(AutoRepr):
    """
    An instance of transaction for easy execution of actions on it.
    """

    def __init__(self, tx_hash: str | _Hash32 | None = None, params: Dict[str, Any] | None = None) -> None:
        """
        Initialize the class.

        Args:
            tx_hash: The transaction hash.
            params: A dictionary with transaction parameters.
        """
        if not tx_hash and not params:
            raise exceptions.TransactionException("Specify 'tx_hash' or 'params' argument values!")

        self.hash = HexBytes(tx_hash) if isinstance(tx_hash, str) else tx_hash
        self.params = params
        self.receipt = None
        self.function_identifier = None
        self.input_data = None

    async def parse_params(self, client: Client) -> Dict[str, Any]:
        """
        Parse the parameters of a sent transaction.

        Args:
            client: The Client instance.

        Returns:
            Dict[str, Any]: The parameters of a sent transaction.
        """
        tx_data = await client.w3.eth.get_transaction(transaction_hash=self.hash)
        self.params = self._extract_params_from_tx_data(tx_data=tx_data, client=client)
        return self.params

    async def wait_for_receipt(
            self, client: Client, timeout: int | float = 120, poll_latency: float = 0.1
    ) -> Dict[str, Any]:
        """
        Wait for the transaction receipt.

        Args:
            client: The Client instance.
            timeout: The receipt waiting timeout in seconds. (Default: 120 sec)
            poll_latency: The poll latency in seconds. (Default: 0.1 sec)

        Returns:
            Dict[str, Any]: The transaction receipt.
        """
        self.receipt = await client.transactions.wait_for_receipt(
            tx_hash=self.hash, timeout=timeout, poll_latency=poll_latency
        )
        return self.receipt

    @staticmethod
    def _extract_params_from_tx_data(tx_data: Dict[str, Any], client: Client) -> Dict[str, Any]:
        """
        Extract transaction parameters from the transaction data.

        Args:
            tx_data: The transaction data.
            client: The Client instance.

        Returns:
            Dict[str, Any]: Extracted transaction parameters.
        """
        return {
            'chainId': client.network.chain_id,
            'nonce': int(tx_data.get('nonce')),
            'gasPrice': int(tx_data.get('gasPrice')),
            'gas': int(tx_data.get('gas')),
            'from': tx_data.get('from'),
            'to': tx_data.get('to'),
            'data': tx_data.get('input'),
            'value': int(tx_data.get('value'))
        }


class Transaction:
    def __init__(self, client: Client) -> None:
        """
        Initialize the Transaction class.

        Args:
            client: The Client instance.
        """
        self.client = client

    async def get_gas_price(self) -> TokenAmount:
        """
        Get the current gas price.

        Returns:
            TokenAmount: The gas price in Wei.
        """
        return TokenAmount(amount=await self.client.w3.eth.gas_price, wei=True)

    async def get_max_priority_fee(self) -> TokenAmount:
        """
        Get current max priority fee (to send EIP-1559, it legacy instead we use -> gasPrice).

        Returns:
            TokenAmount: The max priority fee in Wei.
        """
        return TokenAmount(amount=await self.client.w3.eth.max_priority_fee, wei=True)

    async def get_estimated_gas(self, tx_params: TxParams) -> TokenAmount:
        """
        Estimate the gas limit for a transaction.

        Args:
            tx_params: The parameters of the transaction.

        Returns:
            TokenAmount: The estimated gas limit in Wei.
        """
        return TokenAmount(amount=await self.client.w3.eth.estimate_gas(transaction=tx_params), wei=True)

    async def get_base_gas_fee(self) -> TokenAmount:
        """
        Get the base gas fee for the latest block.

        Returns:
            TokenAmount: The base gas fee in Wei.
        """
        return TokenAmount(amount=(await self.client.w3.eth.get_block('latest'))['baseFeePerGas'], wei=True)

    async def get_allowance_amount(
            self, owner_address: str, spender_address: str, token_contract: types.Contract
    ) -> int:
        """
        Get the allowance amount for a token.

        Args:
            owner_address: The owner's address.
            spender_address: The spender's address.
            token_contract: The token contract instance.

        Returns:
            int: The allowance amount.
        """
        return await token_contract.functions.allowance(
            owner_address,
            spender_address
        ).call()

    async def get_max_fee_per_gas(self) -> TokenAmount:
        """
        Get the maximum fee per gas.

        Returns:
            TokenAmount: The maximum fee per gas in Wei.

        Raises:
            exceptions.GasValueObtaining: If base fee or max priority fee cannot be obtained.
        """
        base_fee = (await self.get_base_gas_fee()).Wei
        max_priority_fee = (await self.get_max_priority_fee()).Wei

        if base_fee is None or max_priority_fee is None:
            raise exceptions.GasValueObtaining()

        return TokenAmount(amount=(max_priority_fee * 2) + (base_fee * 1.05), wei=True)

    async def sign_transaction(self, tx_params: TxParams) -> SignedTransaction:
        """
        Sign a transaction.

        Args:
            tx_params: The parameters of the transaction.

        Returns:
            SignedTransaction: The signed transaction.
        """
        return self.client.w3.eth.account.sign_transaction(
            transaction_dict=tx_params, private_key=self.client.account.key
        )

    async def auto_add_params(self, tx_params: TxParams) -> TxParams:
        """
        Add missing parameters to the transaction parameters.

        Args:
            tx_params: The parameters of the transaction.

        Returns:
            TxParams: The transaction parameters with added values.
        """
        tx_params['chainId'] = tx_params.get('chainId', self.client.network.chain_id)
        tx_params['nonce'] = await self.client.wallet.nonce()
        tx_params['from'] = self.client.account.address

        if self.client.network.tx_type == 2:
            tx_params['maxPriorityFeePerGas'] = (await self.get_max_priority_fee()).Wei
            tx_params['maxFeePerGas'] = (await self.get_max_fee_per_gas()).Wei
        else:
            tx_params['gasPrice'] = (await self.get_gas_price()).Wei

        tx_params['gas'] = (await self.get_estimated_gas(tx_params=tx_params)).Wei

        return tx_params

    async def sign_and_send_transaction(self, tx_params: TxParams) -> Tx:
        """
        Sign and send a transaction. Additionally, add 'chainId', 'nonce', 'from', 'gasPrice' or
        'maxFeePerGas' + 'maxPriorityFeePerGas' and 'gas' parameters to transaction parameters if they are missing.

        Args:
            tx_params: The parameters of the transaction.

        Returns:
            Tx: An instance of the sent transaction.
        """
        tx_params = await self.auto_add_params(tx_params=tx_params)
        signed_tx = await self.sign_transaction(tx_params=tx_params)
        tx_hash = await self.client.w3.eth.send_raw_transaction(transaction=signed_tx.rawTransaction)
        return Tx(tx_hash=tx_hash, params=tx_params)

    async def get_approved_token_amount(
            self,
            token_contract: types.Contract,
            spender_address: types.Contract,
            owner_address: types.Address
    ) -> TokenAmount:
        """
        Get amount of tokens that are already approved.

        Args:
            token_contract: The contract address or instance of token.
            spender_address: The spender address, contract address or instance.
            owner_address: The owner address. (Imported to client address)

        Returns:
            TokenAmount: The approved amount.
        """
        allowance_amount = await self.get_allowance_amount(
            owner_address=owner_address, spender_address=spender_address, token_contract=token_contract
        )

        return TokenAmount(
            amount=allowance_amount, decimals=await self.get_decimals(contract=token_contract), wei=True
        )

    async def wait_for_receipt(
            self,
            tx_hash: str | _Hash32,
            timeout: int | float = 120,
            poll_latency: float = 0.1
    ) -> Dict[str, Any]:
        """
        Wait for a transaction receipt.

        Args:
            tx_hash: The transaction hash.
            timeout: The receipt waiting timeout in seconds. (Default: 120)
            poll_latency: The poll latency in seconds. (Default: 0.1 sec)

        Returns:
            Dict[str, Any]: The transaction receipt.
        """
        return dict(await self.client.w3.eth.wait_for_transaction_receipt(
            transaction_hash=tx_hash, timeout=timeout, poll_latency=poll_latency
        ))

    async def approve_token_spending(
            self,
            token_contract: types.Contract,
            spender_address: types.Address,
            amount: types.Amount | None = None,
            gas_limit: types.GasLimit | None = None,
    ) -> Tx:
        """
        Approve token spending for specified address.

        Args:
            token_contract: The contract address or instance of token to approve.
            spender_address: The spender address, contract address or instance.
            amount: The amount to approve. (Default: Infinity)
            gas_limit: The gas limit in Wei. (Parsed from the network)

        Returns:
            Tx: The instance of the sent transaction.
        """
        amount = await self._determine_approve_amount(amount=amount, token_contract=token_contract.address)

        tx_params = await self._build_tx_approve_params(
            token_contract=token_contract, spender_address=spender_address, amount=amount, gas_limit=gas_limit
        )

        return await self.sign_and_send_transaction(tx_params=tx_params)

    async def _determine_approve_amount(
            self, amount: types.Amount | None, token_contract: Contract | AsyncContract
    ) -> int:
        """
        Determine the amount to approve.

        Args:
            amount: The amount to approve.
            contract: The token contract instance.

        Returns:
            int: The amount to approve in Wei.
        """
        if not amount:
            amount = CommonValues.InfinityInt
        elif isinstance(amount, (int, float)):
            amount = TokenAmount(amount=amount, decimals=await self.get_decimals(contract=token_contract)).Wei
        else:
            amount = amount.Wei

        return amount

    async def _build_tx_approve_params(
            self,
            token_contract: Contract | AsyncContract,
            spender_address: str,
            amount: int,
            gas_limit: int | None,
    ) -> TxParams:
        """
        Build the transaction parameters for approval.

        Args:
            token_contract: The token contract instance.
            spender_address: The spender address.
            amount: The amount to approve.
            gas_limit: The gas limit in Wei.

        Returns:
            TxParams: The transaction parameters.
        """
        tx_args = TxArgs(spender=spender_address, amount=amount)

        tx_params = {
            'nonce': await self.client.wallet.nonce(),
            'to': token_contract.address,
            'data': token_contract.encodeABI('approve', args=tx_args.tuple()),
            'from': self.client.account.address
        }

        if gas_limit:
            if isinstance(gas_limit, int):
                gas_limit = TokenAmount(amount=gas_limit, wei=True)
            tx_params['gas'] = gas_limit.Wei

        return tx_params

    async def get_decimals(self, contract: types.Contract) -> int:
        """
        Get the decimals for a token contract.

        Args:
            contract: The token contract instance.

        Returns:
            int: The number of decimals.
        """
        contract_address, abi = await self.client.contracts.get_contract_attributes(contract)
        contract = await self.client.contracts.get_default_contract_instance(contract_address=contract_address)
        return await contract.functions.decimals().call()

    async def sign_message(self):
        """
        Sign a message. (To be implemented)
        """
        pass

    @staticmethod
    async def decode_input_data():
        """
        Decode input data. (To be implemented)
        """
        pass
