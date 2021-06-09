import requests
import datetime
import numpy as np
import pandas as pd

from v3data.utils import timestamp_to_date, sqrtPriceX96_to_priceDecimal
from v3data.config import V3_SUBGRAPH_ADDRESS, V3_FACTORY_ADDRESS, TOKEN_LIST_URL


class UniV3SubgraphClient:
    def __init__(self, url):
        self._url = url

    def query(self, query: str, variables=None) -> dict:
        """Make graphql query to subgraph"""
        if variables:
            params = {'query': query, 'variables': variables}
        else:
            params = {'query': query}
        response = requests.post(self._url, json=params)
        return response.json()


class UniV3Data(UniV3SubgraphClient):
    def __init__(self):
        super().__init__(V3_SUBGRAPH_ADDRESS)
        
    def get_token_list(self):
        response = requests.get(TOKEN_LIST_URL)
        token_list = response.json()['tokens']

        token_addresses = {}
        for token in token_list:
            symbol = token['symbol']
            if token_addresses.get(symbol):
                token_addresses[symbol].append(token['address'])
            else:
                token_addresses[symbol] = [token['address']]

        return token_addresses

    def get_pools_by_tokens(self, token_addresses):
        query0 = """
        query whitelistPools($ids: [String!]!)
        {
          pools(
            first: 1000
            where: {
              token0_in: $ids
            }
            orderBy: volumeUSD
            orderDirection: desc
          ) {
            id
            feeTier
            volumeUSD
            token0{
              id
              symbol
            }
            token1{
              id
              symbol
            }
          }
        }
        """
        query1 = """
        query whitelistPools($ids: [String!]!)
        {
          pools(
            first: 1000
            where: {
              token1_in: $ids
            }
            orderBy: volumeUSD
            orderDirection: desc
          ) {
            id
            feeTier
            volumeUSD
            token0{
              id
              symbol
            }
            token1{
              id
              symbol
            }
          }
        }
        """
        variables = {"ids": token_addresses}
        pool0 = self.query(query0, variables)['data']['pools']
        pool1 = self.query(query1, variables)['data']['pools']

        return pool0 + pool1

    def get_factory(self):
        """Get factory data."""
        query = """
        query factory($id: String!){
          factory(id: $id) {
            id
            poolCount
            txCount
            totalVolumeUSD
            totalValueLockedUSD
          }
        }
        """
        variables = {"id": V3_FACTORY_ADDRESS}
        self.factory = self.query(query, variables)['data']['factory']

    def get_pool(self, pool_address):
        """Get metadata for pool"""
        query = """
        query poolData($id: String!) {
          pool(
            id: $id
          ){
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
        }
        """

        variables = {"id": pool_address}
        return self.query(query, variables)['data']['pool']

    def get_pools(self):
        """Get latest factory data."""
        query = """
        query allPools($skip: Int!) {
          pools(
            first: 1000
            skip: $skip
            orderBy: volumeUSD
            orderDirection: desc
          ){
            id
            token0{
              symbol
            }
            token1{
              symbol
            }
            volumeUSD
          }
        }
        """

        self.get_factory()
        n_skips = int(self.factory['poolCount']) // 1000 + 1

        self.pools = []
        for i in range(n_skips):
            variables = {'skip': i * 1000}
            self.pools.extend(self.query(query, variables)['data']['pools'])

    def get_daily_uniswap_data(self):
        """Get aggregated daily data for uniswap v3."""
        query = """
        {
          uniswapDayDatas(
            first: 1000
            orderBy: date
            orderDirection: asc
          ) {
            id
            date
            volumeUSD
            tvlUSD
            txCount
          }
        }
        """

        self.daily_uniswap_data = self.query(query)['data']['uniswapDayDatas']

    def get_daily_pool_data(self):
        """Get daily data for pools."""

        query = """
        query allDailyPoolData($date: Int!, $skip: Int!){
          poolDayDatas(
            first: 1000
            skip: $skip
            where: { date: $date }
            orderBy: volumeUSD
            orderDirection: desc
          ){
            id
            date
            pool{
              id
              token0{symbol}
              token1{symbol}
            }
            tvlUSD
            volumeUSD
            txCount
          }
        }
        """

        self.get_daily_uniswap_data()
        self.get_factory()
        n_skips = int(self.factory['poolCount']) // 1000 + 1
        # Loop through days
        self.daily_pool_data = []
        for day in self.daily_uniswap_data:
            for i in range(n_skips):
                print(day['date'])
                variables = {"date": day['date'], "skip": i * 1000}
                self.daily_pool_data.extend((self.query(query, variables))['data']['poolDayDatas'])

    def uniswap_data(self):
        """Current TVL, volume, transaction count."""
        self.get_factory()
        data = {
            'totalValueLockedUSD': self.factory['totalValueLockedUSD'],
            'totalVolumeUSD': self.factory['totalVolumeUSD'],
            'txCount': self.factory['txCount']
        }
        return data

    def volume_pie_chart_data(self):
        """Data for pie chart of pool volumes"""
        self.get_pools()

        volume = [float(pool['volumeUSD']) for pool in self.pools]
        labels = [f"{pool['token0']['symbol']}-{pool['token1']['symbol']}" for pool in self.pools]

        data = {
            "datasets": [{
                "data": volume
            }],
            "labels": labels
        }

        return data

    def daily_volume_by_pair(self):
        """Daily volume by pair"""
        self.get_daily_pool_data()
        data = [
            {
                'pair': f"{pool_day['pool']['token0']['symbol']}-{pool_day['pool']['token1']['symbol']}",
                'date': timestamp_to_date(pool_day['date']),
                'volumeUSD': pool_day['volumeUSD']
            }
            for pool_day in self.daily_pool_data if pool_day['volumeUSD'] != '0'
        ]

        return data

    def cumulative_trade_volume(self):
        """Daily cumulative trade volume."""
        self.get_daily_uniswap_data()
        # This assumes data is ordered already
        cumulative = []
        cumulativeVolumeUSD = 0
        for uniswap_day in self.daily_uniswap_data:
            cumulativeVolumeUSD += float(uniswap_day['volumeUSD'])
            cumulative.append(
                {
                    "date": timestamp_to_date(uniswap_day['date']),
                    "cumulativeVolumeUSD": cumulativeVolumeUSD
                }
            )

        return cumulative

    def get_historical_pool_prices(self, pool_address, time_delta=None):
        query = """
            query poolPrices($id: String!, $timestamp_start: Int!){
                pool(
                    id: $id
                ){
                    swaps(
                        first: 1000
                        orderBy: timestamp
                        orderDirection: asc
                        where: { timestamp_gte: $timestamp_start }
                    ){
                        id
                        timestamp
                        sqrtPriceX96
                    }
                }
            }
        """

        if time_delta:
            timestamp_start = int((datetime.datetime.utcnow() - time_delta).replace(
                tzinfo=datetime.timezone.utc).timestamp())
        else:
            timestamp_start = 0

        variables = {
            'id': pool_address,
            "timestamp_start": timestamp_start
        }
        has_data = True
        all_swaps = []
        while has_data:
            swaps = (self.query(query, variables))['data']['pool']['swaps']

            all_swaps.extend(swaps)
            timestamps = set([int(swap['timestamp']) for swap in swaps])
            variables['timestamp_start'] = max(timestamps)

            if len(swaps) < 1000:
                has_data = False

        pool = self.get_pool(pool_address)

        df_swaps = pd.DataFrame(all_swaps, dtype=np.float64)
        df_swaps.timestamp = df_swaps.timestamp.astype(np.int64)
        df_swaps.drop_duplicates(inplace=True)
        df_swaps['priceDecimal'] = df_swaps.sqrtPriceX96.apply(
            sqrtPriceX96_to_priceDecimal, args=(int(pool['token0']['decimals']), int(pool['token1']['decimals']))
        )
        data = df_swaps.to_dict('records')

        return data

    def get_visr_price_usd(self):
        """Get VISR price from ETH/VISR 0.3% pool"""
        WETH_VISR_03_POOL = "0x9a9cf34c3892acdb61fb7ff17941d8d81d279c75"

        query = """
        query visrPrice($id: String!){
            pool(
                id: $id
            ){
                sqrtPrice
                token0{
                    symbol
                    decimals
                }
                token1{
                    symbol
                    decimals
                }
            }
            bundle(id:1){
            ethPriceUSD
            }
        }
        """
        variables = {"id": WETH_VISR_03_POOL}
        data = self.query(query, variables)['data']

        sqrt_priceX96 = float(data['pool']['sqrtPrice'])
        decimal0 = int(data['pool']['token0']['decimals'])
        decimal1 = int(data['pool']['token1']['decimals'])
        eth_price = float(data['bundle']['ethPriceUSD'])

        visr_price_eth = sqrtPriceX96_to_priceDecimal(
            sqrt_priceX96,
            decimal0,
            decimal1
        )

        return (1 / visr_price_eth) * eth_price
