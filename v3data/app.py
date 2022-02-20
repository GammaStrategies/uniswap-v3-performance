from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache

from v3data import IndexNodeClient
from v3data.accounts import AccountInfo
from v3data.bollingerbands import BollingerBand
from v3data.charts import BaseLimit
from v3data.charts.benchmark import Benchmark
from v3data.charts.daily import DailyChart
from v3data.config import (
    CHARTS_CACHE_TIMEOUT,
    DASHBOARD_CACHE_TIMEOUT,
    DEFAULT_TIMEZONE,
)
from v3data.dashboard import Dashboard
from v3data.eth import EthDistribution
from v3data.gamma import GammaDistribution, GammaInfo, GammaYield
from v3data.hypervisor import HypervisorData
from v3data.pools import pools_from_symbol
from v3data.toplevel import TopLevelData
from v3data.users import UserInfo
from v3data.utils import parse_date

app = FastAPI()

@app.get("/")
def main():
    return "Visor Data"


@app.get("/status/subgraph")
def subgraph_status():
    client = IndexNodeClient()
    return client.status()


@app.get("/charts/bollingerbands/{poolAddress}")
@app.get("/bollingerBandsChartData/{poolAddress}")
@cache(expire=CHARTS_CACHE_TIMEOUT)
async def bollingerbands_chart(poolAddress: str, periodHours: int = 24):
    bband = BollingerBand(poolAddress, periodHours)
    return {"data": bband.chart_data()}


@app.get("/bollingerBandsLatest/{poolAddress}")
def bollingerbands_latest(poolAddress: str, periodHours: int = 24):
    print(poolAddress)
    bband = BollingerBand(poolAddress, periodHours)
    return bband.latest_bands()


@app.get("/charts/dailyTvl")
@cache(expire=CHARTS_CACHE_TIMEOUT)
async def daily_tvl_chart_data(days: int = 24):
    daily = DailyChart(days)
    return {"data": daily.tvl()}


@app.get("/charts/dailyFlows")
def daily_flows_chart_data(days: int = 20):
    daily = DailyChart(days)
    return {"data": daily.asset_flows()}


@app.get("/charts/dailyHypervisorFlows/{hypervisor_address}")
def daily_hypervisor_flows_chart_data(hypervisor_address: str, days: int = 20):
    daily = DailyChart(days)
    return {"data": daily.asset_flows(hypervisor_address)}


@app.get("/charts/baseRange/all")
@cache(expire=CHARTS_CACHE_TIMEOUT)
async def base_range_chart_all(days: int = 20):
    hours = days * 24
    baseLimitData = BaseLimit(hours=hours, chart=True)
    chart_data = baseLimitData.all_rebalance_ranges()
    return chart_data


@app.get("/charts/baseRange/{hypervisor_address}")
@cache(expire=CHARTS_CACHE_TIMEOUT)
async def base_range_chart(hypervisor_address: str, days: int = 20):
    hours = days * 24
    hypervisor_address = hypervisor_address.lower()
    baseLimitData = BaseLimit(hours=hours, chart=True)
    chart_data = baseLimitData.rebalance_ranges(hypervisor_address)
    if chart_data:
        return {hypervisor_address: chart_data}
    else:
        return {}


# haven't tested yet
@app.get("/charts/benchmark/{hypervisor_address}")
# @cache(expire=CHARTS_CACHE_TIMEOUT)
async def benchmark_chart(
    hypervisor_address: str, startDate: str = "", endDate: str = ""
):
    start_date = parse_date(startDate)
    end_date = parse_date(endDate)
    hypervisor_address = hypervisor_address.lower()
    benchmark = Benchmark(hypervisor_address, start_date, end_date)
    chart_data = benchmark.chart()
    if chart_data:
        return {hypervisor_address: chart_data}
    else:
        return {}


@app.get("/user/{address}")
def user_data(address: str):
    user_info = UserInfo(address)

    return user_info.output(get_data=True)


@app.get("/vault/{address}")
def visor_data(address: str):
    account_info = AccountInfo(address)
    return account_info.output()


@app.get("/pools/{token}")
def uniswap_pools(token: str):
    return {"pools": pools_from_symbol(token)}


@app.get("/gamma/basicStats")
@app.get("/visr/basicStats")
def gamma_basic_stats():
    gamma_info = GammaInfo(days=30)
    return gamma_info.output()


@app.get("/gamma/yield")
@app.get("/visr/yield")
def gamma_yield():
    gamma_yield = GammaYield(days=30)
    return gamma_yield.output()


@app.get("/{token_symbol}/dailyDistribution")
def token_distributions(
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
        days=days, timezone=timezone
    )
    return token_distributions.output()


@app.get("/hypervisor/{hypervisor_address}/basicStats")
def hypervisor_basic_stats(response: Response, hypervisor_address):
    hypervisor = HypervisorData()
    basic_stats = hypervisor.basic_stats(hypervisor_address)

    if basic_stats:
        return basic_stats
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return "Invalid hypervisor address or not enough data"


@app.get("/hypervisor/{hypervisor_address}/returns")
def hypervisor_apy(response: Response, hypervisor_address):
    hypervisor = HypervisorData()
    returns = hypervisor.calculate_returns(hypervisor_address)

    if returns:
        return {"hypervisor": hypervisor_address, "returns": returns}
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return "Invalid hypervisor address or not enough data"


@app.get("/hypervisors/aggregateStats")
def aggregate_stats():
    top_level = TopLevelData()
    top_level_data = top_level.all_stats()

    return {
        "totalValueLockedUSD": top_level_data["tvl"],
        "pairCount": top_level_data["pool_count"],
        "totalFeesClaimedUSD": top_level_data["fees_claimed"],
    }


@app.get("/hypervisors/recentFees")
def recent_fees(hours: int = 24):
    top_level = TopLevelData()
    recent_fees = top_level.recent_fees(hours)

    return {"periodHours": hours, "fees": recent_fees}


@app.get("/hypervisors/returns")
def hypervisors_return():
    hypervisor = HypervisorData()

    return hypervisor.all_returns()


@app.get("/hypervisors/allData")
def hypervisors_all():
    hypervisor = HypervisorData()

    return hypervisor.all_data()


@app.get("/dashboard")
@cache(expire=DASHBOARD_CACHE_TIMEOUT)
async def dashboard(period: str = "weekly"):
    dashboard = Dashboard(period.lower())

    return dashboard.info("UTC")


@app.on_event("startup")
async def startup():
    FastAPICache.init(InMemoryBackend())


# Allow CORS
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
