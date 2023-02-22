import asyncio
import numpy as np
from datetime import timedelta
from pandas import DataFrame

from v3data import GammaClient
from v3data.hypervisor import HypervisorInfo
from v3data.pricing import token_price
from v3data.utils import timestamp_ago, filter_addresses_byChain
from v3data.config import EXCLUDED_HYPERVISORS


class TopLevelData:
    """Top level stats"""

    def __init__(self, protocol: str, chain: str = "mainnet"):
        self.protocol = protocol
        self.gamma_client = GammaClient(protocol, chain)
        self.all_stats_data = {}
        self.all_returns_data = {}

        self.excluded_hypervisors = filter_addresses_byChain(
            EXCLUDED_HYPERVISORS, chain
        )

    async def get_hypervisor_data(self):
        """Get hypervisor IDs"""
        query = """
        {
            uniswapV3Hypervisors(
                first: 1000
            ){
                id
                grossFeesClaimedUSD
                tvlUSD
            }
        }
        """
        response = await self.gamma_client.query(query)
        return response["data"]["uniswapV3Hypervisors"]

    async def get_pool_data(self):
        query = """
        {
            uniswapV3Pools(
                first: 1000
            ){
                id
            }
        }
        """
        response = await self.gamma_client.query(query)
        return response["data"]["uniswapV3Pools"]

    async def _get_all_returns_data(self, time_delta):
        query = """
        query allRebalances($timestampStart: Int!){
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
        variables = {"timestampStart": timestamp_ago(time_delta)}
        response = await self.gamma_client.query(query, variables)
        self.all_returns_data = response["data"]["uniswapV3Hypervisors"]

    async def _get_all_stats_data(self):
        query = """
        {
            uniswapV3Hypervisors(
                first: 1000
            ){
                id
                grossFeesClaimedUSD
                tvlUSD
            }
            uniswapV3Pools(
                first: 1000
            ){
                id
            }
        }
        """

        response = await self.gamma_client.query(query)
        self.all_stats_data = response["data"]

    async def get_recent_rebalance_data(self, hours=24):
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
        timestamp_start = timestamp_ago(timedelta(hours=hours))
        variables = {"timestamp_start": timestamp_start}
        response = await self.gamma_client.query(query, variables)
        return response["data"]["uniswapV3Rebalances"]

    def _all_stats(self):
        """
        Aggregate TVL and fees generated stats from all factories
        Should add entity to subgraph to track top level stats
        """
        data = self.all_stats_data
        for hypervisor in data["uniswapV3Hypervisors"]:
            if hypervisor["id"] == "0x8cd73cb1e1fa35628e36b8c543c5f825cd4e77f1":
                # Correcting incorrect USD value for TCR
                hypervisor["grossFeesClaimedUSD"] = str(
                    max(float(hypervisor["grossFeesClaimedUSD"]) - 770480494, 0)
                )
                break

        return {
            "pool_count": len(data["uniswapV3Pools"]),
            "tvl": sum(
                [
                    float(hypervisor["tvlUSD"])
                    for hypervisor in data["uniswapV3Hypervisors"]
                    if hypervisor["id"] not in self.excluded_hypervisors
                ]
            ),
            "fees_claimed": sum(
                [
                    float(hypervisor["grossFeesClaimedUSD"])
                    for hypervisor in data["uniswapV3Hypervisors"]
                    if hypervisor["id"] not in self.excluded_hypervisors
                ]
            ),
        }

    async def all_stats(self):
        await self._get_all_stats_data()
        return self._all_stats()

    async def recent_fees(self, hours=24):
        data, gamma_prices = await asyncio.gather(
            self.get_recent_rebalance_data(hours), token_price("GAMMA")
        )
        gamma_price_usd = gamma_prices["token_in_usdc"]
        df_fees = DataFrame(data, dtype=np.float64)

        df_fees["grossFeesGAMMA"] = df_fees.grossFeesUSD / gamma_price_usd
        df_fees["protocolFeesGAMMA"] = df_fees.protocolFeesUSD / gamma_price_usd
        df_fees["netFeesGAMMA"] = df_fees.netFeesUSD / gamma_price_usd

        return df_fees.sum().to_dict()

    async def _calculate_returns(self):
        hypervisors = self.all_returns_data

        tvl = sum(
            [
                float(hypervisor["tvlUSD"])
                for hypervisor in hypervisors
                if hypervisor["id"] not in self.excluded_hypervisors
            ]
        )

        hypervisor_info = HypervisorInfo(self.protocol)
        hypervisor_info.all_rebalance_data = hypervisors
        all_returns = await hypervisor_info.all_returns()

        returns = {
            "daily": {"feeApr": 0, "feeApy": 0},
            "weekly": {"feeApr": 0, "feeApy": 0},
            "monthly": {"feeApr": 0, "feeApy": 0},
            "allTime": {"feeApr": 0, "feeApy": 0},
        }
        for hypervisor in hypervisors:
            if hypervisor["id"] in self.excluded_hypervisors:
                continue
            if tvl > 0:
                tvl_share = float(hypervisor["tvlUSD"]) / tvl
            else:
                tvl_share = 0
            hypervisor_returns = all_returns.get(hypervisor["id"])
            if hypervisor_returns:
                for period, values in hypervisor_returns.items():
                    returns[period]["feeApr"] += values["feeApr"] * tvl_share
                    returns[period]["feeApy"] += values["feeApy"] * tvl_share

        return returns

    async def calculate_returns(self):
        await self._get_all_returns_data(timedelta(days=30))
        return await self._calculate_returns()
