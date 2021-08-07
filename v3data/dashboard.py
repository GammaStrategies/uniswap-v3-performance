from datetime import timedelta

from v3data import VisorClient
from v3data.visr import VisrCalculations, VisrPrice
from v3data.visor import VisorVault
from v3data.toplevel import TopLevelData
from v3data.utils import timestamp_ago
from v3data.config import PRIVATE_BETA_TVL
from v3data.constants import DAYS_IN_PERIOD


class Dashboard:
    def __init__(self, period):
        self.visor_client = VisorClient()
        self.period = period
        self.days = 30
        self.visr_data = {}
        self.top_level_data = {}
        self.top_level_returns_data = {}

    def _get_data(self, timezone):
        query = """
        query($days: Int!, $timezone: String!, $timestampStart: Int!){
            visrToken(
                id: "0xf938424f7210f31df2aee3011291b658f872e91e"
            ){
                totalSupply
                totalDistributed
                totalDistributedUSD
                totalStaked
            }
            visrTokenDayDatas(
                first: $days
                where: {
                    distributed_gt: 0
                    totalStaked_gt: 0
                    timezone: $timezone
                }
                orderBy: date
                orderDirection: desc
            ){
                date
                distributed
                distributedUSD
                totalStaked
            }
            uniswapV3Pools(
                first: 1000
            ){
                id
            }
            uniswapV3Hypervisors(
                first: 1000
            ){
                id
                grossFeesClaimedUSD
                tvlUSD
                rebalances(
                    first: 1000
                    where: { timestamp_gte: $timestampStart }
                    orderBy: timestamp
                    orderDirection: desc
                ) {
                    id
                    timestamp
                    grossFeesUSD
                    protocolFeesUSD
                    netFeesUSD
                    totalAmountUSD
                }
            }
        }
        """
        variables = {
            "days": self.days,
            "timezone": timezone,
            "timestampStart": timestamp_ago(timedelta(self.days))
        }

        data = self.visor_client.query(query, variables)['data']
        self.visr_data = {
            'visrToken': data['visrToken'],
            'visrTokenDayDatas': data['visrTokenDayDatas']
        }
        self.top_level_data = {
            "uniswapV3Hypervisors": data['uniswapV3Hypervisors'],
            "uniswapV3Pools": data['uniswapV3Pools']
        }
        self.top_level_returns_data = data['uniswapV3Hypervisors']

    def info(self, timezone):
        self._get_data(timezone)
        visr_calcs = VisrCalculations(days=30)
        visr_calcs.data = self.visr_data
        visr_info = visr_calcs.basic_info(get_data=False)
        visr_yield = visr_calcs.visr_yield(get_data=False)
        distributions = visr_calcs.distributions(get_data=False)
        last_day_distribution = float(distributions[0]['distributed'])
        visr_price = VisrPrice()
        visr_price_usd = visr_price.output()

        top_level = TopLevelData()
        top_level.all_stats_data = self.top_level_data
        top_level.all_returns_data = self.top_level_returns_data
        top_level_data = top_level._all_stats()
        top_level_returns = top_level._calculate_returns()

        daily_yield = visr_yield[self.period]['yield'] / DAYS_IN_PERIOD[self.period]

        dashboard_stats = {
            "stakedUsdAmount": visr_info['totalStaked'] * visr_price_usd,
            "stakedAmount": visr_info['totalStaked'],
            "feeStatsFeeAccural": last_day_distribution * visr_price_usd,
            "feeStatsAmountVisr": last_day_distribution,
            "feeStatsStakingApr": visr_yield[self.period]['apr'],
            "feeStatsStakingApy": visr_yield[self.period]['apy'],
            "feeStatsStakingDailyYield": daily_yield,
            "feeCumulativeFeeUsd": visr_info['totalDistributedUSD'],
            "feeCumulativeFeeUsdAnnual": visr_yield[self.period]['estimatedAnnualDistributionUSD'],
            "feeCumulativeFeeDistributed": visr_info['totalDistributed'],
            "feeCumulativeFeeDistributedAnnual": visr_yield[self.period]['estimatedAnnualDistribution'],
            "uniswapPairTotalValueLocked": top_level_data['tvl'] + PRIVATE_BETA_TVL,
            "uniswapPairAmountPairs": top_level_data['pool_count'],
            "uniswapFeesGenerated": top_level_data['fees_claimed'],
            "uniswapFeesBasedApr": f"{top_level_returns[self.period]['feeApr']:.0%}",
            "visrPrice": visr_price_usd,  # End point for price
            "id": 2
        }

        return dashboard_stats
