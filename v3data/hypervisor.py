import numpy as np
from datetime import timedelta
from pandas import DataFrame

from v3data import VisorClient
from v3data.utils import timestamp_ago

DAY_SECONDS = 24 * 60 * 60
YEAR_SECONDS = 365 * DAY_SECONDS


class HypervisorData:
    def __init__(self):
        self.visor_client = VisorClient()

    def get_rebalance_data(self, hypervisor_address, time_delta, limit=1000):
        query = """
        query rebalances($hypervisor: String!, $timestamp_start: Int!, $limit: Int!){
            uniswapV3Rebalances(
                first: $limit
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
            "hypervisor": hypervisor_address.lower(),
            "timestamp_start": timestamp_start,
            "limit": limit
        }
        return self.visor_client.query(query, variables)['data']['uniswapV3Rebalances']

    def get_hypervisor_data(self, hypervisor_address):
        query = """
        query hypervisor($id: String!){
            uniswapV3Hypervisor(
                id: $id
            ) {
                id
                grossFeesClaimedUSD
                protocolFeesCollectedUSD
                feesReinvestedUSD
                tvlUSD
            }
        }
        """
        variables = {"id": hypervisor_address.lower()}
        return self.visor_client.query(query, variables)['data']['uniswapV3Hypervisor']

    def basic_stats(self, hypervisor_address):
        data = self.get_hypervisor_data(hypervisor_address)
        return data

    def calculate_returns(self, hypervisor_address):
        data = self.get_rebalance_data(hypervisor_address, timedelta(days=30))

        if not data:
            # Empty data usually means hypervisor address could not be found
            return False

        df_rebalances = DataFrame(data, dtype=np.float64)

        df_rebalances.sort_values('timestamp', inplace=True)

        # Calculate fee return rate for each rebalance event
        df_rebalances['feeRate'] = df_rebalances.grossFeesUSD / df_rebalances.totalAmountUSD.shift(1)
        df_rebalances['totalRate'] = df_rebalances.totalAmountUSD / df_rebalances.totalAmountUSD.shift(1) - 1

        # Time since last rebalance
        df_rebalances['periodSeconds'] = df_rebalances.timestamp.diff()

        periods = {
            "daily": 1,
            "weekly": 7,
            "monthly": 30
        }

        # Calculate returns for using last 1, 7, and 30 days data
        results = {}
        for period, days in periods.items():
            timestamp_start = timestamp_ago(timedelta(days=days))
            df_period = df_rebalances.loc[df_rebalances.timestamp > timestamp_start].copy()

            if df_period.empty:
                # if no rebalances in the last 24 hours, calculate using the 24 hours prior to the last rebalance
                df_rebalances.timestamp.max() - DAY_SECONDS
                timestamp_start = df_rebalances.timestamp.max() - DAY_SECONDS
                df_period = df_rebalances.loc[df_rebalances.timestamp > timestamp_start].copy()

            # Time since first reblance
            df_period['totalPeriodSeconds'] = df_period.periodSeconds.cumsum()

            # Compound fee return rate for each rebalance
            df_period['cumFeeReturn'] = (1 + df_period.feeRate).cumprod() - 1
            df_period['cumTotalReturn'] = (1 + df_period.totalRate).cumprod() - 1

            # Last row is the cumulative results
            returns = df_period[['totalPeriodSeconds', 'cumFeeReturn']].tail(1)  # , 'cumTotalReturn'

            # Extrapolate linearly to annual rate
            returns['feeApr'] = returns.cumFeeReturn * (YEAR_SECONDS / returns.totalPeriodSeconds)

            # Extrapolate by compounding
            returns['feeApy'] = (1 + returns.cumFeeReturn * (DAY_SECONDS / returns.totalPeriodSeconds)) ** 365 - 1

            results[period] = returns.to_dict('records')[0]

        return results
