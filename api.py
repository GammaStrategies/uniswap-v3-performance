#!/usr/bin/env python

import json

from bottle import get, request, abort, run, hook, response, route
from v3data.data import UniV3Data
from v3data.pools import pools_from_symbol
from v3data.bollingerbands import BollingerBand
from v3data.config import POOL_ADDRESSES

_allow_origin = '*'
_allow_methods = 'PUT, GET, POST, DELETE, OPTIONS'
_allow_headers = 'Authorization, Origin, Accept, Content-Type, X-Requested-With'

@hook('after_request')
def enable_cors():
    '''Add headers to enable CORS'''

    response.headers['Access-Control-Allow-Origin'] = _allow_origin
    response.headers['Access-Control-Allow-Methods'] = _allow_methods
    response.headers['Access-Control-Allow-Headers'] = _allow_headers

@route('/', method = 'OPTIONS')
@route('/<path:path>', method = 'OPTIONS')
def options_handler(path = None):
    return

v3data = UniV3Data()


@get('/uniswap/tvl')
def total_value_locked():
    data = v3data.uniswap_data()
    return data['totalValueLockedUSD']


@get('/uniswap/totalVolume')
def total_volume():
    data = v3data.uniswap_data()
    return data['totalVolumeUSD']


@get('/uniswap/txCount')
def tx_count():
    data = v3data.uniswap_data()
    return data['txCount']


@get('/uniswap/cumulativeVolume')
def cumulative_trade_volume():
    data = v3data.cumulative_trade_volume()
    return json.dumps(data)


@get('/pools/dailyVolume')
def hourly_pool_volume():
    data = v3data.daily_volume_by_pair()
    return json.dumps(data)


@get('/pools/totalVolumePieChart')
def total_volume_pie_chart():
    data = v3data.volume_pie_chart_data()
    return json.dumps(data)


@get('/pools/historicalPrice/<address>')
def pool_historical_price(address):
    data = v3data.get_historical_pool_prices(address)
    return json.dumps(data)

@get('/bollingerBandsChartData')
def bollingerbands_chart():
    if not request.query.poolAddress:
        abort(400, "Missing poolAddress parameter, e.g. ?pool=0xfwfe...")
    if not request.query.periodHours:
        abort(400, "Missing periodHours parameter e.g. ?periodHours=24")

    bband = BollingerBand(request.query.poolAddress, int(request.query.periodHours))

    return {'data': bband.chart_data()}

@get('/pools/<token>')
def whitelist_pools(token):
    return {"pools": pools_from_symbol(token)}


run(host='localhost', port=8080)
