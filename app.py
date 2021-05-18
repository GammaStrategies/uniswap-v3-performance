from flask import Flask, request
from flask_cors import CORS

from v3data.pools import pools_from_symbol
from v3data.bollingerbands import BollingerBand

app = Flask(__name__)
CORS(app)

@app.route('/')
def main():
	return "Visor Data"

@app.route('/bollingerBandsChartData')
def bollingerbands_chart():
    pool_address = request.args.get("poolAddress")
    periodHours = int(request.args.get("periodHours", 24))

    bband = BollingerBand(pool_address, periodHours)

    return {'data': bband.chart_data()}

@app.route('/pools/<token>')
def uniswap_pools(token):
    return {"pools": pools_from_symbol(token)}
