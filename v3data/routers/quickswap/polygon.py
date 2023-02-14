import v3data.common
import v3data.common.charts
import v3data.common.hypervisor
import v3data.common.users
import v3data.common.masterchef
import v3data.common.masterchef_v2

from fastapi import APIRouter, Response
from fastapi_cache.decorator import cache
from v3data.config import APY_CACHE_TIMEOUT, ALLDATA_CACHE_TIMEOUT
from v3data.constants import PROTOCOL_QUICKSWAP

from v3data.hype_fees.data import FeeGrowthData, FeeGrowthSnapshotData
from v3data.hype_fees.fees import Fees
from v3data.hype_fees.fees_yield import FeesYield

from v3data.hype_fees.schema import (
    FeesData,
    _PositionData,
    _TickData,
    _TokenPair,
    _TokenPairDecimals,
)

CHAIN_POLYGON = "polygon"

router = APIRouter(prefix="/quickswap/polygon")


@router.get("/")
def root():
    return "Gamma Strategies - Quickswap - Polygon"


@router.get("/status/subgraph")
async def subgraph_status():
    return await v3data.common.subgraph_status(PROTOCOL_QUICKSWAP, CHAIN_POLYGON)


@router.get("/charts/bollingerbands/{poolAddress}")
async def bollingerbands_chart(poolAddress: str, periodHours: int = 24):
    return await v3data.common.charts.bollingerbands_chart(
        PROTOCOL_QUICKSWAP, CHAIN_POLYGON, poolAddress, periodHours
    )


@router.get("/charts/baseRange/all")
# @cache(expire=CHARTS_CACHE_TIMEOUT)
async def base_range_chart_all(days: int = 20):
    return await v3data.common.charts.base_range_chart_all(
        PROTOCOL_QUICKSWAP, CHAIN_POLYGON, days
    )


@router.get("/charts/baseRange/{hypervisor_address}")
async def base_range_chart(hypervisor_address: str, days: int = 20):
    return await v3data.common.charts.base_range_chart(
        PROTOCOL_QUICKSWAP, CHAIN_POLYGON, hypervisor_address, days
    )


@router.get("/charts/benchmark/{hypervisor_address}")
# @cache(expire=CHARTS_CACHE_TIMEOUT)
async def benchmark_chart(
    hypervisor_address: str, startDate: str = "", endDate: str = ""
):
    return await v3data.common.charts.benchmark_chart(
        PROTOCOL_QUICKSWAP, CHAIN_POLYGON, hypervisor_address, startDate, endDate
    )


@router.get("/hypervisor/{hypervisor_address}/basicStats")
async def hypervisor_basic_stats(hypervisor_address, response: Response):
    return await v3data.common.hypervisor.hypervisor_basic_stats(
        PROTOCOL_QUICKSWAP, CHAIN_POLYGON, hypervisor_address, response
    )


@router.get("/hypervisor/{hypervisor_address}/returns")
@cache(expire=APY_CACHE_TIMEOUT)
async def hypervisor_apy(response: Response, hypervisor_address):
    return await v3data.common.hypervisor.hypervisor_apy(
        PROTOCOL_QUICKSWAP, CHAIN_POLYGON, hypervisor_address, response
    )


@router.get("/hypervisor/{hypervisor_address}/uncollectedFees")
async def hypervisor_uncollected_fees(hypervisor_address: str):
    return await v3data.common.hypervisor.uncollected_fees(
        PROTOCOL_QUICKSWAP, CHAIN_POLYGON, hypervisor_address
    )


@router.get("/hypervisors/aggregateStats")
async def aggregate_stats():
    return await v3data.common.hypervisor.aggregate_stats(
        PROTOCOL_QUICKSWAP, CHAIN_POLYGON
    )


@router.get("/hypervisors/returns")
@cache(expire=APY_CACHE_TIMEOUT)
async def hypervisors_return():
    return await v3data.common.hypervisor.hypervisors_return(
        PROTOCOL_QUICKSWAP, CHAIN_POLYGON
    )


@router.get("/hypervisors/allData")
@cache(expire=ALLDATA_CACHE_TIMEOUT)
async def hypervisors_all():
    return await v3data.common.hypervisor.hypervisors_all(
        PROTOCOL_QUICKSWAP, CHAIN_POLYGON
    )


@router.get("/hypervisors/uncollectedFees")
async def uncollected_fees_all():
    return await v3data.common.hypervisor.uncollected_fees_all(
        PROTOCOL_QUICKSWAP, CHAIN_POLYGON
    )


@router.get("/hypervisors/feeReturns/daily")
@cache(expire=APY_CACHE_TIMEOUT)
async def fee_returns_daily():
    return await v3data.common.hypervisor.fee_returns(
        PROTOCOL_QUICKSWAP, CHAIN_POLYGON, 1
    )


@router.get("/hypervisors/feeReturns/weekly")
@cache(expire=APY_CACHE_TIMEOUT)
async def fee_returns_weekly():
    return await v3data.common.hypervisor.fee_returns(
        PROTOCOL_QUICKSWAP, CHAIN_POLYGON, 7
    )


@router.get("/hypervisors/feeReturns/monthly")
@cache(expire=APY_CACHE_TIMEOUT)
async def fee_returns_monthly():
    return await v3data.common.hypervisor.fee_returns(
        PROTOCOL_QUICKSWAP, CHAIN_POLYGON, 30
    )


@router.get("/allRewards")
async def all_rewards():
    return await v3data.common.masterchef.info(PROTOCOL_QUICKSWAP, CHAIN_POLYGON)


@router.get("/allRewards2")
@cache(expire=ALLDATA_CACHE_TIMEOUT)
async def all_rewards_2():
    return await v3data.common.masterchef_v2.info(PROTOCOL_QUICKSWAP, CHAIN_POLYGON)


@router.get("/userRewards/{user_address}")
async def user_rewards(user_address):
    return await v3data.common.masterchef.user_rewards(
        PROTOCOL_QUICKSWAP, CHAIN_POLYGON, user_address
    )


@router.get("/userRewards2/{user_address}")
async def user_rewards_2(user_address):
    return await v3data.common.masterchef_v2.user_rewards(
        PROTOCOL_QUICKSWAP, CHAIN_POLYGON, user_address
    )


@router.get("/user/{address}")
async def user_data(address: str):
    return await v3data.common.users.user_data(
        PROTOCOL_QUICKSWAP, CHAIN_POLYGON, address
    )


@router.get("/vault/{address}")
async def account_data(address: str):
    return await v3data.common.users.account_data(
        PROTOCOL_QUICKSWAP, CHAIN_POLYGON, address
    )


# @router.get("/test")
# async def test():
#     fees_data = FeeGrowthSnapshotData(1, "quickswap", CHAIN_POLYGON)
#     await fees_data.get_data()

#     results = {}
#     for hypervisor_id, fees_data in fees_data.data.items():
#         fees_yield = FeesYield(fees_data, "quickswap", CHAIN_POLYGON)
#         results[hypervisor_id] = fees_yield._calculate_returns()
#     return results


# @router.get("/test2")
# async def test2():
#     fees_data = FeeGrowthData("quickswap", CHAIN_POLYGON)
#     await fees_data.get_data()

#     hype_id = list(fees_data.data.keys())[0]

#     fees = Fees(fees_data.data[hype_id], "quickswap", CHAIN_POLYGON)

#     results = {}
#     for hype_id, fd in fees_data.data.items():
#         fees = Fees(fd, "quickswap", CHAIN_POLYGON)
#         results[hype_id] = fees.fee_usd()

#     return results
