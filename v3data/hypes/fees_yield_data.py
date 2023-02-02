import asyncio
from datetime import timedelta

from v3data import GammaClient, DexFeeGrowthClient, LlamaClient
from v3data.utils import timestamp_ago, estimate_block_from_timestamp_diff
from v3data.constants import BLOCK_TIME_SECONDS


class YieldData:
    def __init__(
        self,
        period_days,
        protocol: str,
        chain: str = "mainnet",
        delay_buffer_seconds: int = 3600,
    ):
        self.period_days = period_days
        self.protocol = protocol
        self.chain = chain
        self.gamma_client = GammaClient(protocol, chain)
        self.uniswap_client = DexFeeGrowthClient(protocol, chain)
        self.llama_client = LlamaClient(chain)
        self.delay_buffer_seconds = (
            delay_buffer_seconds  # Buffer to account for subgraph being slightly behind
        )
        self._block_ts_map = {}
        self._transition_data = {}
        self._hypervisor_data_by_blocks = {}
        self._pool_data = {}
        self.data = {}

    async def _get_hypervisor_data_at_block(self, block, hypervisors):
        query = """
        query hypervisor($block: Int!, $ids: [String!]!){
            uniswapV3Hypervisors(
                block: {
                    number: $block
                }
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

        variables = {"block": int(block), "ids": hypervisors}

        response = await self.gamma_client.query(query, variables)

        return response

    async def _get_transition_data(self, period_days):
        transition_query = """
        query transitions($timestamp_start: Int!, $timestamp_end: Int!){
            uniswapV3Hypervisors(
                first: 1000
            ){
                id
                withdraws(
                    where: {
                        timestamp_gt: $timestamp_start
                        timestamp_lt: $timestamp_end
                    }
                ) {
                    block
                    timestamp
                }
                rebalances(
                    where: {
                        timestamp_gt: $timestamp_start
                        timestamp_lt: $timestamp_end
                    }
                ) {
                    block
                    timestamp
                }
                deposits(
                    where: {
                        timestamp_gt: $timestamp_start
                        timestamp_lt: $timestamp_end
                    }
                ) {
                    block
                    timestamp
                }
            }
            _meta {
                block {
                    number
                }
            }
        }
        """

        variables = {
            "timestamp_start": timestamp_ago(
                timedelta(days=period_days)
                + timedelta(seconds=self.delay_buffer_seconds)
            ),
            "timestamp_end": timestamp_ago(
                timedelta(seconds=self.delay_buffer_seconds)
            ),
        }
        response = await self.gamma_client.query(transition_query, variables)

        self._transition_data = response["data"]

    async def _get_fee_update_data(self, period_days):
        query = """
        query transitions($timestamp_start: Int!, $timestamp_end: Int!){
            uniswapV3Hypervisors(first: 1000) {
                id
                feeUpdates(
                    where: {
                        timestamp_gt: $timestamp_start
                        timestamp_lt: $timestamp_end}
                ) {
                    block
                    timestamp
                }
            }
            _meta {
                block {
                    number
                }
            }
        }
        """

        variables = {
            "timestamp_start": timestamp_ago(
                timedelta(days=period_days)
                + timedelta(seconds=self.delay_buffer_seconds)
            ),
            "timestamp_end": timestamp_ago(
                timedelta(seconds=self.delay_buffer_seconds)
            ),
        }
        response = await self.gamma_client.query(query, variables)

        self._transition_data = response["data"]

    async def _get_pool_data_at_block(
        self, block, pool_address, base_lower, base_upper, limit_lower, limit_upper
    ):
        pool_query = """
        query pool(
            $block: Int!
            $poolAddress: String!
            $baseLower: Int!
            $baseUpper: Int!
            $limitLower: Int!
            $limitUpper: Int!
        ){
            pool(
                id: $poolAddress
                block: {number: $block}
            ){
                id
                tick
                feeGrowthGlobal0X128
                feeGrowthGlobal1X128
            }
            baseLower: ticks(
                block: {number: $block}
                where: {
                pool: $poolAddress
                tickIdx: $baseLower
                }
            ){
                tickIdx
                feeGrowthOutside0X128
                feeGrowthOutside1X128
            },
            baseUpper: ticks(
                block: {number: $block}
                where: {
                pool: $poolAddress
                tickIdx: $baseUpper
                }
            ){
                tickIdx
                feeGrowthOutside0X128
                feeGrowthOutside1X128
            },
            limitLower: ticks(
                block: {number: $block}
                where: {
                pool: $poolAddress
                tickIdx: $limitLower
                }
            ){
                tickIdx
                feeGrowthOutside0X128
                feeGrowthOutside1X128
            },
            limitUpper: ticks(
                block: {number: $block}
                where: {
                pool: $poolAddress
                tickIdx: $limitUpper
                }
            ){
                tickIdx
                feeGrowthOutside0X128
                feeGrowthOutside1X128
            }
        }
        """

        variables = {
            "block": int(block),
            "poolAddress": pool_address,
            "baseLower": base_lower,
            "baseUpper": base_upper,
            "limitLower": limit_lower,
            "limitUpper": limit_upper,
        }

        response = await self.uniswap_client.query(pool_query, variables)

        return response["data"]

    async def _get_block_timestamps(self):
        initial_timestamp = timestamp_ago(timedelta(days=self.period_days))
        current_timestamp = timestamp_ago(
            timedelta(seconds=self.delay_buffer_seconds)
        )  # Buffer as subgraph may not be indexed to latest
        initial_block, current_block = await asyncio.gather(
            self.llama_client.block_from_timestamp(initial_timestamp),
            self.llama_client.block_from_timestamp(current_timestamp),
        )

        if not current_block:
            current_block = (
                int(self._transition_data["_meta"]["block"]["number"])
                - self.delay_buffer_seconds // BLOCK_TIME_SECONDS[self.chain]
            )

        if not initial_block:
            initial_block = estimate_block_from_timestamp_diff(
                self.chain, current_block, current_timestamp, initial_timestamp
            )

        return {
            "initial": {"block": initial_block, "timestamp": initial_timestamp},
            "current": {"block": current_block, "timestamp": current_timestamp},
        }

    async def _get_hypervisor_data_for_all_blocks(
        self,
        initial_block: int,
        initial_timestamp: int,
        current_block: int,
        current_timestamp: int,
    ):
        # Identify which hypes need to be queried at specific blocks
        block_hypervisor_map = {initial_block: [], current_block: []}
        block_ts_map = {
            initial_block: initial_timestamp,
            current_block: current_timestamp,
        }
        for hypervisor in self._transition_data["uniswapV3Hypervisors"]:
            block_hypervisor_map[initial_block].append(hypervisor["id"])
            block_hypervisor_map[current_block].append(hypervisor["id"])

            if self.protocol == "quickswap":
                tx_types = ["feeUpdates"]
            else:
                tx_types = ["deposits", "withdraws", "rebalances"]

            for tx_type in tx_types:
                for tx in hypervisor[tx_type]:

                    tx_block = int(tx["block"])
                    tx_block_prev = tx_block - 1

                    if tx_block < initial_block:
                        continue

                    block_ts_map[tx_block] = int(tx["timestamp"])
                    block_ts_map[tx_block_prev] = int(
                        int(tx["timestamp"]) - BLOCK_TIME_SECONDS[self.chain]
                    )

                    if not block_hypervisor_map.get(tx_block):
                        block_hypervisor_map[tx_block] = []
                    block_hypervisor_map[tx_block].append(hypervisor["id"])

                    if not block_hypervisor_map.get(tx_block_prev):
                        block_hypervisor_map[tx_block_prev] = []
                    block_hypervisor_map[tx_block_prev].append(hypervisor["id"])

        self._block_ts_map = block_ts_map

        # Build hypervisor queries and execute
        hypervisor_query_params = [
            {"block": block, "hypervisors": hypervisors}
            for block, hypervisors in block_hypervisor_map.items()
        ]
        hypervisors_requests = [
            self._get_hypervisor_data_at_block(params["block"], params["hypervisors"])
            for params in hypervisor_query_params
        ]
        hypervisor_responses = await asyncio.gather(*hypervisors_requests)

        self._hypervisor_data_by_blocks = {
            hypervisor_query_params[index]["block"]: response["data"][
                "uniswapV3Hypervisors"
            ]
            for index, response in enumerate(hypervisor_responses)
        }

    async def _get_pool_data_for_all_blocks(self):
        pool_query_params = [
            {"block": block, "hypervisor": hypervisor}
            for block, hypervisors in self._hypervisor_data_by_blocks.items()
            for hypervisor in hypervisors
        ]

        pool_requests = [
            self._get_pool_data_at_block(
                int(params["block"]),
                params["hypervisor"]["pool"]["id"],
                params["hypervisor"]["baseLower"],
                params["hypervisor"]["baseUpper"],
                params["hypervisor"]["limitLower"],
                params["hypervisor"]["limitUpper"],
            )
            for params in pool_query_params
            if params["hypervisor"].get("pool", {}).get("id")
        ]

        pool_responses = await asyncio.gather(*pool_requests)

        self._pool_data = {
            self.tick_id(
                pool_query_params[index]["block"],
                response["pool"]["id"],
                response["baseLower"][0]["tickIdx"] if response["baseLower"] else 0,
                response["baseUpper"][0]["tickIdx"] if response["baseUpper"] else 0,
                response["limitLower"][0]["tickIdx"] if response["limitLower"] else 0,
                response["limitUpper"][0]["tickIdx"] if response["limitUpper"] else 0,
            ): response
            for index, response in enumerate(pool_responses)
            if response.get("pool", {}).get("id")
        }

    async def get_data(self):
        # Get transition data to identify blocks for making time-travel query
        if self.protocol == "quickswap":
            await self._get_fee_update_data(self.period_days)
        else:
            await self._get_transition_data(self.period_days)

        # Get initial and current blocks and timestamps
        edge_block_ts = await self._get_block_timestamps()
        initial_block = edge_block_ts["initial"]["block"]
        initial_timestamp = edge_block_ts["initial"]["timestamp"]
        current_block = edge_block_ts["current"]["block"]
        current_timestamp = edge_block_ts["current"]["timestamp"]

        # Identify which hypes need to be queried at specific blocks
        await self._get_hypervisor_data_for_all_blocks(
            initial_block,
            initial_timestamp,
            current_block,
            current_timestamp,
        )

        # Make corresponding pool queries for tick data
        await self._get_pool_data_for_all_blocks()

        # Reshape hype + pool data into something useful
        all_data = {}
        for block, hypervisors_in_block in self._hypervisor_data_by_blocks.items():
            for hypervisor in hypervisors_in_block:
                if not all_data.get(hypervisor["id"]):
                    all_data[hypervisor["id"]] = {}

                hypervisor.update(
                    {
                        "ticks": self._pool_data.get(
                            self.tick_id(
                                int(block),
                                hypervisor["pool"]["id"],
                                hypervisor["baseLower"],
                                hypervisor["baseUpper"],
                                hypervisor["limitLower"],
                                hypervisor["limitUpper"],
                            )
                        ),
                        "timestamp": self._block_ts_map.get(block, 0),
                    }
                )
                all_data[hypervisor["id"]][block] = hypervisor

        self.data = {
            "initial_block": initial_block,
            "initial_ts": self._block_ts_map[initial_block],
            "current_block": current_block,
            "current_ts": current_timestamp,
            "hype_data": all_data,
        }

    @staticmethod
    def tick_id(
        block: int,
        address: str,
        baseLower: int,
        baseUpper: int,
        limitLower: int,
        limitUpper: int,
    ):
        return f"{block}_{address}_{baseLower}_{baseUpper}_{limitLower}_{limitUpper}"
