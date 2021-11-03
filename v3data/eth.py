import numpy as np
from pandas import DataFrame

from v3data import VisorClient, UniswapV3Client
from v3data.config import DEFAULT_TIMEZONE
from v3data.utils import timestamp_to_date, sqrtPriceX96_to_priceDecimal
from v3data.constants import DAYS_IN_PERIOD


class EthData:
    def __init__(self, days, timezone=DEFAULT_TIMEZONE):
        self.visor_client = VisorClient()
        self.days = days
        self.timezone = timezone
        self.decimal_factor = 10 ** 18
        self.data = {}

    def _get_data(self):

        query = """
        query($days: Int!, $timezone: String!){
            ethToken(
                id: "0"
            ){
                totalDistributed
                totalDistributedUSD
            }
            ethDayDatas(
                orderBy: date
                orderDirection: desc
                first: $days
                where: {
                    distributed_gt: 0
                    timezone: $timezone
                }
            ){
                date
                distributed
                distributedUSD
            }
        }
        """
        variables = {
            "days": self.days,
            "timezone": self.timezone
        }
        self.data = self.visor_client.query(query, variables)['data']


class EthCalculations(EthData):
    def __init__(self, days=30):
        super().__init__(days=days)

    def basic_info(self, get_data=True):
        if get_data:
            self._get_data()

        data = self.data['ethToken']

        return {
            "totalDistributed": int(data['totalDistributed']) / self.decimal_factor,
            "totalDistributedUSD": float(data['totalDistributedUSD'])
        }

    def distributions(self, get_data=True):

        if get_data:
            self._get_data()

        results = [
            {
                "timestamp": day['date'],
                "date": timestamp_to_date(int(day['date']), '%B %d, %Y'),
                "distributed": float(day['distributed']) / self.decimal_factor
            }
            for day in self.data['ethDayDatas']
        ]

        return results


class EthDistribution(EthCalculations):
    def __init__(self, days=6, timezone=DEFAULT_TIMEZONE):
        super().__init__(days=days)

    def output(self):
        distributions = self.distributions(get_data=True)

        fee_distributions = []
        for i, distribution in enumerate(distributions):
            fee_distributions.append(
                {
                    'title': distribution['date'],
                    'desc': f"{float(distribution['distributed']):.2f} ETH Distributed",
                    'id': i + 2
                }
            )

        return {
            'feeDistribution': fee_distributions
        }
