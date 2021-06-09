import numpy as np
from pandas import DataFrame

from v3data.data import UniV3SubgraphClient
from v3data.config import VISOR_SUBGRAPH_URL
from v3data.utils import timestamp_to_date

class Visr(UniV3SubgraphClient):
    def __init__(self):
        super().__init__(VISOR_SUBGRAPH_URL)
        self.decimal_factor = 10 ** 18

    def get_token_data(self):
        query = """
        {
            visrToken(
                id:"0xf938424f7210f31df2aee3011291b658f872e91e"
            ){
                totalSupply
                totalDistributed
                totalStaked
            }
        }
        """
        return self.query(query)['data']['visrToken']

    def get_token_day_data(self):
        query = """
        {
            visrTokenDayDatas(
                orderBy: date
                orderDirection: desc
                first: 30
                where: {
                    distributed_gt: 0
                    totalStaked_gt: 0
                }
            ){
                date
                distributed
                totalStaked
            }
        }
        """
        return self.query(query)['data']['visrTokenDayDatas']

    def token_data(self):
        data = self.get_token_data()

        return {
            "distributed": int(data['totalDistributed']) / self.decimal_factor,
            "staked": int(data['totalStaked']) / self.decimal_factor,
            "total": int(data['totalSupply']) / self.decimal_factor
        }

    def period_estimates(self):
        """Gets estimates such as APY, visor distributed"""
        day_data = self.get_token_day_data()
        df_day_data = DataFrame(day_data, dtype=np.float64)
        df_day_data['dailyYield'] = df_day_data.distributed / df_day_data.totalStaked
        df_day_data = df_day_data.sort_values('date')

        periods = {
            "daily": 1,
            "weekly": 7,
            "monthly": 30
        }

        results = {}
        for period, days in periods.items():
            df_period = df_day_data.tail(days).copy()
            n_days = len(df_period)
            df_period['cumReturn'] = (1 + df_period['dailyYield']).cumprod() - 1
            period_yield = df_period['cumReturn'].iat[-1]
            results[period] = {}
            results[period]['yield'] = period_yield
            results[period]['apy'] = period_yield * 365 / n_days
            results[period]['visrDistributedAnnual'] = (df_period.distributed.sum() / self.decimal_factor) * 365 / n_days

        return results


    def recent_distributions(self, days=5):
        data = self.get_token_day_data()
        results = [
            {
                "timestamp": day['date'],
                "date": timestamp_to_date(day['date']),
                "distributed": float(day['distributed']) / self.decimal_factor
            }
            for day in data[:days]
        ]

        return results
