from datetime import timedelta

from v3data import GammaClient
from v3data.gamma import GammaCalculations, GammaPrice, ProtocolFeesCalculations
from v3data.toplevel import TopLevelData
from v3data.rewardshypervisor import RewardsHypervisorInfo
from v3data.utils import timestamp_ago
from v3data.constants import DAYS_IN_PERIOD, GAMMA_ADDRESS, XGAMMA_ADDRESS
from v3data.config import legacy_stats

class Dashboard:
    def __init__(self, period):
        self.gamma_client = GammaClient()
        self.period = period
        self.days = 30
        self.visr_data = {}
        self.eth_data = {}
        self.top_level_data = {}
        self.top_level_returns_data = {}
        self.rewards_hypervisor_data = {}

    def _get_data(self, timezone):
        query = """
        query(
            $gammaAddress: String!,
            $xgammaAddress: String!,
            $days: Int!,
            $timezone: String!,
            $timestampStart: Int!,
            $rebalancesStart: Int!
        ){
            token(id: $gammaAddress){
                totalSupply
            }
            protocolDistribution(id: $gammaAddress){
                distributed
                distributedUSD
            }
            distributionDayDatas(
                orderBy: date
                orderDirection: desc
                first: $days
                where: {
                    token: $gammaAddress
                    distributed_gt: 0
                    timezone: $timezone
                }
            ){
                date
                distributed
                distributedUSD
            }
            rewardHypervisorDayDatas(
                orderBy: date
                orderDirection: desc
                first: $days
                where: {
                    totalGamma_gt: 0
                    timezone: $timezone
                }
            ){
                date
                totalGamma
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
                id: $xgammaAddress
            ) {
                totalGamma
                totalSupply
            }
        }
        """
        variables = {
            "gammaAddress": GAMMA_ADDRESS,
            "xgammaAddress": XGAMMA_ADDRESS,
            "days": self.days,
            "timezone": timezone,
            "timestampStart": timestamp_ago(timedelta(self.days)),
            "rebalancesStart": timestamp_ago(timedelta(7))
        }

        data = self.gamma_client.query(query, variables)['data']

        self.gamma_data = {
            'token': data['token'],
            'protocolDistribution': data['protocolDistribution'],
            'distributionDayDatas': data['distributionDayDatas'],
            'rewardHypervisor': data['rewardHypervisor']
        }
        self.top_level_data = {
            "uniswapV3Hypervisors": data['uniswapV3Hypervisors'],
            "uniswapV3Pools": data['uniswapV3Pools']
        }
        self.top_level_returns_data = data['uniswapV3Hypervisors']

        self.protocol_fees_data = {
            'uniswapV3Rebalances': data['uniswapV3Rebalances'],
            'rewardHypervisor': data['rewardHypervisor'],
        }
        self.rewards_hypervisor_data = {
            'rewardHypervisor': data['rewardHypervisor']
        }

    def info(self, timezone):
        self._get_data(timezone)
        gamma_calcs = GammaCalculations(days=30)
        gamma_calcs.data = self.gamma_data
        gamma_info = gamma_calcs.basic_info(get_data=False)
        gamma_yield = gamma_calcs.gamma_yield(get_data=False)
        distributions = gamma_calcs.distributions(get_data=False)
        # last_day_distribution = float(distributions[0]['distributed'])
        visr_price = GammaPrice()
        visr_price_usd = visr_price.output()["gamma_in_usdc"]

        protocol_fees_calcs = ProtocolFeesCalculations(days=7)
        protocol_fees_calcs.data = self.protocol_fees_data
        collected_fees = protocol_fees_calcs.collected_fees(get_data=False)

        visr_in_eth = visr_price.output()["gamma_in_eth"]

        top_level = TopLevelData()
        top_level.all_stats_data = self.top_level_data
        top_level.all_returns_data = self.top_level_returns_data
        top_level_data = top_level._all_stats()
        top_level_returns = top_level._calculate_returns()

        daily_yield = gamma_yield[self.period]['yield'] / DAYS_IN_PERIOD[self.period]

        rewards = RewardsHypervisorInfo()
        rewards.data = self.rewards_hypervisor_data
        rewards_info = rewards.output(get_data=False)

        dashboard_stats = {
            "stakedUsdAmount": rewards_info['gamma_staked'] * visr_price_usd,
            "stakedAmount": rewards_info['gamma_staked'],
            "feeStatsFeeAccural": collected_fees['daily']['collected_usd'],
            "feeStatsAmountVisr": collected_fees['daily']['collected_gamma'],
            "feeStatsStakingApr":  0, # visr_yield[self.period]['apr'],
            "feeStatsStakingApy":  0, # visr_yield[self.period]['apy'],
            "feeStatsStakingDailyYield": 0, # daily_yield,
            "feeCumulativeFeeUsd": legacy_stats['visr_distributed_usd'] + gamma_info['totalDistributedUSD'],
            "feeCumulativeFeeUsdAnnual": legacy_stats['estimated_visr_annual_distribution_usd'],  # gamma_yield[self.period]['estimatedAnnualDistributionUSD'],
            "feeCumulativeFeeDistributed": legacy_stats['visr_distributed'] + gamma_info['totalDistributed'],
            "feeCumulativeFeeDistributedAnnual": legacy_stats['estimated_visr_annual_distribution'],  # gamma_yield[self.period]['estimatedAnnualDistribution'],
            "uniswapPairTotalValueLocked": top_level_data['tvl'],
            "uniswapPairAmountPairs": top_level_data['pool_count'],
            "uniswapFeesGenerated": top_level_data['fees_claimed'],
            "uniswapFeesBasedApr": f"{top_level_returns[self.period]['feeApr']:.0%}",
            "visrPrice": visr_price_usd,  # End point for price
            "visrInEth": visr_in_eth,
            "gammaPrice": visr_price_usd,  # End point for price
            "gammaInEth": visr_in_eth,
            "visrPerVvisr": rewards_info['gamma_per_xgamma'],
            "gammaPerXgamma": rewards_info['gamma_per_xgamma'],
            "id": 2
        }

        return dashboard_stats
