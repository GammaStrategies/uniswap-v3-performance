from xmlrpc.client import Boolean
from v3data import UniswapV3Client


class SimulatorData:
    def __init__(self, chain: str) -> None:
        self.uniswap_client = UniswapV3Client(chain)

    async def _get_token_list(self, page: int = 0):
        query = """
        query tokens($skip: Int!){
            tokens(
                first: 1000
                skip: $skip
                orderBy: volumeUSD
                orderDirection: desc
            ) {
                id
                name
                symbol
                volumeUSD
                decimals
            }
        }
        """
        variables = {
            "skip": 1000 * page,
        }
        response = await self.uniswap_client.query(query, variables)
        self.token_data = response["data"]["tokens"]

    async def _get_pool_ticks(self, pool_address: str):
        query = """
        query ticks($poolAddress: String!){
            ticks(
                first: 1000
                where: {
                    poolAddress: $poolAddress
                }
                orderBy: tickIdx
            ) {
                tickIdx
                liquidityNet
                price0
                price1
            }
        }
        """
        variables = {
            "poolAddress": pool_address.lower(),
        }
        response = await self.uniswap_client.query(query, variables)
        self.tick_data = response["data"]["ticks"]

    async def _get_pool_from_tokens(self, token0: str, token1: str):
        query = """
        query pools($token0: String!, $token1: String!){
            pools(
                where: {
                    token0: $token0
                    token1: $token1
                }
                orderBy: feeTier
            ) {
                id
                tick
                sqrtPrice
                feeTier
                liquidity
                token0Price
                token1Price
            }
        }
        """
        variables = {
            "token0": token0,
            "token1": token1
        }
        response = await self.uniswap_client.query(query, variables)
        self.pool_data = response["data"]["pools"]

    async def _get_pool_24hr_volume(self, pool_address: str):
        query = """
        query poolVolume($poolAddress: String!){
            poolDayDatas(
                skip:1,
                first: 3
                where: { pool: $poolAddress }
                orderBy: date
                orderDirection: desc
            ) {
                volumeUSD
            }
        }
        """
        variables = {
            "poolAddress": pool_address
        }
        response = await self.uniswap_client.query(query, variables)
        self.volume_data = response["data"]["poolDayDatas"]


class SimulatorInfo(SimulatorData):
    async def token_list(self, page: int = 0, get_data: bool = True):
        if get_data:
            await self._get_token_list(page)

        return self.token_data

    async def pool_ticks(self, poolAddress: str, get_data: bool = True):
        if get_data:
            await self._get_pool_ticks(poolAddress)

        return self.tick_data

    async def pools_from_tokens(self, token0: str, token1: str, get_data: bool = True):
        if get_data:
            await self._get_pool_from_tokens(token0, token1)

        return self.pool_data

    async def pool_volume(self, poolAddress: str, get_data: bool = True):
        if get_data:
            await self._get_pool_24hr_volume(poolAddress)

        return self.volume_data

