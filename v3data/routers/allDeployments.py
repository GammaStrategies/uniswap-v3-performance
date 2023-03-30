import asyncio

from fastapi import APIRouter, Response

from v3data.common.aggregate_stats import (
    AggregateStats,
    AggregateStatsDeploymentInfoOutput,
)
from v3data.config import DEPLOYMENTS, RUN_FIRST_QUERY_TYPE

RUN_FIRST = RUN_FIRST_QUERY_TYPE

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

    aggregated_results = sum(valid_results[1:], valid_results[0])

    return AggregateStatsDeploymentInfoOutput(
        totalValueLockedUSD=aggregated_results.totalValueLockedUSD,
        pairCount=aggregated_results.pairCount,
        totalFeesClaimedUSD=aggregated_results.totalFeesClaimedUSD,
        deployments=included_deployments,
    )
