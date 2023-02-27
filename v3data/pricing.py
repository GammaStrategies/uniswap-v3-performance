from abc import ABC, abstractmethod

from v3data import UniswapV3Client
from v3data.utils import sqrtPriceX96_to_priceDecimal
from v3data.enums import Chain, Protocol


class DexPriceData(ABC):
    """Base class for dex prices"""

    def __init__(self, protocol: Protocol, pool: str, chain: Chain) -> None:
        self.uniswap_client = UniswapV3Client(protocol, chain)
        self.pool = pool
        self.pool_query = ""
        self.native_query = ""
        self.pool_data = {}
        self.native_data = {}

    @abstractmethod
    def _init_queries(self):
        """Set queries"""
        # self.pool_query = ""
        # self.native_query = ""
        pass

    async def _get_data(self):
        self._init_queries()
        if self.pool == "native":
            await self._get_native_data()
        else:
            await self._get_pool_data()

    async def _get_pool_data(self):
        variables = {"id": self.pool}
        response = await self.uniswap_client.query(self.pool_query, variables)
        self.pool_data = response["data"]["pool"]
        self.native_data = response["data"]["bundle"]

    async def _get_native_data(self):
        response = await self.uniswap_client.query(self.native_query)
        self.native_data = response["data"]["bundle"]


class UniV3PriceData(DexPriceData):
    """Class for querying GAMMA related data"""

    def __init__(self, pool: str, chain: Chain = Chain.MAINNET):
        super().__init__(Protocol.UNISWAP, pool, chain)

    def _init_queries(self):
        self.pool_query = """
        query tokenPrice($id: String!){
            pool(
                id: $id
            ){
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
            bundle(id:1){
                nativePriceUSD: ethPriceUSD
            }
        }
        """

        self.native_query = """
        query nativePrice{
            bundle(id:1){
                nativePriceUSD: ethPriceUSD
            }
        }
        """


class QuickswapV3PriceData(DexPriceData):
    """Class for querying quickswap price data"""

    def __init__(self, pool: str, chain: Chain = Chain.MAINNET):
        super().__init__(Protocol.QUICKSWAP, pool, chain)

    def _init_queries(self):
        self.pool_query = """
        query tokenPrice($id: String!){
            pool(
                id: $id
            ){
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
            bundle(id:1){
                nativePriceUSD: maticPriceUSD
            }
        }
        """

        self.native_query = """
        query nativePrice{
            bundle(id:1){
                nativePriceUSD: maticPriceUSD
            }
        }
        """


class UniV3Price:
    def __init__(self, chain, protocol: Protocol, pool_address):
        if protocol == Protocol.UNISWAP:
            self.data = UniV3PriceData(pool_address, chain)
        elif protocol == Protocol.QUICKSWAP:
            self.data = QuickswapV3PriceData(pool_address, chain)

    async def output(self, inverse=False):
        await self.data._get_data()

        if self.data.pool_data:
            sqrt_priceX96 = float(self.data.pool_data["sqrtPrice"])
            decimal0 = int(self.data.pool_data["token0"]["decimals"])
            decimal1 = int(self.data.pool_data["token1"]["decimals"])

            token_in_native = sqrtPriceX96_to_priceDecimal(
                sqrt_priceX96, decimal0, decimal1
            )
            if inverse:
                token_in_native = 1 / token_in_native
        else:
            token_in_native = 1

        native_in_usdc = float(self.data.native_data["nativePriceUSD"])

        return {
            "token_in_usdc": token_in_native * native_in_usdc,
            "token_in_native": token_in_native,
        }


async def token_price(token: str):
    if token == "GAMMA":
        pool_address = "0x4006bed7bf103d70a1c6b7f1cef4ad059193dc25"
    else:
        return None

    pricing = UniV3Price(Chain.MAINNET, Protocol.UNISWAP, pool_address)
    return await pricing.output()


async def token_price_from_address(chain: Chain, token_address: str):
    pool_config = {
        Chain.MAINNET: {
            "0xd33526068d116ce69f19a9ee46f0bd304f21a51f": {
                "protocol": Protocol.UNISWAP,
                "pool_address": "0xe42318ea3b998e8355a3da364eb9d48ec725eb45",
                "inverse": True,
            }
        },
        Chain.OPTIMISM: {
            "0x4200000000000000000000000000000000000042": {
                "protocol": Protocol.UNISWAP,
                "pool_address": "0x68f5c0a2de713a54991e01858fd27a3832401849",
                "inverse": True,
            },
            "0x601e471de750cdce1d5a2b8e6e671409c8eb2367": {
                "protocol": Protocol.UNISWAP,
                "pool_address": "0x68f5c0a2de713a54991e01858fd27a3832401849",
                "inverse": True,
            },
        },
        Chain.POLYGON: {
            "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270": {  # WMATIC
                "protocol": Protocol.QUICKSWAP,
                "pool_address": "native",
                "inverse": False,
            },
            "0x580a84c73811e1839f75d86d75d88cca0c241ff4": {
                "protocol": Protocol.QUICKSWAP,
                "pool_address": "0x5cd94ead61fea43886feec3c95b1e9d7284fdef3",  # WMATIC/QI
                "inverse": True,
            },
            "0xb5c064f955d8e7f38fe0460c556a72987494ee17": {
                "protocol": Protocol.QUICKSWAP,
                "pool_address": "0x9f1a8caf3c8e94e43aa64922d67dff4dc3e88a42",  # WMATIC/QUICK
                "inverse": True,
            },
            "0x958d208cdf087843e9ad98d23823d32e17d723a1": {
                "protocol": Protocol.QUICKSWAP,
                "pool_address": "0xb8d00c66accdc01e78fd7957bf24050162916ae2",  # WMATIC/dQUICK
                "inverse": True,
            },
        },
    }

    config = pool_config.get(chain, {}).get(token_address, None)

    if config:
        pricing = UniV3Price(chain, config["protocol"], config["pool_address"])
        price = await pricing.output(inverse=config["inverse"])
    else:
        price = {
            "token_in_usdc": 0,
            "token_in_native": 0,
        }
    return price
