from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any

from web3 import Web3
from eth_typing import ChecksumAddress
from web3.contract import AsyncContract, Contract

from . import types
from .models import DefaultABIs, RawContract
from .utils.strings import text_between
from .utils.utils import async_get

if TYPE_CHECKING:
    from .client import Client


class Contracts:
    def __init__(self, client: Client) -> None:
        self.client = client

    async def get_default_contract_instance(self, contract_address: ChecksumAddress | str) -> Contract | AsyncContract:
        """
        Get a token contract instance with a standard set of functions.

        Args:
            contract_address (ChecksumAddress | str): The contract address.

        Returns:
            Contract | AsyncContract: The token contract instance.
        """
        contract_address = Web3.to_checksum_address(contract_address)
        return self.client.w3.eth.contract(address=contract_address, abi=DefaultABIs.Token)

    async def get_contract_instance(
            self,
            contract_address: types.Contract,
            abi: List[Dict[str, Any]] | str | None = None
    ) -> AsyncContract | Contract:
        """
        Get a contract instance.

        Args:
            contract_address (types.Contract): The contract address or instance.
            abi (List[Dict[str, Any]] | str | None): The contract ABI. (Optional)

        Returns:
            AsyncContract | Contract: The contract instance.

        Raises:
            ValueError: If the ABI cannot be retrieved for the contract.
        """
        contract_address, contract_abi = await self.get_contract_attributes(contract_address)
        abi = abi or contract_abi
        if not abi:
            raise ValueError('Cannot get ABI for contract')

        return self.client.w3.eth.contract(address=contract_address, abi=abi)

    @staticmethod
    async def get_signature(hex_signature: str) -> List[str] | None:
        """
        Find all matching signatures in the database of https://www.4byte.directory/.

        Args:
            hex_signature (str): The signature hash.

        Returns:
            List[str] | None: A list of matching text signatures, or None if not found.
        """
        try:
            response = await async_get(f'https://www.4byte.directory/api/v1/signatures/?hex_signature={hex_signature}')
            results = response['results']
            return [m['text_signature'] for m in sorted(results, key=lambda result: result['created_at'])]
        except Exception:
            return None

    async def parse_function_to_abi(self, text_signature: str) -> Dict[str, Any]:
        """
        Construct a function dictionary for the ABI based on the provided text signature.

        Args:
            text_signature (str): A text signature, e.g., approve(address,uint256).

        Returns:
            Dict[str, Any]: The function dictionary for the ABI.
        """
        name, inputs, tuples = self._parse_signature(text_signature=text_signature)
        return await self._build_function_abi(name=name, inputs=inputs, tuples=tuples)

    @staticmethod
    async def get_contract_attributes(contract: types.Contract) -> tuple[ChecksumAddress, List[Dict[str, Any]] | None]:
        """
        Convert different types of contracts to their address and ABI.

        Args:
            contract (types.Contract): The contract address or instance.

        Returns:
            tuple[ChecksumAddress, List[Dict[str, Any]] | None]: The checksummed contract address and ABI.
        """
        if isinstance(contract, (AsyncContract, RawContract)):
            return contract.address, contract.abi
        return Web3.to_checksum_address(contract), None

    def _parse_signature(self, text_signature: str) -> tuple[str, List[str], List[List[str]]]:
        """
        Parse the text signature into its components.

        Args:
            text_signature (str): The text signature.

        Returns:
            tuple[str, List[str], List[List[str]]]: The function name, inputs, and tuples.
        """
        name, sign = self._split_signature(text_signature)
        sign, tuples = self._extract_tuples(sign)
        inputs = self._get_inputs(sign)
        return name, inputs, tuples

    @staticmethod
    def _split_signature(text_signature: str) -> tuple[str, str]:
        """
        Split the text signature into name and the rest of the signature.

        Args:
            text_signature (str): The text signature.

        Returns:
            tuple[str, str]: The function name and the rest of the signature.
        """
        split_result = text_signature.split('(', 1)
        return split_result[0], split_result[1] if len(split_result) > 1 else ''

    @staticmethod
    def _extract_tuples(sign: str) -> tuple[str, List[List[str]]]:
        """
        Extract tuples from the signature.

        Args:
            sign (str): The rest of the signature.

        Returns:
            tuple[str, List[List[str]]]: The modified signature and the extracted tuples.
        """
        tuples = []
        while '(' in sign:
            tuple_ = text_between(text=sign[:-1], begin='(', end=')')
            tuples.append(tuple_.split(',') or [])
            sign = sign.replace(f'({tuple_})', 'tuple')
        return sign, tuples

    @staticmethod
    def _get_inputs(sign: str) -> List[str]:
        """
        Get the inputs from the signature.

        Args:
            sign (str): The modified signature.

        Returns:
            List[str]: The list of inputs.
        """
        return sign.split(',') if sign else []

    @staticmethod
    async def _build_function_abi(name: str, inputs: List[str], tuples: List[List[str]]) -> Dict[str, Any]:
        """
        Build the function ABI.

        Args:
            name (str): The function name.
            inputs (List[str]): The function inputs.
            tuples (List[List[str]]): The tuples in the inputs.

        Returns:
            Dict[str, Any]: The function ABI dictionary.
        """
        function = {
            'type': 'function',
            'name': name,
            'inputs': [],
            'outputs': [{'type': 'uint256'}]
        }
        i = 0
        for type_ in inputs:
            input_ = {'type': type_}
            if type_ == 'tuple':
                input_['components'] = [{'type': comp_type} for comp_type in tuples[i]]
                i += 1
            function['inputs'].append(input_)
        return function

    @staticmethod
    async def _extract_contract_attributes(contract: types.Contract) -> tuple[
        ChecksumAddress, List[Dict[str, Any]] | None]:
        """
        Extract the contract attributes.

        Args:
            contract (types.Contract): The contract address or instance.

        Returns:
            tuple[ChecksumAddress, List[Dict[str, Any]] | None]: The checksummed contract address and ABI.
        """
        if isinstance(contract, (AsyncContract, RawContract)):
            return contract.address, contract.abi
        return Web3.to_checksum_address(contract), None
