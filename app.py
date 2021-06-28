from flask import Flask, request, Response
from flask_cors import CORS

from v3data.pools import pools_from_symbol
from v3data.bollingerbands import BollingerBand
from v3data.strategies import BaseLimit
from v3data.hypervisor import HypervisorData
from v3data.visr import VisrData
from v3data.toplevel import TopLevelData
from v3data.daily import DailyChart

app = Flask(__name__)
CORS(app)

PRIVATE_BETA_TVL = 400000


@app.route('/')
def main():
    return "Visor Data"


@app.route('/charts/bollingerbands/<poolAddress>')
@app.route('/bollingerBandsChartData/<poolAddress>')
def bollingerbands_chart(poolAddress):
    periodHours = int(request.args.get("periodHours", 24))

    bband = BollingerBand(poolAddress, periodHours)

    return {'data': bband.chart_data()}


@app.route('/bollingerBandsLatest/<poolAddress>')
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


@app.route('/charts/dailyHypervisorFlows/<hypervisor_address>')
def daily_hypervisor_flows_chart_data(hypervisor_address):
    days = int(request.args.get("days", 20))

    daily = DailyChart(days)

    return {'data': daily.asset_flows(hypervisor_address)}


@app.route('/pools/<token>')
def uniswap_pools(token):
    return {"pools": pools_from_symbol(token)}


@app.route('/charts/baseRange/<hypervisor_address>')
def base_range_chart(hypervisor_address):
    baseLimitData = BaseLimit(hypervisor_address)
    chart_data = baseLimitData.rebalance_ranges(hours=336)
    if chart_data:
        return {'data': chart_data}
    else:
        return Response("Invalid hypervisor address or not enough data", status=400)


@app.route('/hypervisor/<hypervisor_address>/basicStats')
def hypervisor_basic_stats(hypervisor_address):
    hypervisor = HypervisorData()
    basic_stats = hypervisor.basic_stats(hypervisor_address)

    if basic_stats:
        return basic_stats
    else:
        return Response("Invalid hypervisor address or not enough data", status=400)


@app.route('/hypervisor/<hypervisor_address>/returns')
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


@app.route('/visr/basicStats')
def visr_basic_stats():
    visr = VisrData()
    token_data = visr.token_data()
    visr_price_usd = visr.price_usd()

    token_data['priceUSD'] = visr_price_usd

    return token_data


@app.route('/visr/yield')
def visr_yield():
    visr = VisrData()
    yield_data = visr.token_yield()

    return yield_data


@app.route('/visr/dailyDistribution')
def visr_distributions():
    days = int(request.args.get("days", 5))
    visr = VisrData()
    distributions = visr.daily_distribution(days)

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


@app.route('/dashboard')
def dashboard():
    period = request.args.get("period", "weekly").lower()

    visr = VisrData()
    token_data = visr.token_data()
    visr_price_usd = visr.price_usd()
    visr_yield = visr.token_yield()
    distributions = visr.daily_distribution(1)

    last_day_distribution = float(distributions[0]['distributed'])

    top_level = TopLevelData()
    top_level_data = top_level.all_stats()
    top_level_returns = top_level.calculate_returns()

    dashboard_stats = {
        "stakedUsdAmount": token_data['totalStaked'] * visr_price_usd,
        "stakedAmount": token_data['totalStaked'],
        "feeStatsFeeAccural": last_day_distribution * visr_price_usd,
        "feeStatsAmountVisr": last_day_distribution,
        "feeStatsStakingApr": visr_yield[period]['apr'],
        "feeStatsStakingApy": visr_yield[period]['apy'],
        "feeStatsStakingDailyYield": visr_yield[period]['yield'],
        "feeCumulativeFeeUsd": token_data['totalDistributedUSD'],
        "feeCumulativeFeeUsdAnnual": visr_yield[period]['estimatedAnnualDistributionUSD'],
        "feeCumulativeFeeDistributed": token_data['totalDistributed'],
        "feeCumulativeFeeDistributedAnnual": visr_yield[period]['estimatedAnnualDistribution'],
        "uniswapPairTotalValueLocked": top_level_data['tvl'] + PRIVATE_BETA_TVL,
        "uniswapPairAmountPairs": top_level_data['pool_count'],
        "uniswapFeesGenerated": top_level_data['fees_claimed'],
        "uniswapFeesBasedApr": f"{top_level_returns[period]['feeApr']:.0%}",
        "visrPrice": visr_price_usd,  # End point for price
        "id": 2  # What is this?
    }

    return dashboard_stats
