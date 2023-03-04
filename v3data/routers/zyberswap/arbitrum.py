import v3data.common
import v3data.common.charts
import v3data.common.hypervisor
import v3data.common.users
import v3data.common.masterchef
import v3data.common.masterchef_v2

from fastapi import APIRouter, Response
from fastapi_cache.decorator import cache
from v3data.config import APY_CACHE_TIMEOUT, ALLDATA_CACHE_TIMEOUT, DB_CACHE_TIMEOUT
from v3data.enums import Chain, Protocol, QueryType

PROTOCOL = Protocol.ZYBERSWAP
CHAIN = Chain.ARBITRUM
RUN_FIRST = QueryType.SUBGRAPH

router = APIRouter(prefix="/zyberswap/arbitrum")


@router.get("/")
def root():
    return "Gamma Strategies - Zyberswap - Arbitrum"


@router.get("/status/subgraph")
async def subgraph_status():
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


@router.get("/charts/benchmark/{hypervisor_address}")
# @cache(expire=CHARTS_CACHE_TIMEOUT)
async def benchmark_chart(
    hypervisor_address: str, startDate: str = "", endDate: str = ""
):
    return await v3data.common.charts.benchmark_chart(
        PROTOCOL, CHAIN, hypervisor_address, startDate, endDate
    )


@router.get("/hypervisor/{hypervisor_address}/basicStats")
async def hypervisor_basic_stats(hypervisor_address, response: Response):
    return await v3data.common.hypervisor.hypervisor_basic_stats(
        PROTOCOL, CHAIN, hypervisor_address, response
    )


@router.get("/hypervisor/{hypervisor_address}/returns")
@cache(expire=APY_CACHE_TIMEOUT)
async def hypervisor_returns(response: Response, hypervisor_address: str):
    hypervisor_returns = v3data.common.hypervisor.HypervisorReturnsAllPeriods(
        PROTOCOL, CHAIN, response
    )
    results = await hypervisor_returns.run(RUN_FIRST)
    return results[hypervisor_address]


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
    aggregate_stats = v3data.common.hypervisor.AggregateStats(PROTOCOL, CHAIN, response)
    return await aggregate_stats.run(RUN_FIRST)


@router.get("/hypervisors/returns")
@cache(expire=APY_CACHE_TIMEOUT)
async def hypervisors_return(response: Response):
    hypervisor_returns = v3data.common.hypervisor.HypervisorsReturnsAllPeriods(
        PROTOCOL, CHAIN, response
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
async def impermanent_divergence_daily():
    return await v3data.common.hypervisor.impermanent_divergence(
        protocol=PROTOCOL, chain=CHAIN, days=1
    )


@router.get("/hypervisors/impermanentDivergence/weekly")
@cache(expire=APY_CACHE_TIMEOUT)
async def impermanent_divergence_weekly():
    return await v3data.common.hypervisor.impermanent_divergence(
        protocol=PROTOCOL, chain=CHAIN, days=7
    )


@router.get("/hypervisors/impermanentDivergence/monthly")
@cache(expire=APY_CACHE_TIMEOUT)
async def impermanent_divergence_monthly():
    return await v3data.common.hypervisor.impermanent_divergence(
        protocol=PROTOCOL, chain=CHAIN, days=30
    )


@router.get("/user/{address}")
async def user_data(address: str):
    return await v3data.common.users.user_data(PROTOCOL, CHAIN, address)


@router.get("/vault/{address}")
async def account_data(address: str):
    return await v3data.common.users.account_data(PROTOCOL, CHAIN, address)


@router.get("/divergence")
async def divergence(response: Response, days: int = 1):
    divergence = v3data.common.hypervisor.ImpermanentDivergence(
        PROTOCOL, CHAIN, days, response
    )
    return await divergence.run(RUN_FIRST)
