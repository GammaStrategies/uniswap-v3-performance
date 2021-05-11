#!/usr/bin/env python

import json

from bottle import route, run
from v3data.data import UniV3Data

v3data = UniV3Data()


@route('/uniswap/tvl')
def total_value_locked():
    data = v3data.uniswap_data()
    return data['totalValueLockedUSD']


@route('/uniswap/totalVolume')
def total_volume():
    data = v3data.uniswap_data()
    return data['totalVolumeUSD']


@route('/uniswap/txCount')
def tx_count():
    data = v3data.uniswap_data()
    return data['txCount']


@route('/uniswap/cumulativeVolume')
def cumulative_trade_volume():
    data = v3data.cumulative_trade_volume()
    return json.dumps(data)


@route('/pools/dailyVolume')
def hourly_pool_volume():
    data = v3data.daily_volume_by_pair()
    return json.dumps(data)


@route('/pools/totalVolumePieChart')
def total_volume_pie_chart():
    data = v3data.volume_pie_chart_data()
    return json.dumps(data)


@route('/pools/historicalPrice/<address>')
def pool_historical_price(address):
    data = v3data.get_historical_pool_prices(address)
    return json.dumps(data)


run(host='localhost', port=8080)
