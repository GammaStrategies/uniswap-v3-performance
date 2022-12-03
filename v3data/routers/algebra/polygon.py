import v3data.common
import v3data.common.charts
import v3data.common.hypervisor
import v3data.common.users
import v3data.common.masterchef
import v3data.common.masterchef_v2

from fastapi import APIRouter, Response
from fastapi_cache.decorator import cache
from v3data.config import APY_CACHE_TIMEOUT
from v3data.constants import PROTOCOL_ALGEBRA

CHAIN_POLYGON = "polygon"

router = APIRouter(prefix="/algebra/polygon")


@router.get("/")
def root():
    return "Gamma Strategies - Algebra Finance - Polygon"


@router.get("/status/subgraph")
async def subgraph_status():
    return await v3data.common.subgraph_status(PROTOCOL_ALGEBRA, CHAIN_POLYGON)


@router.get("/charts/bollingerbands/{poolAddress}")
async def bollingerbands_chart(poolAddress: str, periodHours: int = 24):
    return await v3data.common.charts.bollingerbands_chart(
        PROTOCOL_ALGEBRA, CHAIN_POLYGON, poolAddress, periodHours
    )


@router.get("/charts/baseRange/all")
# @cache(expire=CHARTS_CACHE_TIMEOUT)
async def base_range_chart_all(days: int = 20):
    return await v3data.common.charts.base_range_chart_all(
        PROTOCOL_ALGEBRA, CHAIN_POLYGON, days
    )


@router.get("/charts/baseRange/{hypervisor_address}")
async def base_range_chart(hypervisor_address: str, days: int = 20):
    return await v3data.common.charts.base_range_chart(
        PROTOCOL_ALGEBRA, CHAIN_POLYGON, hypervisor_address, days
    )


@router.get("/charts/benchmark/{hypervisor_address}")
# @cache(expire=CHARTS_CACHE_TIMEOUT)
async def benchmark_chart(
    hypervisor_address: str, startDate: str = "", endDate: str = ""
):
    return await v3data.common.charts.benchmark_chart(
        PROTOCOL_ALGEBRA, CHAIN_POLYGON, hypervisor_address, startDate, endDate
    )


@router.get("/hypervisor/{hypervisor_address}/basicStats")
async def hypervisor_basic_stats(hypervisor_address, response: Response):
    return await v3data.common.hypervisor.hypervisor_basic_stats(
        PROTOCOL_ALGEBRA, CHAIN_POLYGON, hypervisor_address, response
    )


@router.get("/hypervisor/{hypervisor_address}/returns")
@cache(expire=APY_CACHE_TIMEOUT)
async def hypervisor_apy(response: Response, hypervisor_address):
    return await v3data.common.hypervisor.hypervisor_apy(
        PROTOCOL_ALGEBRA, CHAIN_POLYGON, hypervisor_address, response
    )


@router.get("/hypervisor/{hypervisor_address}/uncollectedFees")
async def hypervisor_uncollected_fees(hypervisor_address: str):
    return await v3data.common.hypervisor.uncollected_fees(
        PROTOCOL_ALGEBRA, CHAIN_POLYGON, hypervisor_address
    )


@router.get("/hypervisors/aggregateStats")
async def aggregate_stats():
    return await v3data.common.hypervisor.aggregate_stats(
        PROTOCOL_ALGEBRA, CHAIN_POLYGON
    )


@router.get("/hypervisors/returns")
@cache(expire=APY_CACHE_TIMEOUT)
async def hypervisors_return():
    return await v3data.common.hypervisor.hypervisors_return(
        PROTOCOL_ALGEBRA, CHAIN_POLYGON
    )


@router.get("/hypervisors/allData")
async def hypervisors_all():
    return await v3data.common.hypervisor.hypervisors_all(
        PROTOCOL_ALGEBRA, CHAIN_POLYGON
    )


@router.get("/hypervisors/uncollectedFees")
async def uncollected_fees_all():
    return await v3data.common.hypervisor.uncollected_fees_all(
        PROTOCOL_ALGEBRA, CHAIN_POLYGON
    )


@router.get("/allRewards")
async def all_rewards():
    return await v3data.common.masterchef.info(PROTOCOL_ALGEBRA, CHAIN_POLYGON)


@router.get("/allRewards2")
async def all_rewards_2():
    return await v3data.common.masterchef_v2.info(PROTOCOL_ALGEBRA, CHAIN_POLYGON)


@router.get("/userRewards/{user_address}")
async def user_rewards(user_address):
    return await v3data.common.masterchef.user_rewards(
        PROTOCOL_ALGEBRA, CHAIN_POLYGON, user_address
    )


@router.get("/user/{address}")
async def user_data(address: str):
    return await v3data.common.users.user_data(
        PROTOCOL_ALGEBRA, CHAIN_POLYGON, address
    )


@router.get("/vault/{address}")
async def account_data(address: str):
    return await v3data.common.users.account_data(
        PROTOCOL_ALGEBRA, CHAIN_POLYGON, address
    )
