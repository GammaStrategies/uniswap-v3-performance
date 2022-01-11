import numpy as np
from datetime import timedelta
from pandas import DataFrame

from v3data import GammaClient, UniswapV3Client
from v3data.config import DEFAULT_TIMEZONE
from v3data.utils import timestamp_to_date, sqrtPriceX96_to_priceDecimal, timestamp_ago
from v3data.constants import DAYS_IN_PERIOD


class GammaData:
    def __init__(self, days, timezone=DEFAULT_TIMEZONE):
        self.gamma_client = GammaClient()
        self.days = days
        self.timezone = timezone
        self.address = "0x6bea7cfef803d1e3d5f7c0103f7ded065644e197"
        self.decimal_factor = 10 ** 18
        self.data = {}

    def _get_data(self):

        query = """
        query($id: String!, $days: Int!, $timezone: String!){
            visrToken(
                id: $id
            ){
                totalSupply
                totalDistributed
                totalDistributedUSD
                totalStaked
            }
            visrTokenDayDatas(
                orderBy: date
                orderDirection: desc
                first: $days
                where: {
                    distributed_gt: 0
                    totalStaked_gt: 0
                    timezone: $timezone
                }
            ){
                date
                distributed
                distributedUSD
                totalStaked
            }
            rewardHypervisor(
                id:"0x26805021988f1a45dc708b5fb75fc75f21747d8c"
            ) {
                totalVisr
            }
        }
        """
        variables = {
            "id": self.address,
            "days": self.days,
            "timezone": self.timezone
        }
        self.data = self.gamma_client.query(query, variables)['data']
        print(self.gamma_client._url)


class GammaCalculations(GammaData):
    def __init__(self, days=30):
        super().__init__(days=days)

    def basic_info(self, get_data=True):
        if get_data:
            self._get_data()

        data = self.data['visrToken']
        gammaStaked = self.data['rewardHypervisor']['totalVisr']

        return {
            "totalDistributed": int(data['totalDistributed']) / self.decimal_factor,
            "totalDistributedUSD": float(data['totalDistributedUSD']),
            "totalStaked": int(gammaStaked) / self.decimal_factor,
            "totalSupply": int(data['totalSupply']) / self.decimal_factor
        }

    def gamma_yield(self, get_data=True):
        """Gets estimates such as APY, visor distributed"""

        if get_data:
            self._get_data()

        df_data = DataFrame(self.data['visrTokenDayDatas'], dtype=np.float64)
        df_data.totalStaked = int(self.data['rewardHypervisor']['totalVisr'])
        df_data['dailyYield'] = df_data.distributed / df_data.totalStaked
        df_data = df_data.sort_values('date')

        results = {}
        for period, days in DAYS_IN_PERIOD.items():
            df_period = df_data.tail(days).copy()
            n_days = len(df_period)
            annual_scaling_factor = 365 / n_days

            df_period['cumReturn'] = (1 + df_period['dailyYield']).cumprod() - 1
            period_yield = df_period['cumReturn'].iat[-1]

            results[period] = {}
            results[period]['yield'] = period_yield
            results[period]['apr'] = period_yield * annual_scaling_factor
            results[period]['apy'] = (1 + period_yield / n_days) ** 365 - 1  # compounded daily
            results[period]['estimatedAnnualDistribution'] = (df_period.distributed.sum() / self.decimal_factor) * annual_scaling_factor
            results[period]['estimatedAnnualDistributionUSD'] = df_period.distributedUSD.sum() * annual_scaling_factor

        return results

    def distributions(self, get_data=True):
        if get_data:
            self._get_data()

        results = [
            {
                "timestamp": day['date'],
                "date": timestamp_to_date(int(day['date']), '%d/%m/%Y'),
                "distributed": float(day['distributed']) / self.decimal_factor
            }
            for day in self.data['visrTokenDayDatas']
        ]

        return results


class GammaInfo(GammaCalculations):
    def __init__(self, days=30):
        super().__init__(days=days)

    def output(self):
        self._get_data()
        gamma_pricing = GammaPrice()

        return {
            "info": self.basic_info(get_data=False),
            "yield": self.gamma_yield(get_data=False),
            "priceUSD": gamma_pricing.output()
        }


class GammaYield(GammaCalculations):
    def __init__(self, days=30):
        super().__init__(days=days)

    def output(self):
        return self.gamma_yield(get_data=True)


class GammaDistribution(GammaCalculations):
    def __init__(self, days=6, timezone=DEFAULT_TIMEZONE):
        super().__init__(days=days)

    def output(self):
        distributions = self.distributions(get_data=True)

        fee_distributions = []
        for i, distribution in enumerate(distributions):
            fee_distributions.append(
                {
                    'title': distribution['date'],
                    'desc': f"{int(distribution['distributed']):,}",
                    'id': i + 2
                }
            )

        return {
            'feeDistribution': fee_distributions
        }


class GammaPriceData:
    """Class for querying GAMMA related data"""

    def __init__(self):
        self.uniswap_client = UniswapV3Client()
        self.pool = "0x4006bed7bf103d70a1c6b7f1cef4ad059193dc25"  # GAMMA/WETH 0.3% pool
        self.data = {}

    def _get_data(self):
        query = """
        query gammaPrice($id: String!){
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
        variables = {"id": self.pool}
        self. data = self.uniswap_client.query(query, variables)['data']


class GammaPrice(GammaPriceData):
    def output(self):
        self._get_data()
        sqrt_priceX96 = float(self.data['pool']['sqrtPrice'])
        decimal0 = int(self.data['pool']['token0']['decimals'])
        decimal1 = int(self.data['pool']['token1']['decimals'])
        eth_in_usdc = float(self.data['bundle']['ethPriceUSD'])

        gamma_in_eth = sqrtPriceX96_to_priceDecimal(
            sqrt_priceX96,
            decimal0,
            decimal1
        )

        return {
            "gamma_in_usdc": gamma_in_eth * eth_in_usdc,
            "gamma_in_eth": gamma_in_eth
        }


class ProtocolFeesData:
    def __init__(self):
        self.visor_client = GammaClient()

    def _get_data(self, time_delta):
        query = """
        query  protocolFees($timestamp_start: Int!) {
            uniswapV3Rebalances(
                where: {
                    timestamp_gt: $timestamp_start
                }
            ) {
                timestamp
                protocolFeesUSD
            }
            visrToken(
                id: "0xf938424f7210f31df2aee3011291b658f872e91e"
            ){
                totalStaked
            }
        }
        """
        variables = {"timestamp_start": timestamp_ago(time_delta)}
        self.data = self.visor_client.query(query, variables)['data']


class ProtocolFeesCalculations(ProtocolFeesData):
    def __init__(self, days=30):
        super().__init__()
        self.days = days

    def collected_fees(self, get_data=True):
        if get_data:
            self._get_data(timedelta(days=self.days))

        rebalances = self.data['uniswapV3Rebalances']

        if not rebalances:
            return 0

        df_rebalances = DataFrame(rebalances, dtype=np.float64)

        gamma_price = GammaPrice()
        gamma_in_usd = gamma_price.output()['visr_in_usdc']

        gamma_staked_usd = gamma_in_usd * int(self.data['visrToken']['totalStaked']) / 10**18

        results = {}
        for period, days in DAYS_IN_PERIOD.items():
            df_period = df_rebalances[df_rebalances.timestamp > timestamp_ago(timedelta(days=days))].copy()

            total_fees_in_period = df_period.protocolFeesUSD.sum()
            fees_per_day = total_fees_in_period / days

            daily_yield = fees_per_day / gamma_staked_usd
            fees_apr = daily_yield * 365
            fees_apy = (1 + daily_yield) ** 365 - 1

            results[period] = {}
            results[period]['collected_usd'] = fees_per_day
            results[period]['collected_gamma'] = fees_per_day / gamma_staked_usd
            results[period]['yield'] = daily_yield
            results[period]['apr'] = fees_apr
            results[period]['apy'] = fees_apy

        return results
