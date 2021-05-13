#!/usr/bin/env python

import json

from bottle import get, request, abort, run
from v3data.data import UniV3Data
from v3data.config import POOL_ADDRESSES

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

@get('/bollingerBands')
def pool_historical_price():
    if not request.query.pool:
        abort(400, "Missing pool parameter, e.g. ?pool=WETH/USDT")
    if not request.query.periodHours:
        abort(400, "Missing periodHours parameter e.g. ?periodHours=24")

    pool_address = POOL_ADDRESSES.get(request.query.pool)
    if not pool_address:
        abort(422, "Pool not supported")

    period_hours = int(request.query.periodHours)
    data = v3data.bollinger_bands(pool_address, period_hours)
    return json.dumps(data)


run(host='localhost', port=8080)
