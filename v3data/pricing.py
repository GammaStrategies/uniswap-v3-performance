from v3data import UniswapV3Client
from v3data.utils import sqrtPriceX96_to_priceDecimal


class UniV3PriceData:
    """Class for querying GAMMA related data"""

    def __init__(self, pool: str, chain: str = "mainnet"):
        self.uniswap_client = UniswapV3Client(chain)
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
    async def output(self):
        await self._get_data()
        sqrt_priceX96 = float(self.data["pool"]["sqrtPrice"])
        decimal0 = int(self.data["pool"]["token0"]["decimals"])
        decimal1 = int(self.data["pool"]["token1"]["decimals"])
        eth_in_usdc = float(self.data["bundle"]["ethPriceUSD"])

        token_in_eth = sqrtPriceX96_to_priceDecimal(sqrt_priceX96, decimal0, decimal1)

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
