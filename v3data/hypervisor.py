import numpy as np
from pandas import DataFrame

from v3data.data import UniV3SubgraphClient

HYPERVISOR_SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/l0c4t0r/visor"
YEAR_SECONDS = 60 * 60 * 24 * 365


class Hypervisor(UniV3SubgraphClient):
    def __init__(self):
        super().__init__(HYPERVISOR_SUBGRAPH_URL)

    def get_rebalance_data(self):
        query = """
            {
                uniswapV3Rebalances(
                    first: 1000
                    where: {
                        hypervisor: "0xa08583b36a809934e019574695392b516be9354f"
                    }
                ) {
                    id
                    timestamp
                    tick
                    totalAmount0
                    totalAmount1
                    feeAmount0
                    feeAmount1
                    totalSupply
                }
            }
        """
        return self.query(query)['data']['uniswapV3Rebalances']

    def calculate_apy(self):
        data = self.get_rebalance_data()
        df = DataFrame(data, dtype=np.float64)

        # Convert tick to price
        df['price'] = 1.0001 ** df.tick

        # Calculate total amounts and fees in Token1
        df['totalAmountInToken1'] = df.totalAmount0 * df.price + df.totalAmount1  # Current tokens are current price
        df['totalFeeInToken1'] = df.feeAmount0 * df.price + df.feeAmount1

        df['totalInToken1'] = df.totalAmountInToken1 + df.totalFeeInToken1

        df.sort_values('timestamp', inplace=True)

        # Calculate fee return rate for each rebalance event
        df['feeRate'] = df.totalFeeInToken1 / df.totalInToken1.shift(1)
        df['totalRate'] = df.totalInToken1 / df.totalInToken1.shift(1) - 1

        # Time since last rebalance
        df['periodSeconds'] = df.timestamp.diff()

        # Time since first reblance
        df['cumPeriodSeconds'] = df.periodSeconds.cumsum()

        # Compound fee return rate for each rebalance
        df['cumFeeReturn'] = (1 + df['feeRate']).cumprod() - 1
        df['cumTotalReturn'] = (1 + df['totalRate']).cumprod() - 1

        # Extrapolate linearly to annual rate
        df['apyFee'] = df.cumFeeReturn * (YEAR_SECONDS / df.cumPeriodSeconds)

        return df[['cumPeriodSeconds', 'cumFeeReturn', 'cumTotalReturn', 'apyFee']].tail(1).to_dict('records')[0]
