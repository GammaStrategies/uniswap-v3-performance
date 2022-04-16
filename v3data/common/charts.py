from fastapi_cache.decorator import cache
from v3data.bollingerbands import BollingerBand
from v3data.charts.base_range import BaseLimit
from v3data.charts.benchmark import Benchmark

from v3data.config import CHARTS_CACHE_TIMEOUT
from v3data.utils import parse_date


@cache(expire=CHARTS_CACHE_TIMEOUT)
async def bollingerbands_chart(chain: str, poolAddress: str, periodHours: int = 24):
    bband = BollingerBand(poolAddress, periodHours, chain=chain)
    return {"data": await bband.chart_data()}


@cache(expire=CHARTS_CACHE_TIMEOUT)
async def base_range_chart_all(chain: str, days: int = 20):
    hours = days * 24
    baseLimitData = BaseLimit(hours=hours, chart=True, chain=chain)
    chart_data = await baseLimitData.all_rebalance_ranges()
    return chart_data


@cache(expire=CHARTS_CACHE_TIMEOUT)
async def base_range_chart(chain: str, hypervisor_address: str, days: int = 20):
    hours = days * 24
    hypervisor_address = hypervisor_address.lower()
    baseLimitData = BaseLimit(hours=hours, chart=True, chain=chain)
    chart_data = await baseLimitData.rebalance_ranges(hypervisor_address)
    if chart_data:
        return {hypervisor_address: chart_data}
    else:
        return {}


async def benchmark_chart(
    chain: str, hypervisor_address: str, startDate: str = "", endDate: str = ""
):
    start_date = parse_date(startDate)
    end_date = parse_date(endDate)
    hypervisor_address = hypervisor_address.lower()
    benchmark = Benchmark(chain, hypervisor_address, start_date, end_date)
    chart_data = await benchmark.chart()
    if chart_data:
        return {hypervisor_address: chart_data}
    else:
        return {}
