from abc import ABC, abstractmethod
from gql.dsl import DSLQuery

from v3data import LlamaClient
from v3data.constants import BLOCK_TIME_SECONDS, DAY_SECONDS
from v3data.hype_fees.schema import (
    FeesData,
    FeesDataRange,
    HypervisorStaticInfo,
    Time,
)
from v3data.utils import estimate_block_from_timestamp_diff
from v3data.enums import Chain, Protocol
from v3data.subgraphs.hype_pool import HypePoolClient
from v3data.data import BlockRange


class FeeGrowthDataABC(ABC):
    def __init__(self, protocol: Protocol, chain: Chain) -> None:
        self.protocol = protocol
        self.chain = chain
        self.hype_pool_client = HypePoolClient(protocol, chain)
        self.time_range = BlockRange(chain, self.hype_pool_client)
        self.data = {}
        self._static_data = {}

    @abstractmethod
    def init_time(self, *args, **kwargs) -> None:
        # Required to initialise initial and end times
        pass

    @abstractmethod
    def get_data(self) -> None:
        pass

    def _init_fees_data(
        self,
        hypervisor: dict,
        hypervisor_id: str,
        block: int,
        timestamp: int,
        current_tick: int,
        price_0: float,
        price_1: float,
        fee_growth_global_0: int,
        fee_growth_global_1: int,
    ) -> FeesData:
        return FeesData(
            block=block,
            timestamp=timestamp,
            hypervisor=hypervisor_id,
            symbol=self._static_data[hypervisor_id].symbol,
            currentTick=current_tick,
            price0=price_0,
            price1=price_1,
            decimals0=self._static_data[hypervisor_id].decimals.value0,
            decimals1=self._static_data[hypervisor_id].decimals.value1,
            tvl0=hypervisor["tvl0"],
            tvl1=hypervisor["tvl1"],
            tvl_usd=hypervisor["tvlUSD"],
            fee_growth_global0=fee_growth_global_0,
            fee_growth_global1=fee_growth_global_1,
            liquidity_base=hypervisor["basePosition"]["liquidity"],
            tokens_owed_base0=hypervisor["basePosition"]["tokensOwed0"],
            tokens_owed_base1=hypervisor["basePosition"]["tokensOwed1"],
            fee_growth_inside_base0=hypervisor["basePosition"]["feeGrowthInside0X128"],
            fee_growth_inside_base1=hypervisor["basePosition"]["feeGrowthInside1X128"],
            tick_index_lower_base=hypervisor["basePosition"]["tickLower"]["tickIdx"],
            fee_growth_outside_lower_base0=hypervisor["basePosition"]["tickLower"][
                "feeGrowthOutside0X128"
            ],
            fee_growth_outside_lower_base1=hypervisor["basePosition"]["tickLower"][
                "feeGrowthOutside1X128"
            ],
            tick_index_upper_base=hypervisor["basePosition"]["tickUpper"]["tickIdx"],
            fee_growth_outside_upper_base0=hypervisor["basePosition"]["tickUpper"][
                "feeGrowthOutside0X128"
            ],
            fee_growth_outside_upper_base1=hypervisor["basePosition"]["tickUpper"][
                "feeGrowthOutside1X128"
            ],
            liquidity_limit=hypervisor["limitPosition"]["liquidity"],
            tokens_owed_limit0=hypervisor["limitPosition"]["tokensOwed0"],
            tokens_owed_limit1=hypervisor["limitPosition"]["tokensOwed1"],
            fee_growth_inside_limit0=hypervisor["limitPosition"][
                "feeGrowthInside0X128"
            ],
            fee_growth_inside_limit1=hypervisor["limitPosition"][
                "feeGrowthInside1X128"
            ],
            tick_index_lower_limit=hypervisor["limitPosition"]["tickLower"]["tickIdx"],
            fee_growth_outside_lower_limit0=hypervisor["limitPosition"]["tickLower"][
                "feeGrowthOutside0X128"
            ],
            fee_growth_outside_lower_limit1=hypervisor["limitPosition"]["tickLower"][
                "feeGrowthOutside1X128"
            ],
            tick_index_upper_limit=hypervisor["limitPosition"]["tickUpper"]["tickIdx"],
            fee_growth_outside_upper_limit0=hypervisor["limitPosition"]["tickUpper"][
                "feeGrowthOutside0X128"
            ],
            fee_growth_outside_upper_limit1=hypervisor["limitPosition"]["tickUpper"][
                "feeGrowthOutside1X128"
            ],
            total_supply=hypervisor.get("totalSupply"),
            total_supply_decimals=18 if hypervisor.get("totalSupply") else 0,
        )

    def _extract_static_data(self, hypervisor_static_data: dict) -> None:
        self._static_data = {
            hypervisor["id"]: HypervisorStaticInfo(
                symbol=hypervisor["symbol"],
                decimals0=hypervisor["pool"]["token0"]["decimals"],
                decimals1=hypervisor["pool"]["token1"]["decimals"],
            )
            for hypervisor in hypervisor_static_data
        }


class FeeGrowthData(FeeGrowthDataABC):
    async def init_time(self, timestamp: int | None = None):
        await self.time_range.set_end(timestamp)

    async def get_data(self, hypervisors: list[str] | None = None) -> None:
        self.data = self._transform_data(await self._query_data(hypervisors))

    async def _query_data(self, hypervisors: list[str] | None = None) -> dict:
        ds = self.hype_pool_client.data_schema
        hypervisor_filter = {"where": {"id_in": hypervisors}} if hypervisors else {}

        query = DSLQuery(
            ds.Query.hypervisors(**hypervisor_filter)
            .alias("static")
            .select(
                ds.Hypervisor.id,
                ds.Hypervisor.symbol,
                ds.Hypervisor.pool.select(
                    ds.Pool.token0.select(ds.Token.decimals),
                    ds.Pool.token1.select(ds.Token.decimals),
                ),
            ),
            ds.Query.hypervisors(
                **({"block": {"number": self.time_range.end.block}} | hypervisor_filter)
            ).select(self.hype_pool_client.hypervisor_fields_fragment()),
            ds.Query._meta.select(self.hype_pool_client.meta_fields_fragment()),
        )

        response = await self.hype_pool_client.execute(query)
        return response

    def _transform_data(self, query_data) -> dict[str, FeesData]:
        self._extract_static_data(query_data["static"])
        return {
            hypervisor["id"]: self._init_fees_data(
                hypervisor=hypervisor,
                hypervisor_id=hypervisor["id"],
                block=query_data["_meta"]["block"]["number"],
                timestamp=query_data["_meta"]["block"]["timestamp"],
                current_tick=hypervisor["pool"]["currentTick"],
                price_0=hypervisor["pool"]["token0"]["priceUSD"],
                price_1=hypervisor["pool"]["token1"]["priceUSD"],
                fee_growth_global_0=hypervisor["pool"]["feeGrowthGlobal0X128"],
                fee_growth_global_1=hypervisor["pool"]["feeGrowthGlobal1X128"],
            )
            for hypervisor in query_data["hypervisors"]
        }


class FeeGrowthSnapshotData(FeeGrowthDataABC):
    """Get fee growth data from fee growth subgraph"""

    async def init_time(self, days_ago: int, end_timestamp: int | None = None):
        await self.time_range.set_end(end_timestamp)
        await self.time_range.set_initial_with_days_ago(days_ago)

    async def get_data(self, hypervisors: list[str] | None = None) -> None:
        """Query data and tranfrom to FeesData Class"""
        self.data = self._transform_data(await self._query_data(hypervisors))

    async def _query_data(self, hypervisors: list[str] | None = None) -> dict:
        ds = self.hype_pool_client.data_schema
        hypervisor_filter = {"where": {"id_in": hypervisors}} if hypervisors else {}

        query = DSLQuery(
            ds.Query.hypervisors(**hypervisor_filter)
            .alias("static")
            .select(
                ds.Hypervisor.id,
                ds.Hypervisor.symbol,
                ds.Hypervisor.pool.select(
                    ds.Pool.token0.select(ds.Token.decimals),
                    ds.Pool.token1.select(ds.Token.decimals),
                ),
            ),
            ds.Query.hypervisors(
                **({"block": {"number": self.time_range.end.block}} | hypervisor_filter)
            )
            .alias("latest")
            .select(self.hype_pool_client.hypervisor_fields_fragment()),
            ds.Query.hypervisors(
                **(
                    {"block": {"number": self.time_range.initial.block}}
                    | hypervisor_filter
                )
            )
            .alias("initial")
            .select(self.hype_pool_client.hypervisor_fields_fragment()),
            ds.Query.hypervisors(**hypervisor_filter)
            .alias("snapshots")
            .select(
                ds.Hypervisor.id,
                ds.Hypervisor.feeSnapshots(
                    first=1000,
                    where={
                        "timestamp_gte": self.time_range.initial.timestamp,
                        "timestamp_lte": self.time_range.end.timestamp,
                    },
                ).select(
                    ds.FeeSnapshot.blockNumber,
                    ds.FeeSnapshot.timestamp,
                    ds.FeeSnapshot.currentBlock.select(
                        self.hype_pool_client.block_snapshot_fields_fragment()
                    ),
                    ds.FeeSnapshot.previousBlock.select(
                        self.hype_pool_client.block_snapshot_fields_fragment()
                    ),
                ),
            ),
            ds.Query._meta.select(self.hype_pool_client.meta_fields_fragment()),
        )

        response = await self.hype_pool_client.execute(query)
        return response

    def _transform_data(self, query_data: dict) -> dict[str, list[FeesData]]:
        transformed_data = {}
        self._extract_static_data(query_data["static"])
        # Add latest row
        for hypervisor_latest in query_data["latest"]:
            transformed_data[hypervisor_latest["id"]] = [
                self._init_fees_data(
                    hypervisor=hypervisor_latest,
                    hypervisor_id=hypervisor_latest["id"],
                    block=query_data["_meta"]["block"]["number"],
                    timestamp=query_data["_meta"]["block"]["timestamp"],
                    current_tick=hypervisor_latest["pool"]["currentTick"],
                    price_0=hypervisor_latest["pool"]["token0"]["priceUSD"],
                    price_1=hypervisor_latest["pool"]["token1"]["priceUSD"],
                    fee_growth_global_0=hypervisor_latest["pool"][
                        "feeGrowthGlobal0X128"
                    ],
                    fee_growth_global_1=hypervisor_latest["pool"][
                        "feeGrowthGlobal1X128"
                    ],
                )
            ]

        # Add initial row
        for hypervisor_initial in query_data["initial"]:
            if not transformed_data.get(hypervisor_initial["id"]):
                continue

            transformed_data[hypervisor_initial["id"]].append(
                self._init_fees_data(
                    hypervisor=hypervisor_initial,
                    hypervisor_id=hypervisor_initial["id"],
                    block=self.time_range.initial.block,
                    timestamp=self.time_range.initial.timestamp,
                    current_tick=hypervisor_initial["pool"]["currentTick"],
                    price_0=hypervisor_initial["pool"]["token0"]["priceUSD"],
                    price_1=hypervisor_initial["pool"]["token1"]["priceUSD"],
                    fee_growth_global_0=hypervisor_initial["pool"][
                        "feeGrowthGlobal0X128"
                    ],
                    fee_growth_global_1=hypervisor_initial["pool"][
                        "feeGrowthGlobal1X128"
                    ],
                )
            )

        for hypervisor_snapshot in query_data["snapshots"]:
            for snapshot in hypervisor_snapshot["feeSnapshots"]:
                if not transformed_data.get(hypervisor_snapshot["id"]):
                    continue

                # Add current block
                current_block = snapshot["currentBlock"]
                transformed_data[hypervisor_snapshot["id"]].append(
                    self._init_fees_data(
                        hypervisor=current_block,
                        hypervisor_id=hypervisor_snapshot["id"],
                        block=snapshot["blockNumber"],
                        timestamp=snapshot["timestamp"],
                        current_tick=current_block["tick"],
                        price_0=current_block["price0"],
                        price_1=current_block["price1"],
                        fee_growth_global_0=current_block["feeGrowthGlobal0X128"],
                        fee_growth_global_1=current_block["feeGrowthGlobal1X128"],
                    )
                )
                # Add previous block
                previous_block = snapshot["previousBlock"]
                transformed_data[hypervisor_snapshot["id"]].append(
                    self._init_fees_data(
                        hypervisor=previous_block,
                        hypervisor_id=hypervisor_snapshot["id"],
                        block=int(snapshot["blockNumber"])
                        - 1,  # Previous block is 1 block before
                        timestamp=int(snapshot["timestamp"])
                        - BLOCK_TIME_SECONDS[self.chain],
                        current_tick=previous_block["tick"],
                        price_0=previous_block["price0"],
                        price_1=previous_block["price1"],
                        fee_growth_global_0=previous_block["feeGrowthGlobal0X128"],
                        fee_growth_global_1=previous_block["feeGrowthGlobal1X128"],
                    )
                )
        return transformed_data


class ImpermanentDivergenceData(FeeGrowthDataABC):
    async def init_time(self, days_ago: int, end_timestamp: int | None = None):
        await self.time_range.set_end(end_timestamp)
        await self.time_range.set_initial_with_days_ago(days_ago)

    async def get_data(self, hypervisors: list[str] | None = None) -> None:
        self.data = self._transform_data(await self._query_data(hypervisors))

    async def _query_data(self, hypervisors: list[str] | None = None) -> dict:
        ds = self.hype_pool_client.data_schema
        hypervisor_filter = {"where": {"id_in": hypervisors}} if hypervisors else {}
        query = DSLQuery(
            ds.Query.hypervisors(**hypervisor_filter)
            .alias("static")
            .select(
                ds.Hypervisor.id,
                ds.Hypervisor.symbol,
                ds.Hypervisor.pool.select(
                    ds.Pool.token0.select(ds.Token.decimals),
                    ds.Pool.token1.select(ds.Token.decimals),
                ),
            ),
            ds.Query.hypervisors(
                **({"block": {"number": self.time_range.end.block}} | hypervisor_filter)
            )
            .alias("latest")
            .select(self.hype_pool_client.hypervisor_fields_fragment()),
            ds.Query.hypervisors(
                **(
                    {"block": {"number": self.time_range.initial.block}}
                    | hypervisor_filter
                )
            )
            .alias("initial")
            .select(self.hype_pool_client.hypervisor_fields_fragment()),
            ds.Query._meta.select(self.hype_pool_client.meta_fields_fragment()),
        )

        response = await self.hype_pool_client.execute(query)
        return response

    def _transform_data(self, query_data: dict) -> dict[str, FeesDataRange]:
        self._extract_static_data(query_data["static"])

        # Transform list to dict for easier lookup in the next step
        initial_data = {hype["id"]: hype for hype in query_data["initial"]}

        transformed_data = {
            hypervisor_latest["id"]: FeesDataRange(
                initial=self._init_fees_data(
                    hypervisor=initial_data[hypervisor_latest["id"]],
                    hypervisor_id=initial_data[hypervisor_latest["id"]]["id"],
                    block=self.time_range.initial.block,
                    timestamp=self.time_range.initial.timestamp,
                    current_tick=initial_data[hypervisor_latest["id"]]["pool"][
                        "currentTick"
                    ],
                    price_0=initial_data[hypervisor_latest["id"]]["pool"]["token0"][
                        "priceUSD"
                    ],
                    price_1=initial_data[hypervisor_latest["id"]]["pool"]["token1"][
                        "priceUSD"
                    ],
                    fee_growth_global_0=initial_data[hypervisor_latest["id"]]["pool"][
                        "feeGrowthGlobal0X128"
                    ],
                    fee_growth_global_1=initial_data[hypervisor_latest["id"]]["pool"][
                        "feeGrowthGlobal1X128"
                    ],
                ),
                latest=self._init_fees_data(
                    hypervisor=hypervisor_latest,
                    hypervisor_id=hypervisor_latest["id"],
                    block=query_data["_meta"]["block"]["number"],
                    timestamp=query_data["_meta"]["block"]["timestamp"],
                    current_tick=hypervisor_latest["pool"]["currentTick"],
                    price_0=hypervisor_latest["pool"]["token0"]["priceUSD"],
                    price_1=hypervisor_latest["pool"]["token1"]["priceUSD"],
                    fee_growth_global_0=hypervisor_latest["pool"][
                        "feeGrowthGlobal0X128"
                    ],
                    fee_growth_global_1=hypervisor_latest["pool"][
                        "feeGrowthGlobal1X128"
                    ],
                ),
            )
            for hypervisor_latest in query_data["latest"]
            if initial_data.get(hypervisor_latest["id"])
        }

        return transformed_data
