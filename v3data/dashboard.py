import asyncio
from datetime import timedelta

from v3data import GammaClient
from v3data.gamma import GammaCalculations, ProtocolFeesCalculations
from v3data.pricing import token_price
from v3data.toplevel import TopLevelData
from v3data.rewardshypervisor import RewardsHypervisorInfo
from v3data.utils import timestamp_ago
from v3data.constants import DAYS_IN_PERIOD, GAMMA_ADDRESS, XGAMMA_ADDRESS
from v3data.config import legacy_stats, GROSS_FEES_MAX
from v3data.enums import Chain, Protocol


class Dashboard:
    def __init__(self, period: str):
        self.chain = Chain.MAINNET
        self.gamma_client = GammaClient(Protocol.UNISWAP, self.chain)
        self.period = period
        self.days = 30
        self.visr_data = {}
        self.eth_data = {}
        self.top_level_data = {}
        self.top_level_returns_data = {}
        self.rewards_hypervisor_data = {}

    async def _get_data(self, timezone):
        query = """
        query(
            $gammaAddress: String!,
            $xgammaAddress: String!,
            $days: Int!,
            $timezone: String!,
            $timestampStart: Int!,
            $rebalancesStart: Int!,
            $grossFeesMax: Int!
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
                    where: {
                        timestamp_gte: $timestampStart
                        grossFeesUSD_lt: $grossFeesMax
                    }
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
                badRebalances: rebalances(
                    where: {grossFeesUSD_gte: $grossFeesMax}
                ) {
                    grossFeesUSD
                    protocolFeesUSD
                    netFeesUSD
                }
            }
            uniswapV3Rebalances(
                where: {
                    timestamp_gt: $rebalancesStart
                    grossFeesUSD_lt: $grossFeesMax
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
            "rebalancesStart": timestamp_ago(timedelta(7)),
            "grossFeesMax": GROSS_FEES_MAX
        }

        response = await self.gamma_client.query(query, variables)
        data = response["data"]

        self.gamma_data = {
            "token": data["token"],
            "protocolDistribution": data["protocolDistribution"],
            "distributionDayDatas": data["distributionDayDatas"],
            "rewardHypervisor": data["rewardHypervisor"],
            "rewardHypervisorDayDatas": data["rewardHypervisorDayDatas"],
        }
        self.top_level_data = {
            "uniswapV3Hypervisors": data["uniswapV3Hypervisors"],
            "uniswapV3Pools": data["uniswapV3Pools"],
        }
        self.top_level_returns_data = data["uniswapV3Hypervisors"]

        self.protocol_fees_data = {
            "uniswapV3Rebalances": data["uniswapV3Rebalances"],
            "rewardHypervisor": data["rewardHypervisor"],
        }
        self.rewards_hypervisor_data = {"rewardHypervisor": data["rewardHypervisor"]}

    async def info(self, timezone):

        _, gamma_prices = await asyncio.gather(
            self._get_data(timezone), token_price("GAMMA")
        )

        gamma_price_usd = gamma_prices["token_in_usdc"]
        gamma_in_eth = gamma_prices["token_in_native"]

        gamma_calcs = GammaCalculations(self.chain, days=30)
        gamma_calcs.data = self.gamma_data
        gamma_info = await gamma_calcs.basic_info(get_data=False)
        gamma_yield = await gamma_calcs.gamma_yield(get_data=False)

        protocol_fees_calcs = ProtocolFeesCalculations(days=7)
        protocol_fees_calcs.data = self.protocol_fees_data
        collected_fees = await protocol_fees_calcs.collected_fees(get_data=False)

        top_level = TopLevelData(Protocol.UNISWAP, self.chain)
        top_level.all_stats_data = self.top_level_data
        top_level.all_returns_data = self.top_level_returns_data
        top_level_data = top_level._all_stats()
        top_level_returns = await top_level._calculate_returns()

        daily_yield = gamma_yield[self.period]["yield"] / DAYS_IN_PERIOD[self.period]

        rewards = RewardsHypervisorInfo()
        rewards.data = self.rewards_hypervisor_data
        rewards_info = await rewards.output(get_data=False)

        gamma_staked_usd = rewards_info["gamma_staked"] * gamma_price_usd

        # Use fees for gamma yield
        fees_per_day = collected_fees['weekly']["collected_usd"]
        gamma_fees_apr = 365 * fees_per_day / gamma_staked_usd
        gamma_fees_apy = (1 + fees_per_day / gamma_staked_usd) ** 365 - 1

        dashboard_stats = {
            "stakedUsdAmount": gamma_staked_usd,
            "stakedAmount": rewards_info["gamma_staked"],
            "feeStatsFeeAccural": collected_fees["daily"]["collected_usd"],
            "feeStatsAmountGamma": collected_fees["daily"]["collected_gamma"],
            "feeStatsStakingApr": gamma_fees_apr,  # gamma_yield[self.period]["apr"],
            "feeStatsStakingApy": gamma_fees_apy,  # gamma_yield[self.period]["apy"],
            "stakingDistributionApr": gamma_yield[self.period]["apr"],
            "stakingDistributionApy": gamma_yield[self.period]["apy"],
            "feeStatsStakingDailyYield": daily_yield,
            "feeCumulativeFeeUsd": legacy_stats["visr_distributed_usd"]
            + gamma_info["totalDistributedUSD"],
            "feeCumulativeFeeUsdAnnual": legacy_stats[
                "estimated_visr_annual_distribution_usd"
            ],  # gamma_yield[self.period]['estimatedAnnualDistributionUSD'],
            "feeCumulativeFeeDistributed": legacy_stats["visr_distributed"]
            + gamma_info["totalDistributed"],
            "feeCumulativeFeeDistributedAnnual": legacy_stats[
                "estimated_visr_annual_distribution"
            ],  # gamma_yield[self.period]['estimatedAnnualDistribution'],
            "uniswapPairTotalValueLocked": top_level_data["tvl"],
            "uniswapPairAmountPairs": top_level_data["pool_count"],
            "uniswapFeesGenerated": top_level_data["fees_claimed"],
            "uniswapFeesBasedApr": f"{top_level_returns[self.period]['feeApr']:.0%}",
            "gammaPrice": gamma_price_usd,
            "gammaInEth": gamma_in_eth,
            "gammaPerXgamma": rewards_info["gamma_per_xgamma"],
            "id": 2,
        }

        # For compatability, to be deprecated
        dashboard_stats.update(
            {
                "feeStatsAmountVisr": dashboard_stats["feeStatsAmountGamma"],
                "visrPrice": dashboard_stats["gammaPrice"],
                "visrInEth": dashboard_stats["gammaInEth"],
                "visrPerVvisr": dashboard_stats["gammaPerXgamma"],
            }
        )

        return dashboard_stats
