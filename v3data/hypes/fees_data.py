import asyncio
from dataclasses import dataclass

from v3data import GammaClient, UniswapV3Client
from v3data.utils import timestamp_ago


@dataclass
class PoolQueryParams:
    address: str
    baseLower: int
    baseUpper: int
    limitLower: int
    limitUpper: int


class FeesData:
    def __init__(self, chain: str = "mainnet"):
        self.chain = chain
        self.gamma_client = GammaClient(chain)
        self.uniswap_client = UniswapV3Client(chain)
        self.data = {}

    async def _get_hypervisor_data(self, hypervisors=None):
        hypervisor_list_query = """
        query hypervisor($ids: [String!]!){
            uniswapV3Hypervisors(
                where: {
                    id_in: $ids
                }
            ){
                id
                symbol
                pool{
                    id
                    token0 {decimals}
                    token1 {decimals}
                }
                baseLiquidity
                baseLower
                baseUpper
                baseTokensOwed0
                baseTokensOwed1
                baseFeeGrowthInside0LastX128
                baseFeeGrowthInside1LastX128
                limitLiquidity
                limitLower
                limitUpper
                limitTokensOwed0
                limitTokensOwed1
                limitFeeGrowthInside0LastX128
                limitFeeGrowthInside1LastX128
                conversion {
                    baseTokenIndex
                    priceTokenInBase
                    priceBaseInUSD
                }
                tvlUSD
            }
        }
        """

        hypervisor_all_query = """
        {
            uniswapV3Hypervisors(
                first: 1000
            ){
                id
                symbol
                pool{
                    id
                    token0 {decimals}
                    token1 {decimals}
                }
                baseLiquidity
                baseLower
                baseUpper
                baseTokensOwed0
                baseTokensOwed1
                baseFeeGrowthInside0LastX128
                baseFeeGrowthInside1LastX128
                limitLiquidity
                limitLower
                limitUpper
                limitTokensOwed0
                limitTokensOwed1
                limitFeeGrowthInside0LastX128
                limitFeeGrowthInside1LastX128
                conversion {
                    baseTokenIndex
                    priceTokenInBase
                    priceBaseInUSD
                }
                tvlUSD
            }
        }
        """

        if hypervisors:
            variables = {"ids": [hypervisor.lower() for hypervisor in hypervisors]}
            response = await self.gamma_client.query(hypervisor_list_query, variables)
        else:
            response = await self.gamma_client.query(hypervisor_all_query)

        return {
            hypervisor["id"]: hypervisor
            for hypervisor in response["data"]["uniswapV3Hypervisors"]
        }

    async def _get_pool_data(self, pools_params: list[PoolQueryParams]):
        pool_query = """
        query pool(
            $poolAddress: String!
            $baseLower: Int!
            $baseUpper: Int!
            $limitLower: Int!
            $limitUpper: Int!
        ){
            pool(id: $poolAddress){
                id
                tick
                feeGrowthGlobal0X128
                feeGrowthGlobal1X128
            }
            baseLower: ticks(
                where: {
                poolAddress: $poolAddress
                tickIdx: $baseLower
                }
            ){
                tickIdx
                feeGrowthOutside0X128
                feeGrowthOutside1X128
            },
            baseUpper: ticks(
                where: {
                poolAddress: $poolAddress
                tickIdx: $baseUpper
                }
            ){
                tickIdx
                feeGrowthOutside0X128
                feeGrowthOutside1X128
            },
            limitLower: ticks(
                where: {
                poolAddress: $poolAddress
                tickIdx: $limitLower
                }
            ){
                tickIdx
                feeGrowthOutside0X128
                feeGrowthOutside1X128
            },
            limitUpper: ticks(
                where: {
                poolAddress: $poolAddress
                tickIdx: $limitUpper
                }
            ){
                tickIdx
                feeGrowthOutside0X128
                feeGrowthOutside1X128
            }
        }
        """

        pool_requests = [
            self.uniswap_client.query(
                pool_query,
                {
                    "poolAddress": params.address,
                    "baseLower": params.baseLower,
                    "baseUpper": params.baseUpper,
                    "limitLower": params.limitLower,
                    "limitUpper": params.limitUpper,
                },
            )
            for params in pools_params
        ]

        responses = await asyncio.gather(*pool_requests)

        return {
            self.tick_id(
                response["data"]["pool"]["id"],
                response["data"]["baseLower"][0]["tickIdx"]
                if response["data"]["baseLower"]
                else 0,
                response["data"]["baseUpper"][0]["tickIdx"]
                if response["data"]["baseUpper"]
                else 0,
                response["data"]["limitLower"][0]["tickIdx"]
                if response["data"]["limitLower"]
                else 0,
                response["data"]["limitUpper"][0]["tickIdx"]
                if response["data"]["limitUpper"]
                else 0,
            ): response["data"]
            for response in responses
            if response["data"].get("pool", {}).get("id")
        }

    async def _get_data(self, hypervisors=None):
        hypervisor_data = await self._get_hypervisor_data(hypervisors)

        pools_params = [
            PoolQueryParams(
                hypervisor["pool"]["id"],
                hypervisor["baseLower"],
                hypervisor["baseUpper"],
                hypervisor["limitLower"],
                hypervisor["limitUpper"],
            )
            for hypervisor in hypervisor_data.values()
        ]

        tick_data = await self._get_pool_data(pools_params)

        data = []
        for hypervisor in hypervisor_data.values():
            hypervisor.update(
                {
                    "ticks": tick_data.get(
                        self.tick_id(
                            hypervisor["pool"]["id"],
                            hypervisor["baseLower"],
                            hypervisor["baseUpper"],
                            hypervisor["limitLower"],
                            hypervisor["limitUpper"],
                        )
                    )
                }
            )
            data.append(hypervisor)

        self.data = data

    @staticmethod
    def tick_id(
        address: str, baseLower: int, baseUpper: int, limitLower: int, limitUpper: int
    ):
        return f"{address}_{baseLower}_{baseUpper}_{limitLower}_{limitLower}"
