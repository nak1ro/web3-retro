import json
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass

from eth_typing import ChecksumAddress
from web3 import Web3
import requests

from . import exceptions
from .classes import AutoRepr


class TokenAmount:
    """Represents an amount of a token in both Wei and Ether units."""

    def __init__(self, amount: int | float | str | Decimal, decimals: int = 18, wei: bool = False) -> None:
        """
        Initialize the TokenAmount instance.

        :param amount: The amount of the token.
        :param decimals: The number of decimal places the token uses.
        :param wei: Whether the given amount is in Wei (True) or Ether (False).
        """
        self._amount = self._to_decimal(amount)
        self.decimals = decimals
        self.wei = wei

    @property
    def Wei(self) -> int:
        """The amount in Wei."""
        return int(self._amount * 10 ** self.decimals) if not self.wei else int(self._amount)

    @property
    def Ether(self) -> Decimal:
        """The amount in Ether."""
        return self._amount / 10 ** self.decimals if self.wei else self._amount

    @staticmethod
    def _to_decimal(amount: int | float | str | Decimal) -> Decimal:
        """Convert the amount to Decimal, handling potential exceptions."""
        try:
            return Decimal(amount)
        except InvalidOperation:
            raise ValueError(f"Invalid amount: {amount}")

    def __str__(self) -> str:
        """Return the string representation of the amount in Ether."""
        return f'{self.Ether}'


@dataclass
class DefaultABIs:
    Token = [
        {
            'constant': True,
            'inputs': [],
            'name': 'name',
            'outputs': [{'name': '', 'type': 'string'}],
            'payable': False,
            'stateMutability': 'view',
            'type': 'function'
        },
        {
            'constant': True,
            'inputs': [],
            'name': 'symbol',
            'outputs': [{'name': '', 'type': 'string'}],
            'payable': False,
            'stateMutability': 'view',
            'type': 'function'
        },
        {
            'constant': True,
            'inputs': [],
            'name': 'totalSupply',
            'outputs': [{'name': '', 'type': 'uint256'}],
            'payable': False,
            'stateMutability': 'view',
            'type': 'function'
        },
        {
            'constant': True,
            'inputs': [],
            'name': 'decimals',
            'outputs': [{'name': '', 'type': 'uint256'}],
            'payable': False,
            'stateMutability': 'view',
            'type': 'function'
        },
        {
            'constant': True,
            'inputs': [{'name': 'account', 'type': 'address'}],
            'name': 'balanceOf',
            'outputs': [{'name': '', 'type': 'uint256'}],
            'payable': False,
            'stateMutability': 'view',
            'type': 'function'
        },
        {
            'constant': True,
            'inputs': [{'name': 'owner', 'type': 'address'}, {'name': 'spender', 'type': 'address'}],
            'name': 'allowance',
            'outputs': [{'name': 'remaining', 'type': 'uint256'}],
            'payable': False,
            'stateMutability': 'view',
            'type': 'function'
        },
        {
            'constant': False,
            'inputs': [{'name': 'spender', 'type': 'address'}, {'name': 'value', 'type': 'uint256'}],
            'name': 'approve',
            'outputs': [],
            'payable': False,
            'stateMutability': 'nonpayable',
            'type': 'function'
        },
        {
            'constant': False,
            'inputs': [{'name': 'to', 'type': 'address'}, {'name': 'value', 'type': 'uint256'}],
            'name': 'transfer',
            'outputs': [], 'payable': False,
            'stateMutability': 'nonpayable',
            'type': 'function'
        }]


class Network:
    def __init__(
            self,
            name: str,
            rpc: str,
            chain_id: int | None = None,
            tx_type: int = 0,
            native_coin_decimal: int = 18,
            coin_symbol: str | None = None,
            explorer: str | None = None,
    ) -> None:
        self.name = name.lower()
        self.rpc = rpc
        self.chain_id = chain_id or self._get_chain_id()
        self.tx_type = tx_type
        self.native_coin_decimal = native_coin_decimal
        self.coin_symbol = coin_symbol or self._get_coin_symbol()
        self.explorer = explorer

        if self.coin_symbol:
            self.coin_symbol = self.coin_symbol.upper()

    def _get_chain_id(self) -> int:
        try:
            return Web3(Web3.HTTPProvider(self.rpc)).eth.chain_id
        except Exception as err:
            raise exceptions.WrongChainID(f'Can not get chain id: {err}')

    def _get_coin_symbol(self) -> str:
        try:
            response = requests.get('https://chainid.network/chains.json').json()
            for network in response:
                if network['chainId'] == self.chain_id:
                    return network['nativeCurrency']['symbol']
        except Exception as err:
            raise exceptions.WrongCoinSymbol(f'Can not get coin symbol: {err}')


class Networks:
    # Mainnets
    Ethereum = Network(
        name='ethereum',
        rpc='https://rpc.ankr.com/eth/',
        chain_id=1,
        tx_type=2,
        native_coin_decimal=18,
        coin_symbol='ETH',
        explorer='https://etherscan.io/',
    )

    Arbitrum = Network(
        name='arbitrum',
        rpc='https://arbitrum.llamarpc.com',
        chain_id=42161,
        tx_type=2,
        native_coin_decimal=18,
        coin_symbol='ETH',
        explorer='https://arbiscan.io/',
    )

    ArbitrumNova = Network(
        name='arbitrum_nova',
        rpc='https://nova.arbitrum.io/rpc/',
        chain_id=42170,
        tx_type=2,
        native_coin_decimal=18,
        coin_symbol='ETH',
        explorer='https://nova.arbiscan.io/',
    )

    Optimism = Network(
        name='optimism',
        rpc='https://rpc.ankr.com/optimism/',
        chain_id=10,
        tx_type=2,
        native_coin_decimal=18,
        coin_symbol='ETH',
        explorer='https://optimistic.etherscan.io/',
    )

    BSC = Network(
        name='bsc',
        rpc='https://rpc.ankr.com/bsc/',
        chain_id=56,
        tx_type=0,
        coin_symbol='BNB',
        native_coin_decimal=18,
        explorer='https://bscscan.com/',
    )

    Polygon = Network(
        name='polygon',
        rpc='https://rpc.ankr.com/polygon/',
        chain_id=137,
        tx_type=2,
        native_coin_decimal=18,
        coin_symbol='MATIC',
        explorer='https://polygonscan.com/',
    )

    Avalanche = Network(
        name='avalanche',
        rpc='https://rpc.ankr.com/avalanche/',
        chain_id=43114,
        tx_type=2,
        native_coin_decimal=18,
        coin_symbol='AVAX',
        explorer='https://snowtrace.io/',
    )

    # Testnets
    Goerli = Network(
        name='goerli',
        rpc='https://rpc.ankr.com/eth_goerli/',
        chain_id=5,
        tx_type=2,
        native_coin_decimal=18,
        coin_symbol='ETH',
        explorer='https://goerli.etherscan.io/',
    )


class RawContract(AutoRepr):
    """
    An instance of a raw contract.

    Attributes:
        title str: a contract title.
        address (ChecksumAddress): a contract address.
        abi list[dict[str, Any]] | str: an ABI of the contract.

    """
    title: str
    address: ChecksumAddress
    abi: list[dict[str, ...]]

    def __init__(self, title: str, address: str, abi: list[dict[str, ...]] | str) -> None:
        """
        Initialize the class.

        Args:
            title (str): a contract title.
            address (str): a contract address.
            abi (Union[List[Dict[str, Any]], str]): an ABI of the contract.

        """
        self.title = title
        self.address = Web3.to_checksum_address(address)
        self.abi = json.loads(abi) if isinstance(abi, str) else abi

    def __eq__(self, other) -> bool:
        return self.address == other.address and self.abi == other.abi


@dataclass
class CommonValues:
    """
    An instance with common values used in transactions.
    """
    Null: str = '0x0000000000000000000000000000000000000000000000000000000000000000'
    InfinityStr: str = '0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
    InfinityInt: int = int('0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff', 16)


class TxArgs(AutoRepr):
    """
    An instance for named transaction arguments.
    """

    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)

    def list(self) -> list:
        return list(self.__dict__.values())

    def tuple(self) -> tuple:
        return tuple(self.__dict__.values())
