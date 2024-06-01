import random
import requests
from eth_typing import ChecksumAddress
from fake_useragent import UserAgent
from web3 import Web3
from web3.eth import AsyncEth
from eth_account.signers.local import LocalAccount

from .exceptions import InvalidProxy
from .transactions import Transaction
from .wallet import Wallet
from .contracts import Contracts
from .models import Networks, Network


class Client:
    account: LocalAccount

    def __init__(
            self,
            private_key: str | None = None,
            network: Network = Networks.Goerli,
            proxy: str | None = None,
            check_proxy: bool = True
    ) -> None:
        self.network = network
        self.headers = self._generate_headers()
        self.proxy = self._configure_proxy(proxy, check_proxy)
        self.w3 = self._initialize_web3(self.network.rpc, self.proxy, self.headers)
        self.account = self._initialize_account(private_key)
        self.wallet = Wallet(self)
        self.contracts = Contracts(self)
        self.transactions = Transaction(self)

    @staticmethod
    def _generate_headers() -> dict:
        return {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'user-agent': UserAgent().chrome
        }

    @staticmethod
    def _configure_proxy(proxy: str | None, check_proxy: bool) -> str | None:
        if proxy and 'http' not in proxy:
            proxy = f'http://{proxy}'

        if proxy and check_proxy:
            your_ip = requests.get(
                'http://eth0.me/', proxies={'http': proxy, 'https': proxy}, timeout=10
            ).text.rstrip()
            if your_ip not in proxy:
                raise InvalidProxy(f"Proxy doesn't work! Your IP is {your_ip}.")

        return proxy

    @staticmethod
    def _initialize_web3(rpc: str, proxy: str | None, headers: dict) -> Web3:
        return Web3(
            provider=Web3.AsyncHTTPProvider(
                endpoint_uri=rpc,
                request_kwargs={'proxy': proxy, 'headers': headers}
            ),
            modules={'eth': (AsyncEth,)},
            middlewares=[]
        )

    def _initialize_account(self, private_key: str | None) -> LocalAccount:
        if private_key:
            return self.w3.eth.account.from_key(private_key=private_key)
        return self.w3.eth.account.create(extra_entropy=str(random.randint(1, 999_999_999)))

    @staticmethod
    def get_checksum_address(address: str | ChecksumAddress) -> ChecksumAddress:
        return Web3.to_checksum_address(address)
