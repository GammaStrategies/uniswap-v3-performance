from fastapi import APIRouter, Response
from fastapi_cache.decorator import cache

import v3data.common
import v3data.common.charts
import v3data.common.hypervisor
import v3data.common.masterchef
import v3data.common.masterchef_v2
import v3data.common.users
from v3data.config import (
    ALLDATA_CACHE_TIMEOUT,
    APY_CACHE_TIMEOUT,
    DB_CACHE_TIMEOUT,
    RUN_FIRST_QUERY_TYPE,
)
from v3data.enums import Chain, Protocol

PROTOCOL = Protocol.RETRO
CHAIN = Chain.POLYGON
RUN_FIRST = RUN_FIRST_QUERY_TYPE

router = APIRouter(prefix="/retro/polygon")


@router.get("/")
def root():
    return "Gamma Strategies - Retro - Polygon"


@router.get("/status/subgraph")
async def subgraph_status() -> v3data.common.SubgraphStatusOutput:
    return await v3data.common.subgraph_status(PROTOCOL, CHAIN)


@router.get("/charts/baseRange/all")
# @cache(expire=CHARTS_CACHE_TIMEOUT)
async def base_range_chart_all(days: int = 20):
    return await v3data.common.charts.base_range_chart_all(PROTOCOL, CHAIN, days)


@router.get("/charts/baseRange/{hypervisor_address}")
async def base_range_chart(hypervisor_address: str, days: int = 20):
    return await v3data.common.charts.base_range_chart(
        PROTOCOL, CHAIN, hypervisor_address, days
    )


# @router.get("/charts/benchmark/{hypervisor_address}")
# # @cache(expire=CHARTS_CACHE_TIMEOUT)
# async def benchmark_chart(
#     hypervisor_address: str, startDate: str = "", endDate: str = ""
# ):
#     return await v3data.common.charts.benchmark_chart(
#         PROTOCOL, CHAIN, hypervisor_address, startDate, endDate
#     )


@router.get("/hypervisor/{hypervisor_address}/basicStats")
async def hypervisor_basic_stats(hypervisor_address, response: Response):
    return await v3data.common.hypervisor.hypervisor_basic_stats(
        PROTOCOL, CHAIN, hypervisor_address, response
    )


@router.get("/hypervisor/{hypervisor_address}/returns")
@cache(expire=APY_CACHE_TIMEOUT)
async def hypervisor_returns(response: Response, hypervisor_address: str):
    hypervisor_returns = v3data.common.hypervisor.HypervisorsReturnsAllPeriods(
        protocol=PROTOCOL,
        chain=CHAIN,
        hypervisors=[hypervisor_address],
        response=response,
    )
    return await hypervisor_returns.run(RUN_FIRST)


# TODO: implement response
@router.get("/hypervisor/{hypervisor_address}/averageReturns")
@cache(expire=DB_CACHE_TIMEOUT)
async def hypervisor_average_apy(response: Response, hypervisor_address):
    return await v3data.common.hypervisor.hypervisor_average_return(
        protocol=PROTOCOL,
        chain=CHAIN,
        hypervisor_address=hypervisor_address,
        response=response,
    )


@router.get("/hypervisor/{hypervisor_address}/uncollectedFees")
async def hypervisor_uncollected_fees(hypervisor_address: str):
    return await v3data.common.hypervisor.uncollected_fees(
        PROTOCOL, CHAIN, hypervisor_address
    )


@router.get("/hypervisors/aggregateStats")
async def aggregate_stats(response: Response):
    aggregate_stats = v3data.common.aggregate_stats.AggregateStats(
        PROTOCOL, CHAIN, response
    )
    return await aggregate_stats.run(RUN_FIRST)


@router.get("/hypervisors/returns")
@cache(expire=APY_CACHE_TIMEOUT)
async def hypervisors_return(response: Response):
    hypervisor_returns = v3data.common.hypervisor.HypervisorsReturnsAllPeriods(
        protocol=PROTOCOL, chain=CHAIN, hypervisors=None, response=response
    )
    return await hypervisor_returns.run(RUN_FIRST)


@router.get("/hypervisors/averageReturns")
@cache(expire=DB_CACHE_TIMEOUT)
async def hypervisors_average_return(response: Response):
    return await v3data.common.hypervisor.hypervisors_average_return(
        PROTOCOL, CHAIN, response=response
    )


@router.get("/hypervisors/allData")
@cache(expire=ALLDATA_CACHE_TIMEOUT)
async def hypervisors_all(response: Response):
    all_data = v3data.common.hypervisor.AllData(PROTOCOL, CHAIN, response)
    return await all_data.run(RUN_FIRST)


@router.get("/hypervisors/uncollectedFees")
async def uncollected_fees_all():
    return await v3data.common.hypervisor.uncollected_fees_all(PROTOCOL, CHAIN)


@router.get("/hypervisors/collectedFees")
async def collected_fees(
    response: Response,
    start_timestamp: int | None = None,
    end_timestamp: int | None = None,
    start_block: int | None = None,
    end_block: int | None = None,
    usd_total_only: bool = False,
):
    """Retrieve collected fees for all hypervisors
    When default values are used, the function will return the last month's fees collected
    """
    try:
        return await v3data.common.hypervisor.collected_fees(
            protocol=PROTOCOL,
            chain=CHAIN,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            start_block=start_block,
            end_block=end_block,
            usd_total_only=usd_total_only,
        )
    except ValueError as e:
        return e


@router.get("/hypervisor/{hypervisor_address}/analytics/basic/daily")
@cache(expire=APY_CACHE_TIMEOUT)
async def hypervisor_analytics_basic_daily(hypervisor_address: str, response: Response):
    return await v3data.common.analytics.get_hype_data(
        chain=CHAIN, hypervisor_address=hypervisor_address, period=1
    )


@router.get("/hypervisor/{hypervisor_address}/analytics/basic/weekly")
@cache(expire=APY_CACHE_TIMEOUT)
async def hypervisor_analytics_basic_weekly(
    hypervisor_address: str, response: Response
):
    return await v3data.common.analytics.get_hype_data(
        chain=CHAIN, hypervisor_address=hypervisor_address, period=7
    )


@router.get("/hypervisor/{hypervisor_address}/analytics/basic/biweekly")
@cache(expire=APY_CACHE_TIMEOUT)
async def hypervisor_analytics_basic_biweekly(
    hypervisor_address: str, response: Response
):
    return await v3data.common.analytics.get_hype_data(
        chain=CHAIN, hypervisor_address=hypervisor_address, period=14
    )


@router.get("/hypervisor/{hypervisor_address}/analytics/basic/monthly")
@cache(expire=APY_CACHE_TIMEOUT)
async def hypervisor_analytics_basic_monthly(
    hypervisor_address: str, response: Response
):
    return await v3data.common.analytics.get_hype_data(
        chain=CHAIN, hypervisor_address=hypervisor_address, period=30
    )


@router.get("/hypervisors/feeReturns/daily")
@cache(expire=APY_CACHE_TIMEOUT)
async def fee_returns_daily(response: Response):
    fee_returns = v3data.common.hypervisor.FeeReturns(
        PROTOCOL, CHAIN, 1, response=response
    )
    return await fee_returns.run(RUN_FIRST)


@router.get("/hypervisors/feeReturns/weekly")
@cache(expire=APY_CACHE_TIMEOUT)
async def fee_returns_weekly(response: Response):
    fee_returns = v3data.common.hypervisor.FeeReturns(
        PROTOCOL, CHAIN, 7, response=response
    )
    return await fee_returns.run(RUN_FIRST)


@router.get("/hypervisors/feeReturns/monthly")
@cache(expire=APY_CACHE_TIMEOUT)
async def fee_returns_monthly(response: Response):
    fee_returns = v3data.common.hypervisor.FeeReturns(
        PROTOCOL, CHAIN, 30, response=response
    )
    return await fee_returns.run(RUN_FIRST)


@router.get("/hypervisors/impermanentDivergence/daily")
@cache(expire=APY_CACHE_TIMEOUT)
async def impermanent_divergence_daily(response: Response):
    impermanent = v3data.common.hypervisor.ImpermanentDivergence(
        protocol=PROTOCOL, chain=CHAIN, days=1, response=response
    )
    return await impermanent.run(first=RUN_FIRST)


@router.get("/hypervisors/impermanentDivergence/weekly")
@cache(expire=APY_CACHE_TIMEOUT)
async def impermanent_divergence_weekly(response: Response):
    impermanent = v3data.common.hypervisor.ImpermanentDivergence(
        protocol=PROTOCOL, chain=CHAIN, days=7, response=response
    )
    return await impermanent.run(first=RUN_FIRST)


@router.get("/hypervisors/impermanentDivergence/monthly")
@cache(expire=APY_CACHE_TIMEOUT)
async def impermanent_divergence_monthly(response: Response):
    impermanent = v3data.common.hypervisor.ImpermanentDivergence(
        protocol=PROTOCOL, chain=CHAIN, days=30, response=response
    )
    return await impermanent.run(first=RUN_FIRST)


@router.get("/allRewards2")
@cache(expire=DB_CACHE_TIMEOUT)
async def all_rewards_2(response: Response):
    masterchef_v2_info = v3data.common.masterchef_v2.AllRewards2(
        PROTOCOL, CHAIN, response
    )
    return await masterchef_v2_info.run(RUN_FIRST)


@router.get("/userRewards2/{user_address}")
async def user_rewards_2(user_address):
    return await v3data.common.masterchef_v2.user_rewards(PROTOCOL, CHAIN, user_address)


@router.get("/user/{address}")
async def user_data(address: str):
    return await v3data.common.users.user_data(PROTOCOL, CHAIN, address)


@router.get("/vault/{address}")
async def account_data(address: str):
    return await v3data.common.users.account_data(PROTOCOL, CHAIN, address)
