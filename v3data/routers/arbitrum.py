import v3data.common
import v3data.common.charts
import v3data.common.hypervisor
import v3data.common.users

from fastapi import APIRouter, Response
from fastapi_cache.decorator import cache
from v3data.config import APY_CACHE_TIMEOUT, CHARTS_CACHE_TIMEOUT

CHAIN_ARBITRUM = "arbitrum"

router = APIRouter(prefix="/arbitrum")


@router.get("/")
def root():
    return "Gamma Strategies - Arbitrum"


@router.get("/status/subgraph")
async def subgraph_status():
    return await v3data.common.subgraph_status(CHAIN_ARBITRUM)


@router.get("/charts/bollingerbands/{poolAddress}")
async def bollingerbands_chart(poolAddress: str, periodHours: int = 24):
    return await v3data.common.charts.bollingerbands_chart(
        CHAIN_ARBITRUM, poolAddress, periodHours
    )


@router.get("/charts/baseRange/all")
# @cache(expire=CHARTS_CACHE_TIMEOUT)
async def base_range_chart_all(days: int = 20):
    return await v3data.common.charts.base_range_chart_all(CHAIN_ARBITRUM, days)


@router.get("/charts/baseRange/{hypervisor_address}")
async def base_range_chart(hypervisor_address: str, days: int = 20):
    return await v3data.common.charts.base_range_chart(
        CHAIN_ARBITRUM, hypervisor_address, days
    )

@router.get("/charts/benchmark/{hypervisor_address}")
# @cache(expire=CHARTS_CACHE_TIMEOUT)
async def benchmark_chart(
    hypervisor_address: str, startDate: str = "", endDate: str = ""
):
    return await v3data.common.charts.benchmark_chart(
        CHAIN_ARBITRUM, hypervisor_address, startDate, endDate
    )

@router.get("/hypervisor/{hypervisor_address}/basicStats")
async def hypervisor_basic_stats(hypervisor_address, response: Response):
    return await v3data.common.hypervisor.hypervisor_basic_stats(
        CHAIN_ARBITRUM, hypervisor_address, response
    )


@router.get("/hypervisor/{hypervisor_address}/returns")
@cache(expire=APY_CACHE_TIMEOUT)
async def hypervisor_apy(response: Response, hypervisor_address):
    return await v3data.common.hypervisor.hypervisor_apy(
        CHAIN_ARBITRUM, hypervisor_address, response
    )


@router.get("/hypervisors/aggregateStats")
async def aggregate_stats():
    return await v3data.common.hypervisor.aggregate_stats(CHAIN_ARBITRUM)


@router.get("/hypervisors/returns")
@cache(expire=APY_CACHE_TIMEOUT)
async def hypervisors_return():
    return await v3data.common.hypervisor.hypervisors_return(CHAIN_ARBITRUM)


@router.get("/hypervisors/allData")
async def hypervisors_all():
    return await v3data.common.hypervisor.hypervisors_all(CHAIN_ARBITRUM)


@router.get("/user/{address}")
async def user_data(address: str):
    return await v3data.common.users.user_data(CHAIN_ARBITRUM, address)


@router.get("/vault/{address}")
async def account_data(address: str):
    return await v3data.common.users.account_data(CHAIN_ARBITRUM, address)


@router.get("/hypervisor/{hypervisor_address}/uncollectedFees")
async def hypervisor_uncollected_fees(hypervisor_address: str):
    return await v3data.common.hypervisor.uncollected_fees(
        CHAIN_ARBITRUM, hypervisor_address
    )
