import numpy as np
from  datetime import timedelta
from pandas import DataFrame

from v3data.data import UniV3SubgraphClient
from v3data.config import VISOR_SUBGRAPH_URL


class Factory(UniV3SubgraphClient):
    def __init__(self):
        super().__init__(VISOR_SUBGRAPH_URL)

    def get_factory_data(self):
        query = """
        {
            uniswapV3HypervisorFactories(
                first: 1000
            ){
                id
                tvlUSD
            }
        }
        """
        return self.query(query)['data']['uniswapV3HypervisorFactories']

    def tvl(self):
        data = self.get_factory_data()
        return sum([float(factory['tvlUSD']) for factory in data])
    

