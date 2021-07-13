import datetime
from v3data import UniswapV3Client
from v3data.data import UniV3Data
from v3data.utils import sqrtPriceX96_to_priceDecimal

USDC_WETH_03_POOL = '0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8'


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
    def __init__(self):
        self.client = UniswapV3Client()

    def swap_prices(self, pool_address, time_delta=None):
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
            "pool": pool_address,
            "timestampStart": timestamp_start,
            "paginate": ""
        }
        data = self.client.paginate_query(query, "id", variables)
        return data

    def hourly_prices(self, pools, hours):

        query = """
        query poolPrices($pools: [String!]!, $hours: Int!){
            pools(
                where: {
                    id_in: $pools
                    }
                ){
                    id
                    token0 {
                        decimals
                    }
                    token1 {
                        decimals
                    }
                    poolHourData(
                        first: $hours
                        orderBy: id
                        orderDirection: desc
                        where: {
                            sqrtPrice_gt: 0
                        }
                    ){
                        periodStartUnix
                        sqrtPrice
                    }
                }
            }
        """
        variables = {"pools": [pool.lower() for pool in pools], "hours": hours}
        data = self.client.query(query, variables)['data']['pools']

        pool_prices = {
            pool['id']: [
                {
                    "timestamp": hour_data['periodStartUnix'],
                    "price": sqrtPriceX96_to_priceDecimal(
                        float(hour_data['sqrtPrice']),
                        int(pool['token0']['decimals']),
                        int(pool['token1']['decimals'])
                    )
                }
                for hour_data in pool['poolHourData']
            ]
            for pool in data
        }

        return pool_prices
