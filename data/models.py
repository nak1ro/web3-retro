from eth_async.models import RawContract, DefaultABIs
from eth_async.utils.utils import read_json
from eth_async.classes import Singleton

from data.config import ABIS_DIR


class Contracts(Singleton):
    # Arbitrum
    ARBITRUM_STARGATE = RawContract(
        title='ARBITRUM_STARGATE',
        address='0x53bf833a5d6c4dda888f69c22c88c9f356a41614',
        abi=read_json(path=(ABIS_DIR, 'stargate.json'))
    )

    ARBITRUM_HOPBRIDGE = RawContract(
        title='ARBITRUM_HOPBRIDGE',
        address='0xCB0a4177E0A60247C0ad18Be87f8eDfF6DD30283',
        abi=read_json(path=(ABIS_DIR, 'hop_bridge.json'))
    )

    ARBITRUM_USDC = RawContract(
        title='USDC',
        address='0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
        abi=DefaultABIs.Token
    )

    ARBITRUM_USDC_E = RawContract(
        title='USDC_E',
        address='0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8',
        abi=DefaultABIs.Token
    )

    ARBITRUM_USDT = RawContract(
        title='USDT',
        address='0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
        abi=DefaultABIs.Token
    )

    ARBITRUM_ETH = RawContract(
        title='ETH',
        address='0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE',
        abi=DefaultABIs.Token
    )

    # ETH
    ETH_SHIBASWAP = RawContract(
        title='ETH_SHIBASWAP',
        address='0x03f7724180AA6b939894B5Ca4314783B0b36b329',
        abi=read_json(path=(ABIS_DIR, 'shibaswap.json'))
    )

    ETH_WETH = RawContract(
        title='ETH',
        address='0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
        abi=DefaultABIs.Token
    )

    ETH_USDC = RawContract(
        title='USDC',
        address='0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
        abi=DefaultABIs.Token
    )

    ETH_DAI = RawContract(
        title='DAI',
        address='0x6B175474E89094C44Da98b954EedeAC495271d0F',
        abi=DefaultABIs.Token
    )

    ETH_USDT = RawContract(
        title='USDT',
        address='0xdAC17F958D2ee523a2206206994597C13D831ec7',
        abi=DefaultABIs.Token
    )

    # Poltgon
    POLYGON_STARGATE = RawContract(
        title='POLYGON_STARGATE',
        address='0x45A01E4e04F14f7A4a6702c74187c5F6222033cd',
        abi=read_json(path=(ABIS_DIR, 'stargate.json'))
    )

    POLYGON_USDC = RawContract(
        title='POLYGON_STARGATE',
        address='0x2791bca1f2de4661ed88a30c99a7a9449aa84174',
        abi=DefaultABIs.Token
    )

    # Avalanche
    AVALANCHE_STARGATE = RawContract(
        title='AVALANCHE_STARGATE',
        address='0x45A01E4e04F14f7A4a6702c74187c5F6222033cd',
        abi=read_json(path=(ABIS_DIR, 'stargate.json'))
    )

    AVALANCHE_USDC = RawContract(
        title='USDC',
        address='0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E',
        abi=DefaultABIs.Token
    )

