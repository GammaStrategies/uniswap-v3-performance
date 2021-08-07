from flask import Flask, request, Response
from flask_caching import Cache
from flask_cors import CORS

from v3data import IndexNodeClient
from v3data.pools import pools_from_symbol
from v3data.bollingerbands import BollingerBand
from v3data.charts import BaseLimit, Benchmark, DailyChart
from v3data.hypervisor import HypervisorData
from v3data.visr import VisrInfo, VisrYield, VisrDistribution
from v3data.users import VisorUser
from v3data.visor import VisorVault
from v3data.toplevel import TopLevelData
from v3data.dashboard import Dashboard
from v3data.config import DEFAULT_TIMEZONE, PRIVATE_BETA_TVL, CHARTS_CACHE_TIMEOUT

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
@cache.cached(timeout=CHARTS_CACHE_TIMEOUT)
def benchmark_chart(hypervisor_address):
    start_year = int(request.args.get("startYear", 2021))
    start_month = int(request.args.get("startMonth", 6))
    n_months = int(request.args.get("nMonths", 1))
    hypervisor_address = hypervisor_address.lower()
    benchmark = Benchmark(hypervisor_address, start_year, start_month, n_months)
    chart_data = benchmark.chart()
    if chart_data:
        return {hypervisor_address: chart_data}
    else:
        return {}


@app.route('/user/<string:address>')
def user_data(address):
    visor_user = VisorUser(address)

    return visor_user.info()


@app.route('/vault/<string:address>')
def visor_data(address):
    visor_vault = VisorVault(address)

    return visor_vault.info()


@app.route('/pools/<string:token>')
def uniswap_pools(token):
    return {"pools": pools_from_symbol(token)}


@app.route('/visr/basicStats')
def visr_basic_stats():
    visr_info = VisrInfo(days=30)
    return visr_info.output()


@app.route('/visr/yield')
def visr_yield():
    visr_yield = VisrYield(days=30)
    return visr_yield.output()


@app.route('/visr/dailyDistribution')
def visr_distributions():
    days = int(request.args.get("days", 6))
    timezone = request.args.get("timezone", DEFAULT_TIMEZONE).upper()

    if timezone not in ['UTC', 'UTC-5']:
        return Response("Only UTC and UTC-5 timezones supported", status=400)

    visr_distributions = VisrDistribution(days=days, timezone=timezone)
    return visr_distributions.output()


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
        'totalValueLockedUSD': top_level_data['tvl'] + PRIVATE_BETA_TVL,
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
def dashboard():
    period = request.args.get("period", "weekly").lower()
    dashboard = Dashboard(period)

    return dashboard.info('UTC')
