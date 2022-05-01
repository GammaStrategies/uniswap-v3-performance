import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from v3data.hypervisor import UncollectedFees

from v3data.routers import mainnet, polygon, arbitrum, optimism, simulator

from v3data.bollingerbands import BollingerBand

from v3data.charts.benchmark import Benchmark
from v3data.charts.daily import DailyChart
from v3data.config import CHARTS_CACHE_TIMEOUT

from v3data.pools import pools_from_symbol
from v3data.utils import parse_date

logging.basicConfig(
    format="[%(asctime)s:%(levelname)s]:%(message)s",
    datefmt="%Y/%m/%d %I:%M:%S",
    level=logging.INFO,
)

app = FastAPI()

app.include_router(mainnet.router, tags=["Mainnet"])
app.include_router(polygon.router, tags=["Polygon"])
app.include_router(arbitrum.router, tags=["Arbitrum"])
app.include_router(optimism.router, tags=["Optimism"])
app.include_router(simulator.router, tags=["Simulator"])

# Allow CORS
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@app.get("/bollingerBandsLatest/{poolAddress}")
async def bollingerbands_latest(poolAddress: str, periodHours: int = 24):
    bband = BollingerBand(poolAddress, periodHours)
    return await bband.latest_bands()


@app.get("/charts/dailyTvl")
@cache(expire=CHARTS_CACHE_TIMEOUT)
async def daily_tvl_chart_data(days: int = 24):
    daily = DailyChart(days)
    return {"data": await daily.tvl()}


@app.get("/charts/dailyFlows")
async def daily_flows_chart_data(days: int = 20):
    daily = DailyChart(days)
    return {"data": await daily.asset_flows()}


@app.get("/charts/dailyHypervisorFlows/{hypervisor_address}")
async def daily_hypervisor_flows_chart_data(hypervisor_address: str, days: int = 20):
    daily = DailyChart(days)
    return {"data": await daily.asset_flows(hypervisor_address)}


@app.get("/charts/benchmark/{hypervisor_address}")
# @cache(expire=CHARTS_CACHE_TIMEOUT)
async def benchmark_chart(
    hypervisor_address: str, startDate: str = "", endDate: str = ""
):
    start_date = parse_date(startDate)
    end_date = parse_date(endDate)
    hypervisor_address = hypervisor_address.lower()
    benchmark = Benchmark(hypervisor_address, start_date, end_date)
    chart_data = await benchmark.chart()
    if chart_data:
        return {hypervisor_address: chart_data}
    else:
        return {}


@app.get("/pools/{token}")
async def uniswap_pools(token: str):
    return {"pools": await pools_from_symbol(token)}


@app.on_event("startup")
async def startup():
    FastAPICache.init(InMemoryBackend())
