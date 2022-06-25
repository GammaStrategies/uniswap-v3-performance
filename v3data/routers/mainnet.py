import v3data.common
import v3data.common.charts
import v3data.common.hypervisor
import v3data.common.users

from fastapi import APIRouter, Response, status
from fastapi_cache.decorator import cache
from v3data.config import CHARTS_CACHE_TIMEOUT, DASHBOARD_CACHE_TIMEOUT, DEFAULT_TIMEZONE
from v3data.dashboard import Dashboard
from v3data.eth import EthDistribution

from v3data.gamma import GammaDistribution, GammaInfo, GammaYield

CHAIN_MAINNET = "mainnet"

router = APIRouter()


@router.get("/")
def root():
    return "Gamma Strategies"


@router.get("/status/subgraph")
async def subgraph_status():
    return await v3data.common.subgraph_status(CHAIN_MAINNET)


@router.get("/charts/bollingerbands/{poolAddress}")
@router.get("/bollingerBandsChartData/{poolAddress}")
async def bollingerbands_chart(poolAddress: str, periodHours: int = 24):
    return await v3data.common.charts.bollingerbands_chart(
        CHAIN_MAINNET, poolAddress, periodHours
    )


@router.get("/charts/baseRange/all")
# @cache(expire=CHARTS_CACHE_TIMEOUT)
async def base_range_chart_all(days: int = 20):
    return await v3data.common.charts.base_range_chart_all(CHAIN_MAINNET, days)


@router.get("/charts/baseRange/{hypervisor_address}")
async def base_range_chart(hypervisor_address: str, days: int = 20):
    return await v3data.common.charts.base_range_chart(
        CHAIN_MAINNET, hypervisor_address, days
    )


@router.get("/charts/benchmark/{hypervisor_address}")
# @cache(expire=CHARTS_CACHE_TIMEOUT)
async def benchmark_chart(
    hypervisor_address: str, startDate: str = "", endDate: str = ""
):
    return await v3data.common.charts.benchmark_chart(
        CHAIN_MAINNET, hypervisor_address, startDate, endDate
    )


@router.get("/hypervisor/{hypervisor_address}/basicStats")
async def hypervisor_basic_stats(hypervisor_address, response: Response):
    return await v3data.common.hypervisor.hypervisor_basic_stats(
        CHAIN_MAINNET, hypervisor_address, response
    )


@router.get("/hypervisor/{hypervisor_address}/returns")
async def hypervisor_apy(response: Response, hypervisor_address):
    return await v3data.common.hypervisor.hypervisor_apy(
        CHAIN_MAINNET, hypervisor_address, response
    )


@router.get("/hypervisors/aggregateStats")
async def aggregate_stats():
    return await v3data.common.hypervisor.aggregate_stats(CHAIN_MAINNET)


@router.get("/hypervisors/recentFees")
async def recent_fees(hours: int = 24):
    return await v3data.common.hypervisor.recent_fees(CHAIN_MAINNET, hours)


@router.get("/hypervisors/returns")
async def hypervisors_return():
    return await v3data.common.hypervisor.hypervisors_return(CHAIN_MAINNET)


@router.get("/hypervisors/allData")
async def hypervisors_all():
    return await v3data.common.hypervisor.hypervisors_all(CHAIN_MAINNET)


@router.get("/user/{address}")
async def user_data(address: str):
    return await v3data.common.users.user_data(CHAIN_MAINNET, address)


@router.get("/vault/{address}")
async def account_data(address: str):
    return await v3data.common.users.account_data(CHAIN_MAINNET, address)


@router.get("/gamma/basicStats")
@router.get("/visr/basicStats")
async def gamma_basic_stats():
    gamma_info = GammaInfo(days=30)
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
