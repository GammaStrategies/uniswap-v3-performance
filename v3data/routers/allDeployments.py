import v3data.common
import v3data.common.charts
import v3data.common.hypervisor
import v3data.common.users
import asyncio

from v3data.common.aggregate_stats import AggregateStats, AggregateStatsDeploymentInfoOutput

from fastapi import APIRouter, Response, status
from fastapi_cache.decorator import cache

from v3data.config import (
    APY_CACHE_TIMEOUT,
    DASHBOARD_CACHE_TIMEOUT,
    DEFAULT_TIMEZONE,
    DB_CACHE_TIMEOUT,
    ALLDATA_CACHE_TIMEOUT,
)
from v3data.dashboard import Dashboard
from v3data.eth import EthDistribution

from v3data.gamma import GammaDistribution, GammaInfo, GammaYield
from v3data.enums import Chain, Protocol, QueryType
from v3data.config import DEPLOYMENTS


RUN_FIRST = QueryType.SUBGRAPH

router = APIRouter(prefix="/allDeployments")


@router.get("/hypervisors/aggregateStats")
async def aggregate_stats(
    response: Response,
) -> AggregateStatsDeploymentInfoOutput:
    results = await asyncio.gather(
        *[
            AggregateStats(deployment[0], deployment[1], response).run(RUN_FIRST)
            for deployment in DEPLOYMENTS
        ],
        return_exceptions=True,
    )

    valid_results = []
    included_deployments = []
    for index, result in enumerate(results):
        if not isinstance(result, Exception):
            valid_results.append(result)
            included_deployments.append(
                f"{DEPLOYMENTS[index][0]}-{DEPLOYMENTS[index][1]}"
            )

    aggregated_results = sum(valid_results[:1], valid_results[0])

    return AggregateStatsDeploymentInfoOutput(
        totalValueLockedUSD=aggregated_results.totalValueLockedUSD,
        pairCount=aggregated_results.pairCount,
        totalFeesClaimedUSD=aggregated_results.totalFeesClaimedUSD,
        deployments=included_deployments,
    )
