import numpy as np
import pandas as pd

from datetime import timedelta

from v3data import VisorClient
from v3data.pools import Pool, USDC_WETH_03_POOL
from v3data.utils import tick_to_priceDecimal, timestamp_ago
from v3data.constants import WETH_ADDRESS


STABLECOINS = [
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
    "0xdac17f958d2ee523a2206206994597c13d831ec7",  # USDT
    "0x6b175474e89094c44da98b954eedeac495271d0f"   # DAI
]

OVERRIDE_TS = [
    1625162739,
    1625332777
]


class BaseLimit:
    def __init__(self, hours, chart=True):
        self.hours = hours
        self.timestamp_start = timestamp_ago(timedelta(hours=hours))
        self.visor_client = VisorClient()
        self.chart = chart
        self.pool_hourly = {}
        self.eth_hourly = {}

    def _get_pool_data(self, pool_addresses):
        pool_addresses.append(USDC_WETH_03_POOL)

        pool = Pool()
        pool_data = pool.hourly_prices(pool_addresses, self.hours)

        self.eth_hourly = pool_data[USDC_WETH_03_POOL]
        self.pool_hourly = pool_data

    def _reshape(self, data):
        """Reshape/flatten query data"""
        rebalances = data['rebalances']

        for rebalance in rebalances:
            for limit in ['baseLower', 'baseUpper', 'limitLower', 'limitUpper']:
                rebalance[limit] = tick_to_priceDecimal(
                    rebalance[limit],
                    int(data['pool']['token0']['decimals']),
                    int(data['pool']['token1']['decimals'])
                )

        token0_id = data['pool']['token0']['id']
        token1_id = data['pool']['token1']['id']

        if token0_id == WETH_ADDRESS:
            weth_token = 0
        elif token1_id == WETH_ADDRESS:
            weth_token = 1
        else:
            weth_token = None

        rebalances = {
            "pool": data['pool']['id'],
            "token0_name": data['pool']['token0']['symbol'],
            "token1_name": data['pool']['token1']['symbol'],
            "weth_token": weth_token,
            "is_stablecoin": True if token0_id in STABLECOINS or token1_id in STABLECOINS else False,
            "rebalances": rebalances
        }

        return rebalances

    def _get_data(self, hypervisor_address):
        """Get data for one hypervisor"""
        hypervisor_address = hypervisor_address.lower()
        query = """
        query historicalRanges($id: String!, $timestampStart: Int!){
            uniswapV3Hypervisor(
                id: $id
            ){
                pool{
                    id
                    token0{
                        id
                        symbol
                        decimals
                    }
                    token1{
                        id
                        symbol
                        decimals
                    }
                }
                rebalances(
                    first: 1000
                    where: {timestamp_gte: $timestampStart}
                    orderBy: timestamp
                    orderDirection: desc
                ){
                    timestamp
                    tick
                    baseLower
                    baseUpper
                    limitLower
                    limitUpper
                }
            }
        }
        """
        variables = {
            "id": hypervisor_address,
            "timestampStart": self.timestamp_start
        }

        data = self.visor_client.query(query, variables)['data']['uniswapV3Hypervisor']

        return self._reshape(data)

    def _get_all_data(self):
        """Get data for all hypervisors"""
        query = """
        query historicalRanges($timestampStart: Int!){
            uniswapV3Hypervisors(
                first:1000
            ){
                id
                pool{
                    id
                    token0{
                        id
                        symbol
                        decimals
                    }
                    token1{
                        id
                        symbol
                        decimals
                    }
                }
                rebalances(
                    first: 1000
                    where: {timestamp_gte: $timestampStart}
                    orderBy: timestamp
                    orderDirection: desc
                ){
                    timestamp
                    tick
                    baseLower
                    baseUpper
                    limitLower
                    limitUpper
                }
            }
        }
        """
        variables = {"timestampStart": self.timestamp_start}
        data = self.visor_client.query(query, variables)['data']['uniswapV3Hypervisors']

        return {hypervisor['id']: self._reshape(hypervisor) for hypervisor in data}

    def _rebalance_ranges(self, rebalance_data):
        """Interpolate prices and rebalance ranges for complete set of data"""
        # For stables, if WETH = 1 then flip
        rebalances = pd.DataFrame(rebalance_data['rebalances'], dtype=np.float64)
        if rebalances.empty:
            return []

        hourly_prices = pd.DataFrame(self.pool_hourly[rebalance_data['pool']], dtype=np.float64)

        df_data = pd.concat([
            rebalances[['timestamp', 'baseLower', 'baseUpper', 'limitLower', 'limitUpper']],
            hourly_prices[['timestamp', 'price']]
        ]).sort_values('timestamp').set_index('timestamp')

        # Remove outlier
        if rebalance_data['token0_name'] == 'USDC':
            drop_ts = set(OVERRIDE_TS).intersection(set(df_data.index))
            df_data.drop(drop_ts, inplace=True)

        token0_is_stable = (rebalance_data['is_stablecoin'] and rebalance_data['weth_token'] == 1)
        token1_is_token = (not rebalance_data['is_stablecoin'] and rebalance_data['weth_token'] == 0)

        # If stables, show price of ETH. otherwise show token price in terms of ETH
        if token0_is_stable or token1_is_token:
            df_data = 1 / df_data
            pair_name = f"{rebalance_data['token1_name']}-{rebalance_data['token0_name']}"
        else:
            pair_name = f"{rebalance_data['token0_name']}-{rebalance_data['token1_name']}"

        # Intepolate prices
        df_data.price = df_data.price.interpolate()
        # Extend rebalance ranges
        df_data = df_data.fillna(method='ffill').dropna().reset_index()

        df_data['date'] = pd.to_datetime(df_data.timestamp, unit='s').dt.strftime('%Y-%m-%dT%H:%M:%SZ')

        if self.chart:
            df_data.rename(
                columns={
                    "price": "value",
                    "baseLower": "min",
                    "baseUpper": "max"
                }, inplace=True
            )
            df_data['group'] = pair_name
            df_data = df_data[['group', 'date', 'value', 'min', 'max']]
        else:
            df_data = df_data[[
                'date',
                'price',
                'baseLower',
                'baseUpper',
                'limitLower',
                'limitUpper'
            ]]

        return df_data.to_dict('records')

    def rebalance_ranges(self, hypervisor_address):
        """Get price/rebalance ranges for one hypervisor"""
        data = self._get_data(hypervisor_address)
        self._get_pool_data([data['pool']])
        return self._rebalance_ranges(data)

    def all_rebalance_ranges(self):
        """Get price/rebalance ranges for all hypervisor"""
        data = self._get_all_data()
        self._get_pool_data([hypervisor_data['pool'] for _, hypervisor_data in data.items()])
        return {hypervisor_id: self._rebalance_ranges(rebalances) for hypervisor_id, rebalances in data.items()}
