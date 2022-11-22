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
                ethPriceUSD
            }
        }
        """
        variables = {"id": self.pool}
        response = await self.uniswap_client.query(query, variables)
        self.data = response["data"]


class UniV3Price(UniV3PriceData):
    async def output(self, inverse=False):
        await self._get_data()
        sqrt_priceX96 = float(self.data["pool"]["sqrtPrice"])
        decimal0 = int(self.data["pool"]["token0"]["decimals"])
        decimal1 = int(self.data["pool"]["token1"]["decimals"])
        eth_in_usdc = float(self.data["bundle"]["ethPriceUSD"])

        token_in_eth = sqrtPriceX96_to_priceDecimal(sqrt_priceX96, decimal0, decimal1)
        if inverse:
            token_in_eth = 1 / token_in_eth

        return {
            "token_in_usdc": token_in_eth * eth_in_usdc,
            "token_in_eth": token_in_eth,
        }


async def token_price(token: str):
    if token == "GAMMA":
        pool_address = "0x4006bed7bf103d70a1c6b7f1cef4ad059193dc25"
    else:
        return None

    pricing = UniV3Price(pool_address, "mainnet")
    return await pricing.output()


async def token_price_from_address(chain: str, token_address: str):
    inverse = False
    pool_address = None

    if chain == "mainnet":
        if token_address == "0xd33526068d116ce69f19a9ee46f0bd304f21a51f":
            pool_address = "0xe42318ea3b998e8355a3da364eb9d48ec725eb45"
            inverse = True

    if chain == "optimism":
        if token_address == "0x4200000000000000000000000000000000000042":
            pool_address = "0x68f5c0a2de713a54991e01858fd27a3832401849"
            inverse = True
        elif token_address == "0x601e471de750cdce1d5a2b8e6e671409c8eb2367":
            pool_address = "0x68f5c0a2de713a54991e01858fd27a3832401849"
            inverse = True

    if pool_address:
        pricing = UniV3Price(pool_address, chain)
        price = await pricing.output(inverse=inverse)
    else:
        price = {
            "token_in_usdc": 0,
            "token_in_eth": 0,
        }
    return price
