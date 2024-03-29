import v3data.common
import v3data.common.charts
import v3data.common.hypervisor
import v3data.common.users

from fastapi import APIRouter, Response, status
from fastapi_cache.decorator import cache
from v3data.config import (
    APY_CACHE_TIMEOUT,
    DASHBOARD_CACHE_TIMEOUT,
    DEFAULT_TIMEZONE,
)
from v3data.dashboard import Dashboard
from v3data.eth import EthDistribution

from v3data.gamma import GammaDistribution, GammaInfo, GammaYield
from v3data.constants import PROTOCOL_UNISWAP_V3


CHAIN_MAINNET = "mainnet"

router = APIRouter()


@router.get("/")
def root():
    return "Gamma Strategies"


@router.get("/status/subgraph")
async def subgraph_status():
    return await v3data.common.subgraph_status(
        PROTOCOL_UNISWAP_V3,
        CHAIN_MAINNET
    )


@router.get("/charts/bollingerbands/{poolAddress}")
@router.get("/bollingerBandsChartData/{poolAddress}")
async def bollingerbands_chart(poolAddress: str, periodHours: int = 24):
    return await v3data.common.charts.bollingerbands_chart(
        PROTOCOL_UNISWAP_V3, CHAIN_MAINNET, poolAddress, periodHours
    )


@router.get("/charts/baseRange/all")
# @cache(expire=CHARTS_CACHE_TIMEOUT)
async def base_range_chart_all(days: int = 20):
    return await v3data.common.charts.base_range_chart_all(
        PROTOCOL_UNISWAP_V3, CHAIN_MAINNET, days
    )


@router.get("/charts/baseRange/{hypervisor_address}")
async def base_range_chart(hypervisor_address: str, days: int = 20):
    return await v3data.common.charts.base_range_chart(
        PROTOCOL_UNISWAP_V3, CHAIN_MAINNET, hypervisor_address, days
    )


@router.get("/charts/benchmark/{hypervisor_address}")
# @cache(expire=CHARTS_CACHE_TIMEOUT)
async def benchmark_chart(
    hypervisor_address: str, startDate: str = "", endDate: str = ""
):
    return await v3data.common.charts.benchmark_chart(
        PROTOCOL_UNISWAP_V3,
        CHAIN_MAINNET,
        hypervisor_address,
        startDate,
        endDate
    )


@router.get("/hypervisor/{hypervisor_address}/basicStats")
async def hypervisor_basic_stats(hypervisor_address, response: Response):
    return await v3data.common.hypervisor.hypervisor_basic_stats(
        PROTOCOL_UNISWAP_V3, CHAIN_MAINNET, hypervisor_address, response
    )


@router.get("/hypervisor/{hypervisor_address}/returns")
@cache(expire=APY_CACHE_TIMEOUT)
async def hypervisor_apy(response: Response, hypervisor_address):
    return await v3data.common.hypervisor.hypervisor_apy(
        PROTOCOL_UNISWAP_V3, CHAIN_MAINNET, hypervisor_address, response
    )


@router.get("/hypervisor/{hypervisor_address}/uncollectedFees")
async def hypervisor_uncollected_fees(hypervisor_address: str):
    return await v3data.common.hypervisor.uncollected_fees(
        PROTOCOL_UNISWAP_V3, CHAIN_MAINNET, hypervisor_address
    )


@router.get("/hypervisors/aggregateStats")
async def aggregate_stats():
    return await v3data.common.hypervisor.aggregate_stats(
        PROTOCOL_UNISWAP_V3, CHAIN_MAINNET
    )


@router.get("/hypervisors/recentFees")
async def recent_fees(hours: int = 24):
    return await v3data.common.hypervisor.recent_fees(
        PROTOCOL_UNISWAP_V3, CHAIN_MAINNET, hours
    )


@router.get("/hypervisors/returns")
@cache(expire=APY_CACHE_TIMEOUT)
async def hypervisors_return():
    return await v3data.common.hypervisor.hypervisors_return(
        PROTOCOL_UNISWAP_V3, CHAIN_MAINNET
    )


@router.get("/hypervisors/allData")
@cache(expire=APY_CACHE_TIMEOUT)
async def hypervisors_all():
    return await v3data.common.hypervisor.hypervisors_all(
        PROTOCOL_UNISWAP_V3, CHAIN_MAINNET
    )


@router.get("/hypervisors/uncollectedFees")
async def uncollected_fees_all():
    return await v3data.common.hypervisor.uncollected_fees_all_fg(
        PROTOCOL_UNISWAP_V3, CHAIN_MAINNET
    )


@router.get("/hypervisors/feeReturns/daily")
@cache(expire=APY_CACHE_TIMEOUT)
async def fee_returns_daily():
    return await v3data.common.hypervisor.fee_returns_fg(
        PROTOCOL_UNISWAP_V3, CHAIN_MAINNET, 1
    )


@router.get("/hypervisors/feeReturns/weekly")
@cache(expire=APY_CACHE_TIMEOUT)
async def fee_returns_weekly():
    return await v3data.common.hypervisor.fee_returns_fg(
        PROTOCOL_UNISWAP_V3, CHAIN_MAINNET, 7
    )


@router.get("/hypervisors/feeReturns/monthly")
@cache(expire=APY_CACHE_TIMEOUT)
async def fee_returns_monthly():
    return await v3data.common.hypervisor.fee_returns_fg(
        PROTOCOL_UNISWAP_V3, CHAIN_MAINNET, 30
    )


@router.get("/allRewards")
async def all_rewards():
    return await v3data.common.masterchef.info(
        PROTOCOL_UNISWAP_V3,
        CHAIN_MAINNET
    )


@router.get("/userRewards/{user_address}")
async def user_rewards(user_address):
    return await v3data.common.masterchef.user_rewards(
        PROTOCOL_UNISWAP_V3, CHAIN_MAINNET, user_address
    )


@router.get("/user/{address}")
async def user_data(address: str):
    return await v3data.common.users.user_data(
        PROTOCOL_UNISWAP_V3, CHAIN_MAINNET, address
    )


@router.get("/vault/{address}")
async def account_data(address: str):
    return await v3data.common.users.account_data(
        PROTOCOL_UNISWAP_V3, CHAIN_MAINNET, address
    )


@router.get("/gamma/basicStats")
@router.get("/visr/basicStats")
async def gamma_basic_stats():
    gamma_info = GammaInfo(CHAIN_MAINNET, days=30)
    return await gamma_info.output()


@router.get("/gamma/yield")
@router.get("/visr/yield")
async def gamma_yield():
    gamma_yield = GammaYield(CHAIN_MAINNET, days=30)
    return await gamma_yield.output()


@router.get("/{token_symbol}/dailyDistribution")
async def token_distributions(
    response: Response,
    token_symbol: str = "gamma",
    days: int = 6,
    timezone: str = DEFAULT_TIMEZONE,
):
    token_symbol = token_symbol.lower()
    timezone = timezone.upper()

    if token_symbol not in ["gamma", "visr", "eth"]:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return "Only GAMMA, VISR and ETH supported"

    if timezone not in ["UTC", "UTC-5"]:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return "Only UTC and UTC-5 timezones supported"

    distribution_class_map = {
        "gamma": GammaDistribution,
        "visr": GammaDistribution,
        "eth": EthDistribution,
    }

    token_distributions = distribution_class_map[token_symbol](
        CHAIN_MAINNET, days=60, timezone=timezone
    )
    return await token_distributions.output(days)


@router.get("/dashboard")
@cache(expire=DASHBOARD_CACHE_TIMEOUT)
async def dashboard(period: str = "weekly"):
    dashboard = Dashboard(period.lower())

    return await dashboard.info("UTC")
