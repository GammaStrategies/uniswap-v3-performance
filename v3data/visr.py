import numpy as np
from pandas import DataFrame

from v3data import VisorClient, UniswapV3Client
from v3data.utils import timestamp_to_date, sqrtPriceX96_to_priceDecimal


class VisrData:
    """Class for querying VISR related data"""

    def __init__(self):
        self.visor_client = VisorClient()
        self.uniswap_client = UniswapV3Client()
        self.address = "0xf938424f7210f31df2aee3011291b658f872e91e"
        self.decimal_factor = 10 ** 18

    def get_token_data(self):
        """Get basic stats from VisrToken entity"""
        query = """
        query($id: String!){
            visrToken(
                id: $id
            ){
                totalSupply
                totalDistributed
                totalDistributedUSD
                totalStaked
            }
        }
        """
        variables = {"id": self.address}
        return self.visor_client.query(query, variables)['data']['visrToken']

    def get_token_day_data(self, days=30):
        """Get daily data for VISR token"""
        query = """
        query($days: Int!){
            visrTokenDayDatas(
                orderBy: date
                orderDirection: desc
                first: $days
                where: {
                    distributed_gt: 0
                    totalStaked_gt: 0
                }
            ){
                date
                distributed
                distributedUSD
                totalStaked
            }
        }
        """
        variables = {"days": days}
        return self.visor_client.query(query, variables)['data']['visrTokenDayDatas']

    def token_data(self):
        """Returns basic info in decimal"""
        data = self.get_token_data()

        return {
            "totalDistributed": int(data['totalDistributed']) / self.decimal_factor,
            "totalDistributedUSD": float(data['totalDistributedUSD']),
            "totalStaked": int(data['totalStaked']) / self.decimal_factor,
            "totalSupply": int(data['totalSupply']) / self.decimal_factor
        }

    def token_yield(self):
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
            annual_scaling_factor = 365 / n_days

            df_period['cumReturn'] = (1 + df_period['dailyYield']).cumprod() - 1
            period_yield = df_period['cumReturn'].iat[-1]

            results[period] = {}
            results[period]['yield'] = period_yield
            results[period]['apy'] = period_yield * annual_scaling_factor
            results[period]['estimatedAnnualDistribution'] = (df_period.distributed.sum() / self.decimal_factor) * annual_scaling_factor
            results[period]['estimatedAnnualDistributionUSD'] = df_period.distributedUSD.sum() * annual_scaling_factor

        return results

    def daily_distribution(self, days=5):
        """Get most recent VISR distribution amounts"""
        data = self.get_token_day_data(days)
        results = [
            {
                "timestamp": day['date'],
                "date": timestamp_to_date(day['date'], '%B %d, %Y'),
                "distributed": float(day['distributed']) / self.decimal_factor
            }
            for day in data
        ]

        return results

    def price_usd(self):
        """Get VISR price from ETH/VISR 0.3% pool"""
        WETH_VISR_03_POOL = "0x9a9cf34c3892acdb61fb7ff17941d8d81d279c75"

        query = """
        query visrPrice($id: String!){
            pool(
                id: $id
            ){
                sqrtPrice
                token0{
                    symbol
                    decimals
                }
                token1{
                    symbol
                    decimals
                }
            }
            bundle(id:1){
            ethPriceUSD
            }
        }
        """
        variables = {"id": WETH_VISR_03_POOL}
        data = self.uniswap_client.query(query, variables)['data']

        sqrt_priceX96 = float(data['pool']['sqrtPrice'])
        decimal0 = int(data['pool']['token0']['decimals'])
        decimal1 = int(data['pool']['token1']['decimals'])
        eth_price = float(data['bundle']['ethPriceUSD'])

        visr_price_eth = sqrtPriceX96_to_priceDecimal(
            sqrt_priceX96,
            decimal0,
            decimal1
        )

        return eth_price / visr_price_eth
