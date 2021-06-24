import datetime
from v3data import UniswapV3Client
from v3data.data import UniV3Data
from v3data.utils import sqrtPriceX96_to_priceDecimal


def pools_from_symbol(symbol):
    client = UniV3Data()
    token_list = client.get_token_list()
    token_addresses = token_list.get(symbol.upper())
    pool_list = client.get_pools_by_tokens(token_addresses)

    pools = [
        {
            "token0Address": pool['token0']['id'],
            "token1Address": pool['token1']['id'],
            "poolAddress": pool['id'],
            'symbol': f"{pool['token0']['symbol']}-{pool['token1']['symbol']}",
            'feeTier': pool['feeTier'],
            'volumeUSD': pool['volumeUSD']
        } for pool in pool_list
    ]

    return pools


class Pool:
    def __init__(self, address):
        self.address = address.lower()
        self.client = UniswapV3Client()
        self._init()

    def _init(self):
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
        variables = {"id": self.address}
        data = self.client.query(query, variables)['data']['pool']

        self.symbol0 = data['token0']['symbol']
        self.symbol1 = data['token1']['symbol']

        self.decimal0 = int(data['token0']['decimals'])
        self.decimal1 = int(data['token1']['decimals'])

    def swap_prices(self, time_delta=None):
        query = """
        query poolPrices($pool: String!, $timestampStart: Int!, $paginate: String!){
            swaps(
                first: 1000
                pool: $pool
                orderBy: id
                orderDirection: asc
                where: {
                    timestamp_gte: $timestampStart
                    id_gt: $paginate
                }
            ){
                id
                timestamp
                sqrtPriceX96
            }
        }
        """
        if time_delta:
            timestamp_start = int((datetime.datetime.utcnow() - time_delta).replace(
                tzinfo=datetime.timezone.utc).timestamp())
        else:
            timestamp_start = 0

        variables = {
            "pool": self.address,
            "timestampStart": timestamp_start,
            "paginate": ""
        }
        data = self.client.paginate_query(query, "id", variables)
        return data

    def hourly_prices(self, hours):
        query = """
        query poolPrices($pool: String!, $hours: Int!){
            poolHourDatas(
                first: $hours
                orderBy: id
                orderDirection: desc
                where: {pool: $pool, sqrtPrice_gt: 0}
            ){
                periodStartUnix
                sqrtPrice
            }
        }
        """
        variables = {
            "pool": self.address,
            "hours": hours
        }
        data = self.client.query(query, variables)['data']['poolHourDatas']

        for record in data:
            record['timestamp'] = record.pop('periodStartUnix')
            record['price'] = sqrtPriceX96_to_priceDecimal(float(record['sqrtPrice']), self.decimal0, self.decimal1)

        return data
