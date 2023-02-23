from abc import ABC, abstractmethod

from v3data import HypePoolClient, LlamaClient
from v3data.constants import BLOCK_TIME_SECONDS, DAY_SECONDS
from v3data.hype_fees.schema import (
    FeesData,
    FeesDataRange,
    HypervisorStaticInfo,
    Time,
    _PositionData,
    _TickData,
    _TokenPair,
    _TokenPairDecimals,
)
from v3data.utils import estimate_block_from_timestamp_diff


class FeeGrowthDataABC(ABC):
    def __init__(self, protocol: str, chain: str) -> None:
        self.protocol = protocol
        self.chain = chain
        self.fee_growth_client = HypePoolClient(protocol, chain)
        self.data = {}
        self._static_data = {}

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
            hypervisor=hypervisor_id,
            symbol=self._static_data[hypervisor_id].symbol,
            block=block,  # set to block
            timestamp=timestamp,  # set to timestamp
            currentTick=current_tick,
            price=_TokenPairDecimals(price_0, price_1),
            decimals=_TokenPair(
                self._static_data[hypervisor_id].decimals.value0,
                self._static_data[hypervisor_id].decimals.value1,
            ),
            tvl=_TokenPair(hypervisor["tvl0"], hypervisor["tvl1"]),
            tvl_usd=hypervisor["tvlUSD"],
            fee_growth_global=_TokenPair(fee_growth_global_0, fee_growth_global_1),
            base_position=self._init_position_data(hypervisor, "basePosition"),
            limit_position=self._init_position_data(hypervisor, "limitPosition"),
        )

    def _init_position_data(
        self, hypervisor: dict, position_type: str
    ) -> _PositionData:
        return _PositionData(
            liquidity=hypervisor[position_type]["liquidity"],
            tokens_owed=_TokenPair(
                hypervisor[position_type]["tokensOwed0"],
                hypervisor[position_type]["tokensOwed1"],
            ),
            fee_growth_inside=_TokenPair(
                hypervisor[position_type]["feeGrowthInside0X128"],
                hypervisor[position_type]["feeGrowthInside1X128"],
            ),
            tick_lower=self._init_tick_data(hypervisor, position_type, "tickLower"),
            tick_upper=self._init_tick_data(hypervisor, position_type, "tickUpper"),
        )

    def _init_tick_data(
        self, hypervisor: dict, position_type: str, tick_type: str
    ) -> _TickData:
        return _TickData(
            tick_index=hypervisor[position_type][tick_type]["tickIdx"],
            fee_growth_outside=_TokenPair(
                hypervisor[position_type][tick_type]["feeGrowthOutside0X128"],
                hypervisor[position_type][tick_type]["feeGrowthOutside1X128"],
            ),
        )

    def _extract_static_data(self, hypervisor_static_data: dict) -> None:
        self._static_data = {
            hypervisor["id"]: HypervisorStaticInfo(
                symbol=hypervisor["symbol"],
                decimals=_TokenPair(
                    hypervisor["pool"]["token0"]["decimals"],
                    hypervisor["pool"]["token1"]["decimals"],
                ),
            )
            for hypervisor in hypervisor_static_data
        }


class FeeGrowthTemporalData(FeeGrowthDataABC):
    """Additional methods to manage time ranges"""

    def __init__(
        self,
        period_days,
        protocol: str,
        chain: str,
    ) -> None:
        self.period_days = period_days
        self.llama_client = LlamaClient(chain)
        super().__init__(protocol, chain)

    async def _init_start_time(self) -> None:
        self.end_time = await self._query_current_time()
        timestamp_start = self.end_time.timestamp - (self.period_days * DAY_SECONDS)
        response = await self.llama_client.block_from_timestamp(timestamp_start, True)

        if response:
            self.initial_time = Time(
                block=response["height"], timestamp=response["timestamp"]
            )
        else:
            # Estimate start time if not found
            self.initial_time = Time(
                block=estimate_block_from_timestamp_diff(
                    self.chain,
                    self.end_time.block,
                    self.end_time.timestamp,
                    timestamp_start,
                ),
                timestamp=timestamp_start,
            )

            self.initial_block = estimate_block_from_timestamp_diff(
                self.chain,
                self.end_time.block,
                self.end_time.timestamp,
                timestamp_start,
            )

    async def _query_current_time(self) -> Time:
        query = """
        {
            _meta {
                block {
                number
                timestamp
                }
            }
        }
        """

        response = await self.fee_growth_client.query(query)

        return Time(
            block=response["data"]["_meta"]["block"]["number"],
            timestamp=response["data"]["_meta"]["block"]["timestamp"],
        )


class FeeGrowthData(FeeGrowthDataABC):
    async def get_data(self) -> None:
        self.data = self._transform_data(await self._query_data())

    async def _query_data(self) -> dict:
        query = """
        query feeGrowth {
            static: hypervisors {
                id
                symbol
                pool {
                    token0 {
                        decimals
                    }
                    token1 {
                        decimals
                    }
                }
            }
            hypervisors {
                id
                tvl0
                tvl1
                tvlUSD
                pool {
                    currentTick
                    feeGrowthGlobal0X128
                    feeGrowthGlobal1X128
                    token0 {
                        priceUSD
                    }
                    token1 {
                        priceUSD
                    }
                }
                basePosition {
                    liquidity
                    tokensOwed0
                    tokensOwed1
                    feeGrowthInside0X128
                    feeGrowthInside1X128
                    tickLower {
                        tickIdx
                        feeGrowthOutside0X128
                        feeGrowthOutside1X128
                    }
                    tickUpper {
                        tickIdx
                        feeGrowthOutside0X128
                        feeGrowthOutside1X128
                    }
                }
                limitPosition {
                    liquidity
                    tokensOwed0
                    tokensOwed1
                    feeGrowthInside0X128
                    feeGrowthInside1X128
                    tickLower {
                        tickIdx
                        feeGrowthOutside0X128
                        feeGrowthOutside1X128
                    }
                    tickUpper {
                        tickIdx
                        feeGrowthOutside0X128
                        feeGrowthOutside1X128
                    }
                }
            }
            _meta {
                block {
                number
                timestamp
                }
            }
        }
        """

        response = await self.fee_growth_client.query(query)
        return response["data"]

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


class FeeGrowthSnapshotData(FeeGrowthTemporalData):
    """Get fee growth data from fee growth subgraph"""

    async def get_data(self) -> None:
        """Query data and tranfrom to FeesData Class"""
        await self._init_start_time()
        self.data = self._transform_data(await self._query_data())

    async def _query_data(self) -> dict:
        query = """
        query Snapshots(
            $blockStart: Int!
            $timestampStart: Int!
            $blockEnd: Int!
            $timestampEnd: Int!
        ) {
            static: hypervisors(block: {number: $blockEnd}) {
                id
                symbol
                pool {
                    token0 {
                        priceUSD
                        decimals
                    }
                    token1 {
                        priceUSD
                        decimals
                    }
                }
            }
            latest: hypervisors(block: {number: $blockEnd}) {
                id
                tvl0
                tvl1
                tvlUSD
                pool {
                    currentTick
                    feeGrowthGlobal0X128
                    feeGrowthGlobal1X128
                    token0 {
                        priceUSD
                    }
                    token1 {
                        priceUSD
                    }
                }
                basePosition {
                    liquidity
                    tokensOwed0
                    tokensOwed1
                    feeGrowthInside0X128
                    feeGrowthInside1X128
                    tickLower {
                        tickIdx
                        feeGrowthOutside0X128
                        feeGrowthOutside1X128
                    }
                    tickUpper {
                        tickIdx
                        feeGrowthOutside0X128
                        feeGrowthOutside1X128
                    }
                }
                limitPosition {
                    liquidity
                    tokensOwed0
                    tokensOwed1
                    feeGrowthInside0X128
                    feeGrowthInside1X128
                    tickLower {
                        tickIdx
                        feeGrowthOutside0X128
                        feeGrowthOutside1X128
                    }
                    tickUpper {
                        tickIdx
                        feeGrowthOutside0X128
                        feeGrowthOutside1X128
                    }
                }
            }
            initial: hypervisors(block: {number: $blockStart}) {
                id
                tvl0
                tvl1
                tvlUSD
                pool {
                    currentTick
                    feeGrowthGlobal0X128
                    feeGrowthGlobal1X128
                    token0 {
                        priceUSD
                    }
                    token1 {
                        priceUSD
                    }
                }
                basePosition{
                    liquidity
                    tokensOwed0
                    tokensOwed1
                    feeGrowthInside0X128
                    feeGrowthInside1X128
                    tickLower {
                        tickIdx
                        feeGrowthOutside0X128
                        feeGrowthOutside1X128
                    }
                    tickUpper {
                        tickIdx
                        feeGrowthOutside0X128
                        feeGrowthOutside1X128
                    }
                }
                limitPosition {
                    liquidity
                    tokensOwed0
                    tokensOwed1
                    feeGrowthInside0X128
                    feeGrowthInside1X128
                    tickLower {
                        tickIdx
                        feeGrowthOutside0X128
                        feeGrowthOutside1X128
                    }
                    tickUpper {
                        tickIdx
                        feeGrowthOutside0X128
                        feeGrowthOutside1X128
                    }
                }
            }
            snapshots: hypervisors {
                id
                feeSnapshots(
                    where: {
                        timestamp_gte: $timestampStart
                        timestamp_lte: $timestampEnd
                    }
                ) {
                    blockNumber
                    timestamp
                    currentBlock {
                        tick
                        feeGrowthGlobal0X128
                        feeGrowthGlobal1X128
                        price0
                        price1
                        tvl0
                        tvl1
                        tvlUSD
                        basePosition {
                            liquidity
                            tokensOwed0
                            tokensOwed1
                            feeGrowthInside0X128
                            feeGrowthInside1X128
                            tickLower {
                                tickIdx
                                feeGrowthOutside0X128
                                feeGrowthOutside1X128
                            }
                            tickUpper {
                                tickIdx
                                feeGrowthOutside0X128
                                feeGrowthOutside1X128
                            }
                        }
                        limitPosition {
                            liquidity
                            tokensOwed0
                            tokensOwed1
                            feeGrowthInside0X128
                            feeGrowthInside1X128
                            tickLower {
                                tickIdx
                                feeGrowthOutside0X128
                                feeGrowthOutside1X128
                            }
                            tickUpper {
                                tickIdx
                                feeGrowthOutside0X128
                                feeGrowthOutside1X128
                            }
                        }
                    }
                    previousBlock {
                        tick
                        feeGrowthGlobal0X128
                        feeGrowthGlobal1X128
                        price0
                        price1
                        tvl0
                        tvl1
                        tvlUSD
                        basePosition {
                            liquidity
                            tokensOwed0
                            tokensOwed1
                            feeGrowthInside0X128
                            feeGrowthInside1X128
                            tickLower {
                                tickIdx
                                feeGrowthOutside0X128
                                feeGrowthOutside1X128
                            }
                            tickUpper {
                                tickIdx
                                feeGrowthOutside0X128
                                feeGrowthOutside1X128
                            }
                        }
                        limitPosition {
                            liquidity
                            tokensOwed0
                            tokensOwed1
                            feeGrowthInside0X128
                            feeGrowthInside1X128
                            tickLower {
                                tickIdx
                                feeGrowthOutside0X128
                                feeGrowthOutside1X128
                            }
                            tickUpper {
                                tickIdx
                                feeGrowthOutside0X128
                                feeGrowthOutside1X128
                            }
                        }
                    }
                }
            }
            _meta {
                block {
                number
                timestamp
                }
            }
        }
        """

        variables = {
            "blockStart": self.initial_time.block,
            "timestampStart": self.initial_time.timestamp,
            "blockEnd": self.end_time.block,
            "timestampEnd": self.end_time.timestamp,
        }

        response = await self.fee_growth_client.query(query, variables)
        return response["data"]

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
                    block=self.initial_time.block,
                    timestamp=self.initial_time.timestamp,
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


class ImpermanentDivergenceData(FeeGrowthTemporalData):
    async def get_data(self) -> None:
        await self._init_start_time()
        self.data = self._transform_data(await self._query_data())

    async def _query_data(self) -> dict:
        query = """
        query Snapshots(
            $blockStart: Int!
            $timestampStart: Int!
            $blockEnd: Int!
            $timestampEnd: Int!
        ) {
            static: hypervisors(block: {number: $blockEnd}) {
                id
                symbol
                pool {
                    token0 {
                        priceUSD
                        decimals
                    }
                    token1 {
                        priceUSD
                        decimals
                    }
                }
            }
            latest: hypervisors(block: {number: $blockEnd}) {
                id
                tvl0
                tvl1
                tvlUSD
                pool {
                    currentTick
                    feeGrowthGlobal0X128
                    feeGrowthGlobal1X128
                    token0 {
                        priceUSD
                    }
                    token1 {
                        priceUSD
                    }
                }
                basePosition {
                    liquidity
                    tokensOwed0
                    tokensOwed1
                    feeGrowthInside0X128
                    feeGrowthInside1X128
                    tickLower {
                        tickIdx
                        feeGrowthOutside0X128
                        feeGrowthOutside1X128
                    }
                    tickUpper {
                        tickIdx
                        feeGrowthOutside0X128
                        feeGrowthOutside1X128
                    }
                }
                limitPosition {
                    liquidity
                    tokensOwed0
                    tokensOwed1
                    feeGrowthInside0X128
                    feeGrowthInside1X128
                    tickLower {
                        tickIdx
                        feeGrowthOutside0X128
                        feeGrowthOutside1X128
                    }
                    tickUpper {
                        tickIdx
                        feeGrowthOutside0X128
                        feeGrowthOutside1X128
                    }
                }
            }
            initial: hypervisors(block: {number: $blockStart}) {
                id
                tvl0
                tvl1
                tvlUSD
                pool {
                    currentTick
                    feeGrowthGlobal0X128
                    feeGrowthGlobal1X128
                    token0 {
                        priceUSD
                    }
                    token1 {
                        priceUSD
                    }
                }
                basePosition{
                    liquidity
                    tokensOwed0
                    tokensOwed1
                    feeGrowthInside0X128
                    feeGrowthInside1X128
                    tickLower {
                        tickIdx
                        feeGrowthOutside0X128
                        feeGrowthOutside1X128
                    }
                    tickUpper {
                        tickIdx
                        feeGrowthOutside0X128
                        feeGrowthOutside1X128
                    }
                }
                limitPosition {
                    liquidity
                    tokensOwed0
                    tokensOwed1
                    feeGrowthInside0X128
                    feeGrowthInside1X128
                    tickLower {
                        tickIdx
                        feeGrowthOutside0X128
                        feeGrowthOutside1X128
                    }
                    tickUpper {
                        tickIdx
                        feeGrowthOutside0X128
                        feeGrowthOutside1X128
                    }
                }
            }
            _meta {
                block {
                number
                timestamp
                }
            }
        }
        """

        variables = {
            "blockStart": self.initial_time.block,
            "timestampStart": self.initial_time.timestamp,
            "blockEnd": self.end_time.block,
            "timestampEnd": self.end_time.timestamp,
        }

        response = await self.fee_growth_client.query(query, variables)
        return response["data"]

    def _transform_data(self, query_data: dict) -> dict[str, FeesDataRange]:
        self._extract_static_data(query_data["static"])

        # Transform list to dict for easier lookup in the next step
        initial_data = {hype["id"]: hype for hype in query_data["initial"]}

        transformed_data = {
            hypervisor_latest["id"]: FeesDataRange(
                initial=self._init_fees_data(
                    hypervisor=initial_data[hypervisor_latest["id"]],
                    hypervisor_id=initial_data[hypervisor_latest["id"]]["id"],
                    block=self.initial_time.block,
                    timestamp=self.initial_time.timestamp,
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
