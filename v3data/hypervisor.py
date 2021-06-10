import numpy as np
from  datetime import timedelta
from pandas import DataFrame

from v3data.data import UniV3SubgraphClient
from v3data.utils import timestamp_ago
from v3data.config import VISOR_SUBGRAPH_URL

YEAR_SECONDS = 60 * 60 * 24 * 365


class Hypervisor(UniV3SubgraphClient):
    def __init__(self):
        super().__init__(VISOR_SUBGRAPH_URL)

    def get_24hrs_rebalance_data(self):
        query = """
        query rebalances($timestamp_start: Int!){
            uniswapV3Rebalances(
                first: 1000
                where: {
                    timestamp_gte: $timestamp_start
                }
            ) {
                grossFeesUSD
                protocolFeesUSD
                netFeesUSD
            }
        }
        """
        timestamp_start = timestamp_ago(timedelta(hours=24))
        variables = {"timestamp_start": timestamp_start}
        return self.query(query, variables)['data']['uniswapV3Rebalances']

    def get_rebalance_data(self, hypervisor_address, time_delta):
        query = """
        query rebalances($hypervisor: String!, $timestamp_start: Int!){
            uniswapV3Rebalances(
                first: 1000
                where: {
                    hypervisor: $hypervisor
                    timestamp_gte: $timestamp_start
                }
            ) {
                id
                timestamp
                grossFeesUSD
                protocolFeesUSD
                netFeesUSD
                totalAmountUSD
            }
        }
        """
        timestamp_start = timestamp_ago(time_delta)
        variables = {
            "hypervisor": hypervisor_address,
            "timestamp_start": timestamp_start
        }
        return self.query(query, variables)['data']['uniswapV3Rebalances']

    def get_hypervisor_data(self):
        query = """
        {
            uniswapV3Hypervisors(
                first: 1000
            ) {
                id
                pool
                grossFeesClaimedUSD
                protocolFeesCollectedUSD
                feesReinvestedUSD
                tvlUSD
            }
        }
        """
        return self.query(query)['data']['uniswapV3Hypervisors']

    def calculate_apy(self, hypervisor_address):
        data = self.get_rebalance_data(hypervisor_address, timedelta(days=30))

        if not data:
            # Empty data usually means hypervisor address could not be found
            return False

        df = DataFrame(data, dtype=np.float64)

        df.sort_values('timestamp', inplace=True)

        # Calculate fee return rate for each rebalance event
        df['feeRate'] = df.grossFeesUSD / df.totalAmountUSD.shift(1)
        df['totalRate'] = df.totalAmountUSD / df.totalAmountUSD.shift(1) - 1

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


    def fees_24hr(self):
        data = self.get_24hrs_rebalance_data()
        df_fees = DataFrame(data, dtype=np.float64)

        return df_fees.sum().to_dict()