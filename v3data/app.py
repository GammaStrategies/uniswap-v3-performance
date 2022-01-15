import logging

from flask import Flask, request, Response
from flask_caching import Cache
from flask_cors import CORS

from v3data import IndexNodeClient
from v3data.pools import pools_from_symbol
from v3data.bollingerbands import BollingerBand
from v3data.charts import BaseLimit, Benchmark, DailyChart
from v3data.hypervisor import HypervisorData
from v3data.eth import EthDistribution
from v3data.gamma import GammaInfo, GammaDistribution, GammaYield
from v3data.users import UserInfo
from v3data.accounts import AccountInfo
from v3data.toplevel import TopLevelData
from v3data.dashboard import Dashboard
from v3data.config import DEFAULT_TIMEZONE, CHARTS_CACHE_TIMEOUT, DASHBOARD_CACHE_TIMEOUT
from v3data.utils import parse_date

logging.basicConfig(
    format='[%(asctime)s:%(levelname)s]:%(message)s',
    datefmt='%Y/%m/%d %I:%M:%S',
    level=logging.INFO
)

app = Flask(__name__)
app.config.from_mapping({'CACHE_TYPE': 'SimpleCache'})
cache = Cache(app)
CORS(app)


@app.route('/')
def main():
    return "Visor Data"


@app.route('/status/subgraph')
def subgraph_status():
    client = IndexNodeClient()
    return client.status()


@app.route('/charts/bollingerbands/<string:poolAddress>')
@app.route('/bollingerBandsChartData/<string:poolAddress>')
@cache.cached(timeout=CHARTS_CACHE_TIMEOUT)
def bollingerbands_chart(poolAddress):
    periodHours = int(request.args.get("periodHours", 24))

    bband = BollingerBand(poolAddress, periodHours)

    return {'data': bband.chart_data()}


@app.route('/bollingerBandsLatest/<string:poolAddress>')
def bollingerbands_latest(poolAddress):
    periodHours = int(request.args.get("periodHours", 24))

    bband = BollingerBand(poolAddress, periodHours)

    return bband.latest_bands()


@app.route('/charts/dailyTvl')
@cache.cached(timeout=CHARTS_CACHE_TIMEOUT)
def daily_tvl_chart_data():
    days = int(request.args.get("days", 20))

    daily = DailyChart(days)

    return {'data': daily.tvl()}


@app.route('/charts/dailyFlows')
def daily_flows_chart_data():
    days = int(request.args.get("days", 20))

    daily = DailyChart(days)

    return {'data': daily.asset_flows()}


@app.route('/charts/dailyHypervisorFlows/<string:hypervisor_address>')
def daily_hypervisor_flows_chart_data(hypervisor_address):
    days = int(request.args.get("days", 20))

    daily = DailyChart(days)

    return {'data': daily.asset_flows(hypervisor_address)}


@app.route('/charts/baseRange/<string:hypervisor_address>')
@cache.cached(timeout=CHARTS_CACHE_TIMEOUT)
def base_range_chart(hypervisor_address):
    hours = int(request.args.get("days", 20)) * 24
    hypervisor_address = hypervisor_address.lower()
    baseLimitData = BaseLimit(hours=hours, chart=True)
    chart_data = baseLimitData.rebalance_ranges(hypervisor_address)
    if chart_data:
        return {hypervisor_address: chart_data}
    else:
        return {}


@app.route('/charts/baseRange/all')
@cache.cached(timeout=CHARTS_CACHE_TIMEOUT)
def base_range_chart_all():
    hours = int(request.args.get("days", 20)) * 24
    baseLimitData = BaseLimit(hours=hours, chart=True)
    chart_data = baseLimitData.all_rebalance_ranges()
    return chart_data


@app.route('/charts/benchmark/<string:hypervisor_address>')
# @cache.cached(timeout=CHARTS_CACHE_TIMEOUT)
def benchmark_chart(hypervisor_address):
    start_date = parse_date(request.args.get("startDate"))
    end_date = parse_date(request.args.get("endDate"))
    hypervisor_address = hypervisor_address.lower()
    benchmark = Benchmark(hypervisor_address, start_date, end_date)
    chart_data = benchmark.chart()
    if chart_data:
        return {hypervisor_address: chart_data}
    else:
        return {}


@app.route('/user/<string:address>')
def user_data(address):
    user_info = UserInfo(address)

    return user_info.output(get_data=True)


@app.route('/vault/<string:address>')
def visor_data(address):
    account_info = AccountInfo(address)
    return account_info.output()


@app.route('/pools/<string:token>')
def uniswap_pools(token):
    return {"pools": pools_from_symbol(token)}


@app.route('/gamma/basicStats')
@app.route('/visr/basicStats')
def gamma_basic_stats():
    gamma_info = GammaInfo(days=30)
    return gamma_info.output()


@app.route('/gamma/yield')
@app.route('/visr/yield')
def gamma_yield():
    gamma_yield = GammaYield(days=30)
    return gamma_yield.output()


@app.route('/gamma/dailyDistribution')
@app.route('/visr/dailyDistribution')
def gamma_distributions():
    days = int(request.args.get("days", 6))
    timezone = request.args.get("timezone", DEFAULT_TIMEZONE).upper()

    if timezone not in ['UTC', 'UTC-5']:
        return Response("Only UTC and UTC-5 timezones supported", status=400)

    gamma_distributions = GammaDistribution(days=days, timezone=timezone)
    return gamma_distributions.output()


@app.route('/eth/dailyDistribution')
def eth_distributions():
    days = int(request.args.get("days", 6))
    timezone = request.args.get("timezone", DEFAULT_TIMEZONE).upper()

    if timezone not in ['UTC', 'UTC-5']:
        return Response("Only UTC and UTC-5 timezones supported", status=400)

    eth_distributions = EthDistribution(days=days, timezone=timezone)
    return eth_distributions.output()


@app.route('/hypervisor/<string:hypervisor_address>/basicStats')
def hypervisor_basic_stats(hypervisor_address):
    hypervisor = HypervisorData()
    basic_stats = hypervisor.basic_stats(hypervisor_address)

    if basic_stats:
        return basic_stats
    else:
        return Response("Invalid hypervisor address or not enough data", status=400)


@app.route('/hypervisor/<string:hypervisor_address>/returns')
def hypervisor_apy(hypervisor_address):
    hypervisor = HypervisorData()
    returns = hypervisor.calculate_returns(hypervisor_address)

    if returns:
        return {
            "hypervisor": hypervisor_address,
            "returns": returns
        }
    else:
        return Response("Invalid hypervisor address or not enough data", status=400)


@app.route('/hypervisors/aggregateStats')
def aggregate_stats():
    top_level = TopLevelData()
    top_level_data = top_level.all_stats()

    return {
        'totalValueLockedUSD': top_level_data['tvl'],
        'pairCount': top_level_data['pool_count'],
        'totalFeesClaimedUSD': top_level_data['fees_claimed']
    }


@app.route('/hypervisors/recentFees')
def recent_fees():
    hours = int(request.args.get("hours", 24))
    top_level = TopLevelData()
    recent_fees = top_level.recent_fees(hours)

    return {
        "periodHours": hours,
        "fees": recent_fees
    }


@app.route('/hypervisors/returns')
def hypervisors_return():
    hypervisor = HypervisorData()

    return hypervisor.all_returns()


@app.route('/hypervisors/allData')
def hypervisors_all():
    hypervisor = HypervisorData()

    return hypervisor.all_data()


@app.route('/dashboard')
@cache.cached(timeout=DASHBOARD_CACHE_TIMEOUT)
def dashboard():
    period = request.args.get("period", "weekly").lower()
    dashboard = Dashboard(period)

    return dashboard.info('UTC')
