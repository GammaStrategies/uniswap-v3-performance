import v3data.common
import v3data.common.charts
import v3data.common.hypervisor
import v3data.common.users
import v3data.common.masterchef

from fastapi import APIRouter, Response
from fastapi_cache.decorator import cache
from v3data.config import APY_CACHE_TIMEOUT, ALLDATA_CACHE_TIMEOUT, DB_CACHE_TIMEOUT
from v3data.constants import PROTOCOL_UNISWAP_V3


CHAIN_CELO = "celo"

router = APIRouter(prefix="/celo")


@router.get("/")
def root():
    return "Gamma Strategies - Celo"


@router.get("/status/subgraph")
async def subgraph_status():
    return await v3data.common.subgraph_status(PROTOCOL_UNISWAP_V3, CHAIN_CELO)


@router.get("/charts/bollingerbands/{poolAddress}")
async def bollingerbands_chart(poolAddress: str, periodHours: int = 24):
    return await v3data.common.charts.bollingerbands_chart(
        PROTOCOL_UNISWAP_V3, CHAIN_CELO, poolAddress, periodHours
    )


@router.get("/charts/baseRange/all")
# @cache(expire=CHARTS_CACHE_TIMEOUT)
async def base_range_chart_all(days: int = 20):
    return await v3data.common.charts.base_range_chart_all(
        PROTOCOL_UNISWAP_V3, CHAIN_CELO, days
    )


@router.get("/charts/baseRange/{hypervisor_address}")
async def base_range_chart(hypervisor_address: str, days: int = 20):
    return await v3data.common.charts.base_range_chart(
        PROTOCOL_UNISWAP_V3, CHAIN_CELO, hypervisor_address, days
    )


@router.get("/charts/benchmark/{hypervisor_address}")
# @cache(expire=CHARTS_CACHE_TIMEOUT)
async def benchmark_chart(
    hypervisor_address: str, startDate: str = "", endDate: str = ""
):
    return await v3data.common.charts.benchmark_chart(
        PROTOCOL_UNISWAP_V3, CHAIN_CELO, hypervisor_address, startDate, endDate
    )


@router.get("/hypervisor/{hypervisor_address}/basicStats")
async def hypervisor_basic_stats(hypervisor_address, response: Response):
    return await v3data.common.hypervisor.hypervisor_basic_stats(
        PROTOCOL_UNISWAP_V3, CHAIN_CELO, hypervisor_address, response
    )


@router.get("/hypervisor/{hypervisor_address}/returns")
@cache(expire=APY_CACHE_TIMEOUT)
async def hypervisor_apy(response: Response, hypervisor_address):
    return await v3data.common.hypervisor.hypervisor_apy(
        PROTOCOL_UNISWAP_V3, CHAIN_CELO, hypervisor_address, response
    )


# TODO: implement response
@router.get("/hypervisor/{hypervisor_address}/averageReturns")
@cache(expire=DB_CACHE_TIMEOUT)
async def hypervisor_average_apy(response: Response, hypervisor_address):
    return await v3data.common.hypervisor.hypervisor_average_return(
        protocol=PROTOCOL_UNISWAP_V3,
        chain=CHAIN_CELO,
        hypervisor_address=hypervisor_address,
        response=response,
    )


@router.get("/hypervisor/{hypervisor_address}/uncollectedFees")
async def hypervisor_uncollected_fees(hypervisor_address: str):
    return await v3data.common.hypervisor.uncollected_fees(
        PROTOCOL_UNISWAP_V3, CHAIN_CELO, hypervisor_address
    )


@router.get("/hypervisors/aggregateStats")
async def aggregate_stats(response: Response):
    return await v3data.common.hypervisor.aggregate_stats(
        PROTOCOL_UNISWAP_V3, CHAIN_CELO, response=response
    )


@router.get("/hypervisors/returns")
@cache(expire=APY_CACHE_TIMEOUT)
async def hypervisors_return(response: Response):
    return await v3data.common.hypervisor.hypervisors_return(
        PROTOCOL_UNISWAP_V3, CHAIN_CELO, response=response
    )


@router.get("/hypervisors/averageReturns")
@cache(expire=DB_CACHE_TIMEOUT)
async def hypervisors_average_return(response: Response):
    return await v3data.common.hypervisor.hypervisors_average_return(
        PROTOCOL_UNISWAP_V3, CHAIN_CELO, response=response
    )


@router.get("/hypervisors/allData")
@cache(expire=ALLDATA_CACHE_TIMEOUT)
async def hypervisors_all(response: Response):
    return await v3data.common.hypervisor.hypervisors_all(
        PROTOCOL_UNISWAP_V3, CHAIN_CELO, response=response
    )


@router.get("/hypervisors/uncollectedFees")
async def uncollected_fees_all():
    return await v3data.common.hypervisor.uncollected_fees_all(
        PROTOCOL_UNISWAP_V3, CHAIN_CELO
    )


@router.get("/hypervisors/feeReturns/daily")
@cache(expire=APY_CACHE_TIMEOUT)
async def fee_returns_daily(response: Response):
    return await v3data.common.hypervisor.fee_returns(
        PROTOCOL_UNISWAP_V3, CHAIN_CELO, 1, response=response
    )


@router.get("/hypervisors/feeReturns/weekly")
@cache(expire=APY_CACHE_TIMEOUT)
async def fee_returns_weekly(response: Response):
    return await v3data.common.hypervisor.fee_returns(
        PROTOCOL_UNISWAP_V3, CHAIN_CELO, 7, response=response
    )


@router.get("/hypervisors/feeReturns/monthly")
@cache(expire=APY_CACHE_TIMEOUT)
async def fee_returns_monthly(response: Response):
    return await v3data.common.hypervisor.fee_returns(
        PROTOCOL_UNISWAP_V3, CHAIN_CELO, 30, response=response
    )


@router.get("/hypervisors/impermanentDivergence/daily")
@cache(expire=APY_CACHE_TIMEOUT)
async def impermanent_divergence_daily():
    return await v3data.common.hypervisor.impermanent_divergence(
        protocol=PROTOCOL_UNISWAP_V3, chain=CHAIN_CELO, days=1
    )


@router.get("/hypervisors/impermanentDivergence/weekly")
@cache(expire=APY_CACHE_TIMEOUT)
async def impermanent_divergence_weekly():
    return await v3data.common.hypervisor.impermanent_divergence(
        protocol=PROTOCOL_UNISWAP_V3, chain=CHAIN_CELO, days=7
    )


@router.get("/hypervisors/impermanentDivergence/monthly")
@cache(expire=APY_CACHE_TIMEOUT)
async def impermanent_divergence_monthly():
    return await v3data.common.hypervisor.impermanent_divergence(
        protocol=PROTOCOL_UNISWAP_V3, chain=CHAIN_CELO, days=30
    )


@router.get("/user/{address}")
async def user_data(address: str):
    return await v3data.common.users.user_data(PROTOCOL_UNISWAP_V3, CHAIN_CELO, address)


@router.get("/vault/{address}")
async def account_data(address: str):
    return await v3data.common.users.account_data(
        PROTOCOL_UNISWAP_V3, CHAIN_CELO, address
    )
