from flask import Flask, request, Response
from flask_cors import CORS

from v3data.pools import pools_from_symbol
from v3data.bollingerbands import BollingerBand
from v3data.charts import BaseLimit, Benchmark, DailyChart
from v3data.hypervisor import HypervisorData
from v3data.visr import VisrData
from v3data.users import VisorUser
from v3data.visor import VisorVault
from v3data.toplevel import TopLevelData
from v3data.config import DEFAULT_TIMEZONE, PRIVATE_BETA_TVL

app = Flask(__name__)
CORS(app)


@app.route('/')
def main():
    return "Visor Data"


@app.route('/charts/bollingerbands/<string:poolAddress>')
@app.route('/bollingerBandsChartData/<string:poolAddress>')
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
def base_range_chart_all():
    hours = int(request.args.get("days", 20)) * 24
    baseLimitData = BaseLimit(hours=hours, chart=True)
    chart_data = baseLimitData.all_rebalance_ranges()
    return chart_data


@app.route('/charts/benchmark/<string:hypervisor_address>')
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


@app.route('/dev/v2pools/<string:address>')
def v2pools(address):
    hp = HypervisorPerformance()
    data = hp._get_v2_pricing(address)
    return {"data": data}


@app.route('/visr/basicStats')
def visr_basic_stats():
    visr = VisrData()
    token_info = visr.token_info()
    visr_price_usd = visr.price_usd()

    token_info['priceUSD'] = visr_price_usd

    return token_info


@app.route('/visr/yield')
def visr_yield():
    visr = VisrData()
    yield_data = visr.token_yield()

    return yield_data


@app.route('/visr/dailyDistribution')
def visr_distributions():
    days = int(request.args.get("days", 5))
    timezone = request.args.get("timezone", DEFAULT_TIMEZONE).upper()

    if timezone not in ['UTC', 'UTC-5']:
        return Response("Only UTC and UTC-5 timezones supported", status=400)

    visr = VisrData()
    distributions = visr.daily_distribution(timezone, days)

    fee_distributions = []
    for i, distribution in enumerate(distributions):
        fee_distributions.append(
            {
                'title': distribution['date'],
                'desc': f"{int(distribution['distributed']):,} VISR Distributed",
                'id': i + 2
            }
        )

    return {
        'feeDistribution': fee_distributions
    }


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

    visr = VisrData()
    visr_info = visr.info()
    token_info = visr_info['info']
    visr_yield = visr_info['yield']
    visr_price_usd = visr.price_usd()
    distributions = visr.daily_distribution(timezone=DEFAULT_TIMEZONE, days=1)

    last_day_distribution = float(distributions[0]['distributed'])

    top_level = TopLevelData()
    top_level_data = top_level.all_stats()
    top_level_returns = top_level.calculate_returns()

    dashboard_stats = {
        "stakedUsdAmount": token_info['totalStaked'] * visr_price_usd,
        "stakedAmount": token_info['totalStaked'],
        "feeStatsFeeAccural": last_day_distribution * visr_price_usd,
        "feeStatsAmountVisr": last_day_distribution,
        "feeStatsStakingApr": visr_yield[period]['apr'],
        "feeStatsStakingApy": visr_yield[period]['apy'],
        "feeStatsStakingDailyYield": visr_yield[period]['yield'],
        "feeCumulativeFeeUsd": token_info['totalDistributedUSD'],
        "feeCumulativeFeeUsdAnnual": visr_yield[period]['estimatedAnnualDistributionUSD'],
        "feeCumulativeFeeDistributed": token_info['totalDistributed'],
        "feeCumulativeFeeDistributedAnnual": visr_yield[period]['estimatedAnnualDistribution'],
        "uniswapPairTotalValueLocked": top_level_data['tvl'] + PRIVATE_BETA_TVL,
        "uniswapPairAmountPairs": top_level_data['pool_count'],
        "uniswapFeesGenerated": top_level_data['fees_claimed'],
        "uniswapFeesBasedApr": f"{top_level_returns[period]['feeApr']:.0%}",
        "visrPrice": visr_price_usd,  # End point for price
        "id": 2  # What is this?
    }

    return dashboard_stats
