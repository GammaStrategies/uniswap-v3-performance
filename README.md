# analytics

Endpoints available for testing:

/uniswap/tvl

/uniswap/totalVolume

/uniswap/txCount

/uniswap/cumulativeVolume

/pools/dailyVolume

/pools/totalVolumePieChart

To get the list of v3 pools for a specific symbol:
/pools/<symbol>

To get bollinger bands for a specific pool:
/bollingerBandsChartData
with these paramaters:
poolAddress: address of pool
periodHours: The total period in hours