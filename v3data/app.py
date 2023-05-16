import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache

from v3data.charts.daily import DailyChart
from v3data.config import CHARTS_CACHE_TIMEOUT
from v3data.routers import (
    allDeployments,
    arbitrum,
    bsc,
    celo,
    mainnet,
    optimism,
    polygon,
)
from v3data.routers.camelot import arbitrum as camelot_arbitrum
from v3data.routers.glacier import avalanche as glacier_avalanche
from v3data.routers.quickswap import polygon as quickswap_polygon
from v3data.routers.quickswap import polygon_zkevm as quickswap_polygon_zkevm
from v3data.routers.retro import polygon as retro_polygon
from v3data.routers.thena import bsc as thena_bsc
from v3data.routers.zyberswap import arbitrum as zyberswap_arbitrum
from v3data.subapps.internal import app_internal
from v3data.subapps.simulator import app_simulator

logging.basicConfig(
    format="[%(asctime)s:%(levelname)s:%(name)s]:%(message)s",
    datefmt="%Y/%m/%d %I:%M:%S",
    level=logging.INFO,
)

app = FastAPI()

app.include_router(allDeployments.router, tags=["All-deployments"])
app.include_router(mainnet.router, tags=["Mainnet"])
app.include_router(polygon.router, tags=["Polygon"])
app.include_router(arbitrum.router, tags=["Arbitrum"])
app.include_router(optimism.router, tags=["Optimism"])
app.include_router(celo.router, tags=["Celo"])
app.include_router(bsc.router, tags=["BSC"])
app.include_router(quickswap_polygon.router, tags=["Quickswap - Polygon"])
app.include_router(quickswap_polygon_zkevm.router, tags=["Quickswap - Polygon zkEVM"])
app.include_router(zyberswap_arbitrum.router, tags=["Zyberswap - Arbitrum"])
app.include_router(thena_bsc.router, tags=["Thena - BSC"])
app.include_router(camelot_arbitrum.router, tags=["Camelot - Arbitrum"])
app.include_router(glacier_avalanche.router, tags=["Glacier - Avalanche"])
app.include_router(retro_polygon.router, tags=["Retro - Polygon"])

# Allow CORS
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

app.mount("/simulator", app_simulator)
app.mount("/internal", app_internal)

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


@app.on_event("startup")
async def startup():
    FastAPICache.init(InMemoryBackend())
