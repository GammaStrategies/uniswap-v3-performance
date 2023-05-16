"""Token pricing"""
import asyncio
from collections import defaultdict

from v3data import UniswapV3Client, LlamaClient
from v3data.enums import Chain, Protocol
from v3data.utils import sqrtPriceX96_to_priceDecimal

POOLS = {
    Chain.MAINNET: {
        "USDC_WETH": {
            "protocol": Protocol.UNISWAP,
            "address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        },
        "WETH_RPL": {
            "protocol": Protocol.UNISWAP,
            "address": "0xe42318ea3b998e8355a3da364eb9d48ec725eb45",
        },
        "GAMMA_WETH": {
            "protocol": Protocol.UNISWAP,
            "address": "0x4006bed7bf103d70a1c6b7f1cef4ad059193dc25",
        },
        "AXL_USDC": {
            "protocol": Protocol.UNISWAP,
            "address": "0x5b0d2536f0c970b8d9cbf3959460fb97ce808ade",
        },
    },
    Chain.OPTIMISM: {
        "WETH_USDC": {
            "protocol": Protocol.UNISWAP,
            "address": "0x85149247691df622eaf1a8bd0cafd40bc45154a9",
        },
        "WETH_OP": {
            "protocol": Protocol.UNISWAP,
            "address": "0x68f5c0a2de713a54991e01858fd27a3832401849",
        },
    },
    Chain.POLYGON: {
        "WMATIC_USDC": {
            "protocol": Protocol.QUICKSWAP,
            "address": "0xae81fac689a1b4b1e06e7ef4a2ab4cd8ac0a087d",
        },
        "WMATIC_QI": {
            "protocol": Protocol.QUICKSWAP,
            "address": "0x5cd94ead61fea43886feec3c95b1e9d7284fdef3",
        },
        "WMATIC_QUICK": {
            "protocol": Protocol.QUICKSWAP,
            "address": "0x9f1a8caf3c8e94e43aa64922d67dff4dc3e88a42",
        },
        "WMATIC_DQUICK": {
            "protocol": Protocol.QUICKSWAP,
            "address": "0xb8d00c66accdc01e78fd7957bf24050162916ae2",
        },
        "WMATIC_GHST": {
            "protocol": Protocol.QUICKSWAP,
            "address": "0x80deece4befd9f27d2df88064cf75f080d3ce1b2",
        },
        "WMATIC_ANKR": {
            "protocol": Protocol.QUICKSWAP,
            "address": "0x2f2dd65339226df7441097a710aba0f493879579",
        },
        "USDC_DAVOS": {
            "protocol": Protocol.QUICKSWAP,
            "address": "0xfb0bc232cd11dbe804b489860c470b7f9cc80d9f",
        },
        "USDC_GIDDY": {
            "protocol": Protocol.QUICKSWAP,
            "address": "0x65c30f39b880bdd9616280450c4b41cc74b438b7",
        },
        "WMATIC_LCD": {
            "protocol": Protocol.QUICKSWAP,
            "address": "0xd9c2c978915b907df04972cb3f577126fe55143c",
        },
        "WOMBAT_USDC": {
            "protocol": Protocol.QUICKSWAP,
            "address": "0xaf835698673655e9910de8398df6c5238f5d3aeb",
        },
        "USDC_FIS": {
            "protocol": Protocol.QUICKSWAP,
            "address": "0x2877703a3ba3e712d684d22bd6d60cc0031d84e8"
        },
        "SD_USDC": {
            "protocol": Protocol.QUICKSWAP,
            "address": "0x5d0acfa39a0fca603147f1c14e53f46be76984bc"
        }
    },
    Chain.POLYGON_ZKEVM: {
        "WETH_USDC": {
            "protocol": Protocol.QUICKSWAP,
            "address": "0xc44ad482f24fd750caeba387d2726d8653f8c4bb",
        },
        "QUICK_USDC": {
            "protocol": Protocol.QUICKSWAP,
            "address": "0x1247b70c4b41890e8c1836e88dd0c8e3b23dd60e",
        },
        "WETH_MATIC": {
            "protocol": Protocol.QUICKSWAP,
            "address": "0xb73abfb5a2c89f4038baa476ff3a7942a021c196",
        },
    },
    Chain.BSC: {},
    Chain.AVALANCHE: {},
    Chain.ARBITRUM: {},
}


POOL_PATHS = {
    Chain.MAINNET: {
        # GAMMA
        "0x6bea7cfef803d1e3d5f7c0103f7ded065644e197": [
            (POOLS[Chain.MAINNET]["GAMMA_WETH"], 1),
            (POOLS[Chain.MAINNET]["USDC_WETH"], 0),
        ],
        # RPL
        "0xd33526068d116ce69f19a9ee46f0bd304f21a51f": [
            (POOLS[Chain.MAINNET]["WETH_RPL"], 0),
            (POOLS[Chain.MAINNET]["USDC_WETH"], 0),
        ],
        # AXL
        "0x467719ad09025fcc6cf6f8311755809d45a5e5f3": [
            (POOLS[Chain.MAINNET]["AXL_USDC"], 1)
        ],
    },
    Chain.OPTIMISM: {
        # OP
        "0x4200000000000000000000000000000000000042": [
            (POOLS[Chain.OPTIMISM]["WETH_OP"], 0),
            (POOLS[Chain.OPTIMISM]["WETH_USDC"], 1),
        ],
        # MOCK-OPT
        "0x601e471de750cdce1d5a2b8e6e671409c8eb2367": [
            (POOLS[Chain.OPTIMISM]["WETH_OP"], 0),
            (POOLS[Chain.OPTIMISM]["WETH_USDC"], 1),
        ],
    },
    Chain.POLYGON: {
        # WMATIC
        "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270": [
            (POOLS[Chain.POLYGON]["WMATIC_USDC"], 1)
        ],
        # QI
        "0x580a84c73811e1839f75d86d75d88cca0c241ff4": [
            (POOLS[Chain.POLYGON]["WMATIC_QI"], 0),
            (POOLS[Chain.POLYGON]["WMATIC_USDC"], 1),
        ],
        # QUICK
        "0xb5c064f955d8e7f38fe0460c556a72987494ee17": [
            (POOLS[Chain.POLYGON]["WMATIC_QUICK"], 0),
            (POOLS[Chain.POLYGON]["WMATIC_USDC"], 1),
        ],
        # dQUICK
        "0x958d208cdf087843e9ad98d23823d32e17d723a1": [
            (POOLS[Chain.POLYGON]["WMATIC_DQUICK"], 0),
            (POOLS[Chain.POLYGON]["WMATIC_USDC"], 1),
        ],
        # GHST
        "0x385eeac5cb85a38a9a07a70c73e0a3271cfb54a7": [
            (POOLS[Chain.POLYGON]["WMATIC_GHST"], 0),
            (POOLS[Chain.POLYGON]["WMATIC_USDC"], 1),
        ],
        # ANKR
        "0x101a023270368c0d50bffb62780f4afd4ea79c35": [
            (POOLS[Chain.POLYGON]["WMATIC_ANKR"], 0),
            (POOLS[Chain.POLYGON]["WMATIC_USDC"], 1),
        ],
        # DAVOS
        "0xec38621e72d86775a89c7422746de1f52bba5320": [
            (POOLS[Chain.POLYGON]["USDC_DAVOS"], 0)
        ],
        # GIDDY
        "0x67eb41a14c0fe5cd701fc9d5a3d6597a72f641a6": [
            (POOLS[Chain.POLYGON]["USDC_GIDDY"], 0)
        ],
        # LCD
        "0xc2a45fe7d40bcac8369371b08419ddafd3131b4a": [
            (POOLS[Chain.POLYGON]["WMATIC_LCD"], 0),
            (POOLS[Chain.POLYGON]["WMATIC_USDC"], 1),
        ],
        # WOMBAT
        "0x0c9c7712c83b3c70e7c5e11100d33d9401bdf9dd": [
            (POOLS[Chain.POLYGON]["WOMBAT_USDC"], 1),
        ],
        # FIS
        "0x7a7b94f18ef6ad056cda648588181cda84800f94": [
            (POOLS[Chain.POLYGON]["USDC_FIS"], 0),
        ],
        # SD
        "0x1d734a02ef1e1f5886e66b0673b71af5b53ffa94": [
            (POOLS[Chain.POLYGON]["SD_USDC"], 1),
        ],
    },
    Chain.POLYGON_ZKEVM: {
        # WMATIC
        "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270": [
            (POOLS[Chain.POLYGON_ZKEVM]["WETH_MATIC"], 0),
            (POOLS[Chain.POLYGON_ZKEVM]["WETH_USDC"], 1),
        ],
        # QUICK
        "0x68286607a1d43602d880d349187c3c48c0fd05e6": [
            (POOLS[Chain.POLYGON_ZKEVM]["QUICK_USDC"], 1),
        ],
    },
    Chain.BSC: {},
    Chain.AVALANCHE: {},
    Chain.ARBITRUM: {},
}


class DexPriceData:
    """Base class for dex prices"""

    def __init__(self, protocol: Protocol, chain: Chain, pools: list[str]) -> None:
        self.protocol = protocol
        self.chain = chain
        self.uniswap_client = UniswapV3Client(protocol, chain)
        self.pools = pools
        self.pool_query = ""
        self.data = {}

    def _init_queries(self):
        self.pool_query = """
        query tokenPrice($pools: [String!]!){
            pools(
                where: {
                    id_in: $pools
                }
            ){
                id
                sqrtPrice
                token0{
                    symbol
                    decimals
                }
                token1{
                    symbol
                    decimals
                }
            }
        }
        """

    async def get_data(self):
        self._init_queries()
        variables = {"pools": self.pools}
        response = await self.uniswap_client.query(self.pool_query, variables)
        self.data = response["data"]["pools"]


class DexPrice:
    def __init__(self, chain: Chain):
        self.chain_prices: dict
        self.token_prices: dict
        self.chain = chain

    async def _get_data(self):
        pools_by_protocol = defaultdict(list)
        for pool in POOLS[self.chain].values():
            pools_by_protocol[pool["protocol"]].append(pool["address"])

        dex_clients = [
            DexPriceData(protocol, self.chain, pools)
            for protocol, pools in pools_by_protocol.items()
        ]

        await asyncio.gather(*[client.get_data() for client in dex_clients])

        chain_prices = {}
        for protocol_client in dex_clients:
            chain_prices[protocol_client.protocol] = {
                pool.pop("id"): pool for pool in protocol_client.data
            }
        self.chain_prices = chain_prices

    async def get_token_prices(self):
        await self._get_data()
        token_pricing = {}
        for token, path in POOL_PATHS[self.chain].items():
            price = 1
            for pool in path:
                pool_address = pool[0]["address"]
                pool_protocol = pool[0]["protocol"]
                pool_info = self.chain_prices[pool_protocol].get(pool_address)

                if not pool_info:
                    price = 0
                    break

                sqrt_price_x96 = float(pool_info["sqrtPrice"])
                decimal0 = int(pool_info["token0"]["decimals"])
                decimal1 = int(pool_info["token1"]["decimals"])

                token_in_base = sqrtPriceX96_to_priceDecimal(
                    sqrt_price_x96, decimal0, decimal1
                )
                if pool[1] == 0:
                    token_in_base = 1 / token_in_base

                price *= token_in_base

            token_pricing[token] = price

        self.token_prices = token_pricing


async def gamma_price():
    dex_pricing = DexPrice(Chain.MAINNET)
    await dex_pricing.get_token_prices()
    return dex_pricing.token_prices["0x6bea7cfef803d1e3d5f7c0103f7ded065644e197"]


async def token_prices(chain: Chain):
    dex_pricing = DexPrice(chain)
    await dex_pricing.get_token_prices()
    prices = dex_pricing.token_prices

    # Stop gap until refactoring to get multichain prices
    if chain != Chain.MAINNET:
        dex_pricing_mainnet = DexPrice(Chain.MAINNET)
        await dex_pricing_mainnet.get_token_prices()

        AXL_MAINNET = "0x467719ad09025fcc6cf6f8311755809d45a5e5f3"
        AXL_POLYGON = "0x6e4e624106cb12e168e6533f8ec7c82263358940"

        for token, price in dex_pricing_mainnet.token_prices.items():
            if token not in prices:
                if token == AXL_MAINNET:
                    prices[AXL_POLYGON] = price
                prices[token] = price

    llama_client = LlamaClient(Chain.MAINNET)
    try:
        ALCX_ADDRESS = "0xdbdb4d16eda451d0503b854cf79d55697f90c8df"
        prices[ALCX_ADDRESS] = await llama_client.current_token_price(ALCX_ADDRESS)
    except Exception:
        pass

    return prices
