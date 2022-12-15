from v3data import UniswapV3Client
from v3data.utils import sqrtPriceX96_to_priceDecimal


class UniV3PriceData:
    """Class for querying GAMMA related data"""

    def __init__(self, pool: str, chain: str = "mainnet"):
        self.uniswap_client = UniswapV3Client("uniswap_v3", chain)
        self.pool = pool
        # self.pool = "0x4006bed7bf103d70a1c6b7f1cef4ad059193dc25"  # GAMMA/WETH 0.3% pool
        self.data = {}

    async def _get_data(self):
        query = """
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
        variables = {"id": self.pool}
        response = await self.uniswap_client.query(query, variables)
        self.data = response["data"]


class QuickswapV3PriceData:
    """Class for querying GAMMA related data"""

    def __init__(self, pool: str, chain: str = "polygon"):
        self.uniswap_client = UniswapV3Client("quickswap", chain)
        self.pool = pool
        self.data = {}

    async def _get_data(self):
        query = """
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
        variables = {"id": self.pool}
        response = await self.uniswap_client.query(query, variables)
        self.data = response["data"]


class UniV3Price:
    def __init__(self, chain, protocol, pool_address):
        if protocol == "uniswap_v3":
            self.data = UniV3PriceData(pool_address, chain)
        elif protocol == "quickswap":
            self.data = QuickswapV3PriceData(pool_address, chain)

    async def output(self, inverse=False):
        await self.data._get_data()
        sqrt_priceX96 = float(self.data.data["pool"]["sqrtPrice"])
        decimal0 = int(self.data.data["pool"]["token0"]["decimals"])
        decimal1 = int(self.data.data["pool"]["token1"]["decimals"])
        native_in_usdc = float(self.data.data["bundle"]["nativePriceUSD"])

        token_in_native = sqrtPriceX96_to_priceDecimal(
            sqrt_priceX96, decimal0, decimal1
        )
        if inverse:
            token_in_native = 1 / token_in_native

        return {
            "token_in_usdc": token_in_native * native_in_usdc,
            "token_in_native": token_in_native,
        }


async def token_price(token: str):
    if token == "GAMMA":
        pool_address = "0x4006bed7bf103d70a1c6b7f1cef4ad059193dc25"
    else:
        return None

    pricing = UniV3Price("mainnet", "uniswap_v3", pool_address)
    return await pricing.output()


async def token_price_from_address(chain: str, token_address: str):
    pool_config = {
        "mainnet": {
            "0xd33526068d116ce69f19a9ee46f0bd304f21a51f": {
                "protocol": "uniswap_v3",
                "pool_address": "0xe42318ea3b998e8355a3da364eb9d48ec725eb45",
                "inverse": True,
            }
        },
        "optimism": {
            "0x4200000000000000000000000000000000000042": {
                "protocol": "uniswap_v3",
                "pool_address": "0x68f5c0a2de713a54991e01858fd27a3832401849",
                "inverse": True,
            },
            "0x601e471de750cdce1d5a2b8e6e671409c8eb2367": {
                "protocol": "uniswap_v3",
                "pool_address": "0x68f5c0a2de713a54991e01858fd27a3832401849",
                "inverse": True,
            },
        },
        "polygon": {
            "0x580a84c73811e1839f75d86d75d88cca0c241ff4": {
                "protocol": "quickswap",
                "pool_address": "0x5cd94ead61fea43886feec3c95b1e9d7284fdef3",  # WMATC/QI
                "inverse": True,
            },
            "0xb5c064f955d8e7f38fe0460c556a72987494ee17": {
                "protocol": "quickswap",
                "pool_address": "0x9f1a8caf3c8e94e43aa64922d67dff4dc3e88a42",  # WMATC/QUICK
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
