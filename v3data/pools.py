from v3data.data import UniV3Data
from v3data.data import UniV3SubgraphClient
from v3data.config import VISOR_SUBGRAPH_URL

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


class Pool(UniV3SubgraphClient):
    def __init__(self):
        super().__init__(VISOR_SUBGRAPH_URL)

    def get_pool_data(self):
        query = """
        {
            uniswapV3Pools(
                first: 1000  
            ){
                id
            }
        }
        """
        return self.query(query)['data']['uniswapV3Pools']

    def count(self):
        data = self.get_pool_data()
        return len(data)
