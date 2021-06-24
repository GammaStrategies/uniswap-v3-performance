import numpy as np
import pandas as pd

from datetime import timedelta

from v3data import VisorClient
from v3data.pools import Pool
from v3data.utils import timestamp_to_date, tick_to_priceDecimal, timestamp_ago


class BaseLimit:
    def __init__(self, hypervisor_address):
        self.address = hypervisor_address.lower()
        self.visor_client = VisorClient()

    def _get_data(self, timestamp_start):
        query = """
        query historicalRanges($id: String!, $timestampStart: Int!){
            uniswapV3Hypervisor(
                id: $id
            ){
                pool{
                    id
                    token0{
                        symbol
                        decimals
                    }
                    token1{
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
            "id": self.address,
            "timestampStart": timestamp_start
        }

        data = self.visor_client.query(query, variables)['data']['uniswapV3Hypervisor']
        rebalances = data['rebalances']

        for rebalance in rebalances:
            for limit in ['baseLower', 'baseUpper', 'limitLower', 'limitUpper']:
                rebalance[limit] = tick_to_priceDecimal(
                    rebalance[limit],
                    int(data['pool']['token0']['decimals']),
                    int(data['pool']['token1']['decimals'])
                )

        self.pool = data['pool']['id']
        self.name = f"{data['pool']['token0']['symbol']}-{data['pool']['token1']['symbol']}"
        self.rebalances = rebalances

    def rebalance_ranges(self, hours, chart=True):
        self._get_data(timestamp_ago(timedelta(hours=hours)))
        rebalances = pd.DataFrame(self.rebalances, dtype=np.float64)
        if rebalances.empty:
            return False
        pool = Pool(self.pool)
        hourly_prices = pd.DataFrame(pool.hourly_prices(hours), dtype=np.float64)

        df_data = pd.concat([
            rebalances[['timestamp', 'baseLower', 'baseUpper', 'limitLower', 'limitUpper']],
            hourly_prices[['timestamp', 'price']]
        ]).sort_values('timestamp').set_index('timestamp')

        df_data.price = df_data.price.interpolate()
        df_data = df_data.fillna(method='ffill').dropna().reset_index()

        df_data['date'] = pd.to_datetime(df_data.timestamp, unit='s').dt.strftime('%Y-%m-%dT%H:%M:%SZ')

        if chart:
            df_data.rename(
                columns={
                    "price": "value",
                    "baseLower": "min",
                    "baseUpper": "max"
                }, inplace=True
            )
            df_data['group'] = self.name
            df_data = df_data[['group', 'date', 'value', 'min', 'max']]
        else:
            df_data = df_data[['date', 'price', 'baseLower', 'baseUpper', 'limitLower', 'limitUpper']]            

        return df_data.to_dict('records')
