from datetime import timedelta

from v3data import VisorClient
from v3data.visr import VisrCalculations, VisrPrice, ProtocolFeesCalculations
from v3data.eth import EthCalculations
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
        self.eth_data = {}
        self.top_level_data = {}
        self.top_level_returns_data = {}

    def _get_data(self, timezone):
        query = """
        query($days: Int!, $timezone: String!, $timestampStart: Int!, $rebalancesStart: Int!){
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
            uniswapV3Rebalances(
                where: {
                    timestamp_gt: $rebalancesStart
                }
            ) {
                timestamp
                protocolFeesUSD
            }
            rewardHypervisor(
                id:"0xc9f27a50f82571c1c8423a42970613b8dbda14ef"
            ) {
                totalVisr
            }
        }
        """
        variables = {
            "days": self.days,
            "timezone": timezone,
            "timestampStart": timestamp_ago(timedelta(self.days)),
            "rebalancesStart": timestamp_ago(timedelta(7))
        }

        data = self.visor_client.query(query, variables)['data']
        self.visr_data = {
            'visrToken': data['visrToken'],
            'visrTokenDayDatas': data['visrTokenDayDatas'],
            'rewardHypervisor': data['rewardHypervisor']
        }
        self.eth_data = {
            'ethToken': data['ethToken'],
            'ethDayDatas': data['ethDayDatas']
        }
        self.top_level_data = {
            "uniswapV3Hypervisors": data['uniswapV3Hypervisors'],
            "uniswapV3Pools": data['uniswapV3Pools']
        }
        self.top_level_returns_data = data['uniswapV3Hypervisors']

        self.protocol_fees_data = {
            'uniswapV3Rebalances': data['uniswapV3Rebalances'],
            'visrToken': data['visrToken'],
        }

    def info(self, timezone):
        self._get_data(timezone)
        visr_calcs = VisrCalculations(days=30)
        visr_calcs.data = self.visr_data
        visr_info = visr_calcs.basic_info(get_data=False)
        visr_yield = visr_calcs.visr_yield(get_data=False)
        distributions = visr_calcs.distributions(get_data=False)
        last_day_distribution = float(distributions[0]['distributed'])
        visr_price = VisrPrice()
        visr_price_usd = visr_price.output()["visr_in_usdc"]

        protocol_fees_calcs = ProtocolFeesCalculations(days=7)
        protocol_fees_calcs.data = self.protocol_fees_data
        collected_fees = protocol_fees_calcs.collected_fees(get_data=False)

        eth_calcs = EthCalculations(days=30)
        eth_calcs.data = self.eth_data
        eth_distributions = eth_calcs.distributions(get_data=False)
        eth_last_distribution = float(eth_distributions[0]['distributed'])
        eth_average_daily_distribution = eth_last_distribution / 7
        visr_in_eth = visr_price.output()["visr_in_eth"]

        top_level = TopLevelData()
        top_level.all_stats_data = self.top_level_data
        top_level.all_returns_data = self.top_level_returns_data
        top_level_data = top_level._all_stats()
        top_level_returns = top_level._calculate_returns()

        daily_yield = visr_yield[self.period]['yield'] / DAYS_IN_PERIOD[self.period]

        dashboard_stats = {
            "visr_in_eth": visr_in_eth,
            "visr_price_usd": visr_price_usd,
            "stakedUsdAmount": visr_info['totalStaked'] * visr_price_usd,
            "stakedAmount": visr_info['totalStaked'],
            "feeStatsFeeAccural": collected_fees['daily']['collected_usd'], # (eth_average_daily_distribution / visr_in_eth) * visr_price_usd, # last_day_distribution * visr_price_usd,
            "feeStatsAmountVisr": collected_fees['daily']['collected_visr'], # (eth_average_daily_distribution / visr_in_eth), # last_day_distribution,
            "feeStatsStakingApr":  visr_yield[self.period]['apr'],  # collected_fees[self.period]['apr'],
            "feeStatsStakingApy":  visr_yield[self.period]['apy'],  # collected_fees[self.period]['apy'],
            "feeStatsStakingDailyYield": daily_yield,  # collected_fees[self.period]['yield'],
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
