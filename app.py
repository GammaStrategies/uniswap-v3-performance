from flask import Flask, request, Response
from flask_cors import CORS

from v3data.pools import pools_from_symbol
from v3data.bollingerbands import BollingerBand
from v3data.hypervisor import Hypervisor
from v3data.visr import VisrData
from v3data.toplevel import TopLevelData

app = Flask(__name__)
CORS(app)


@app.route('/')
def main():
    return "Visor Data"


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


@app.route('/pools/<token>')
def uniswap_pools(token):
    return {"pools": pools_from_symbol(token)}


@app.route('/hypervisor/<hypervisorAddress>/apy')
def hypervisor_apy(hypervisorAddress):
    hypervisor = Hypervisor()
    apy = hypervisor.calculate_apy(hypervisorAddress)

    if apy:
        return apy
    else:
        return Response("Invalid hypervisor address", status=400)


@app.route('/visr/basicStats')
def basic_stats():
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
    return {
        'nDays': len(distributions),
        'dailyDistribution': distributions
    }


@app.route('/uniswapV3Hypervisors/aggregateStats')
def aggregate_stats():
    top_level = TopLevelData()
    top_level_data = top_level.all_stats()

    private_beta_tvl = 400000

    return {
        'totalValueLockedUSD': top_level_data['tvl'] + private_beta_tvl,
        'pairCount': top_level_data['pool_count'],
        'totalFeesClaimedUSD': top_level_data['fees_claimed']
    }


@app.route('/uniswapV3Hypervisors/recentFees')
def recent_fees():
    hours = int(request.args.get("hours", 24))
    top_level = TopLevelData()
    recent_fees = top_level.recent_fees(hours)

    return {
        "periodHours": hours,
        "fees": recent_fees
    }


@app.route('/dashboard')
def dashboard():

    dashboard_stats = {
        "uniswapFeesBasedApr": "Todo",
    }

    return None
