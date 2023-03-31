"""Hype Pool Subgraph for getting fee data"""
from gql.dsl import DSLFragment

from v3data.enums import Chain, Protocol
from v3data.config import DEX_HYPEPOOL_SUBGRAPH_URLS
from v3data.subgraphs import SubgraphClient, fragment


class HypePoolClient(SubgraphClient):
    """Client for accessing Hype Pool Subgraphs for different deployments"""

    def __init__(self, protocol: Protocol, chain: Chain) -> None:
        super().__init__(
            url=DEX_HYPEPOOL_SUBGRAPH_URLS[protocol][chain],
            schema_path="v3data/subgraphs/hype_pool/schema.graphql",
        )

    @fragment
    def tick_fields_fragment(self) -> DSLFragment:
        """Common tick fields"""
        frag = DSLFragment("TickFields")
        ds_tick = self.data_schema.Tick
        frag.on(ds_tick)
        frag.select(
            ds_tick.tickIdx,
            ds_tick.feeGrowthOutside0X128,
            ds_tick.feeGrowthOutside1X128,
        )
        return frag

    @fragment
    def position_fields_fragment(self) -> DSLFragment:
        """Common position fields"""
        frag = DSLFragment("PositionFields")
        ds_position = self.data_schema.HypervisorPosition
        tick_fields_fragment = self.tick_fields_fragment()
        frag.on(ds_position)
        frag.select(
            ds_position.liquidity,
            ds_position.tokensOwed0,
            ds_position.tokensOwed1,
            ds_position.feeGrowthInside0X128,
            ds_position.feeGrowthInside1X128,
            ds_position.tickLower.select(tick_fields_fragment),
            ds_position.tickUpper.select(tick_fields_fragment),
        )
        return frag

    @fragment
    def hypervisor_fields_fragment(self) -> DSLFragment:
        "All relevant hypervisor fields"
        frag = DSLFragment("HypervisorFields")
        ds_hypervisor = self.data_schema.Hypervisor
        ds_pool = self.data_schema.Pool
        position_fields_fragment = self.position_fields_fragment()
        frag.on(ds_hypervisor)
        frag.select(
            ds_hypervisor.id,
            ds_hypervisor.totalSupply,
            ds_hypervisor.tvl0,
            ds_hypervisor.tvl1,
            ds_hypervisor.tvlUSD,
            ds_hypervisor.pool.select(
                ds_pool.currentTick,
                ds_pool.feeGrowthGlobal0X128,
                ds_pool.feeGrowthGlobal1X128,
                ds_pool.token0.select(self.data_schema.Token.priceUSD),
                ds_pool.token1.select(self.data_schema.Token.priceUSD),
            ),
            ds_hypervisor.basePosition.select(position_fields_fragment),
            ds_hypervisor.limitPosition.select(position_fields_fragment),
        )
        return frag

    @fragment
    def tick_snapshot_fields_fragment(self) -> DSLFragment:
        """Tick fields for snapshots"""
        frag = DSLFragment("TickSnapshotFields")
        ds_tick_snapshot = self.data_schema.TickSnapshot
        frag.on(ds_tick_snapshot)
        frag.select(
            ds_tick_snapshot.tickIdx,
            ds_tick_snapshot.feeGrowthOutside0X128,
            ds_tick_snapshot.feeGrowthOutside1X128,
        )
        return frag

    @fragment
    def position_snapshot_fields_fragment(self) -> DSLFragment:
        """Position fields for snapshots"""
        frag = DSLFragment("PositionSnapshotFields")
        ds_position_snapshot = self.data_schema.PositionSnapshot
        tick_snapshot_fields_fragment = self.tick_snapshot_fields_fragment()
        frag.on(ds_position_snapshot)
        frag.select(
            ds_position_snapshot.liquidity,
            ds_position_snapshot.tokensOwed0,
            ds_position_snapshot.tokensOwed1,
            ds_position_snapshot.feeGrowthInside0X128,
            ds_position_snapshot.feeGrowthInside1X128,
            ds_position_snapshot.tickLower.select(tick_snapshot_fields_fragment),
            ds_position_snapshot.tickUpper.select(tick_snapshot_fields_fragment),
        )
        return frag

    @fragment
    def block_snapshot_fields_fragment(self) -> DSLFragment:
        """Block fields for snapshots"""
        frag = DSLFragment("BlockSnapshotFields")
        ds_fee_collection_snapshot = self.data_schema.FeeCollectionSnapshot
        position_snapshot_fields_fragment = self.position_snapshot_fields_fragment()
        frag.on(ds_fee_collection_snapshot)
        frag.select(
            ds_fee_collection_snapshot.tick,
            ds_fee_collection_snapshot.feeGrowthGlobal0X128,
            ds_fee_collection_snapshot.feeGrowthGlobal1X128,
            ds_fee_collection_snapshot.price0,
            ds_fee_collection_snapshot.price1,
            ds_fee_collection_snapshot.tvl0,
            ds_fee_collection_snapshot.tvl1,
            ds_fee_collection_snapshot.tvlUSD,
            ds_fee_collection_snapshot.basePosition.select(
                position_snapshot_fields_fragment
            ),
            ds_fee_collection_snapshot.limitPosition.select(
                position_snapshot_fields_fragment
            ),
        )
        return frag
