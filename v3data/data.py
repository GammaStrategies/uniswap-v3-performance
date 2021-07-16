import requests
import datetime
import numpy as np
import pandas as pd

from v3data import SubgraphClient
from v3data.utils import sqrtPriceX96_to_priceDecimal
from v3data.config import UNI_V3_SUBGRAPH_URL, TOKEN_LIST_URL


class UniV3Data(SubgraphClient):
    def __init__(self):
        super().__init__(UNI_V3_SUBGRAPH_URL)

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
        variables = {"ids": [address.lower() for address in token_addresses]}
        pool0 = self.query(query0, variables)['data']['pools']
        pool1 = self.query(query1, variables)['data']['pools']

        return pool0 + pool1

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

        variables = {"id": pool_address.lower()}
        return self.query(query, variables)['data']['pool']

    def get_historical_pool_prices(self, pool_address, time_delta=None):
        pool_address = pool_address.lower()
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
