import v3data.common
import v3data.common.charts
import v3data.common.hypervisor
import v3data.common.users

from fastapi import APIRouter, Response
from v3data.config import CHARTS_CACHE_TIMEOUT

CHAIN_OPTIMISM = "optimism"

router = APIRouter(prefix="/optimism")


@router.get("/")
def root():
    return "Gamma Strategies - Optimism"


@router.get("/status/subgraph")
async def subgraph_status():
    return await v3data.common.subgraph_status(CHAIN_OPTIMISM)


@router.get("/charts/bollingerbands/{poolAddress}")
async def bollingerbands_chart(poolAddress: str, periodHours: int = 24):
    return await v3data.common.charts.bollingerbands_chart(
        CHAIN_OPTIMISM, poolAddress, periodHours
    )


@router.get("/charts/baseRange/all")
@cache(expire=CHARTS_CACHE_TIMEOUT)
async def base_range_chart_all(days: int = 20):
    return await v3data.common.charts.base_range_chart_all(CHAIN_OPTIMISM, days)


@router.get("/charts/baseRange/{hypervisor_address}")
async def base_range_chart(hypervisor_address: str, days: int = 20):
    return await v3data.common.charts.base_range_chart(
        CHAIN_OPTIMISM, hypervisor_address, days
    )

@router.get("/charts/benchmark/{hypervisor_address}")
# @cache(expire=CHARTS_CACHE_TIMEOUT)
async def benchmark_chart(
    hypervisor_address: str, startDate: str = "", endDate: str = ""
):
    return await v3data.common.charts.benchmark_chart(
        CHAIN_OPTIMISM, hypervisor_address, startDate, endDate
    )

@router.get("/hypervisor/{hypervisor_address}/basicStats")
async def hypervisor_basic_stats(hypervisor_address, response: Response):
    return await v3data.common.hypervisor.hypervisor_basic_stats(
        CHAIN_OPTIMISM, hypervisor_address, response
    )


@router.get("/hypervisor/{hypervisor_address}/returns")
async def hypervisor_apy(response: Response, hypervisor_address):
    return await v3data.common.hypervisor.hypervisor_apy(
        CHAIN_OPTIMISM, hypervisor_address, response
    )


@router.get("/hypervisors/aggregateStats")
async def aggregate_stats():
    return await v3data.common.hypervisor.aggregate_stats(CHAIN_OPTIMISM)


@router.get("/hypervisors/returns")
async def hypervisors_return():
    return await v3data.common.hypervisor.hypervisors_return(CHAIN_OPTIMISM)


@router.get("/hypervisors/allData")
async def hypervisors_all():
    return await v3data.common.hypervisor.hypervisors_all(CHAIN_OPTIMISM)


@router.get("/user/{address}")
async def user_data(address: str):
    return await v3data.common.users.user_data(CHAIN_OPTIMISM, address)


@router.get("/vault/{address}")
async def account_data(address: str):
    return await v3data.common.users.account_data(CHAIN_OPTIMISM, address)
