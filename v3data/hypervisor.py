import logging
import numpy as np
from datetime import timedelta
from pandas import DataFrame

from v3data import GammaClient, UniswapV3Client
from v3data.utils import timestamp_ago, timestamp_to_date
from v3data.constants import DAYS_IN_PERIOD, SECONDS_IN_DAYS
from v3data.config import EXCLUDED_HYPERVISORS, FALLBACK_DAYS

DAY_SECONDS = 24 * 60 * 60
YEAR_SECONDS = 365 * DAY_SECONDS

logger = logging.getLogger(__name__)


class HypervisorData:
    def __init__(self, chain: str = "mainnet"):
        self.gamma_client = GammaClient(chain)
        self.uniswap_client = UniswapV3Client(chain)
        self.basics_data = {}
        self.pools_data = {}

    async def get_rebalance_data(self, hypervisor_address, time_delta, limit=1000):
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
            "limit": limit,
        }
        response = await self.gamma_client.query(query, variables)
        return response["data"]["uniswapV3Rebalances"]

    async def _get_all_rebalance_data(self, time_delta):
        query = """
        query allRebalances($timestamp_start: Int!){
            uniswapV3Hypervisors(
                first: 1000
            ){
                id
                rebalances(
                    first: 1000
                    where: { timestamp_gte: $timestamp_start }
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
        variables = {"timestamp_start": timestamp_ago(time_delta)}
        response = await self.gamma_client.query(query, variables)
        self.all_rebalance_data = response["data"]["uniswapV3Hypervisors"]

    async def _get_hypervisor_data(self, hypervisor_address):
        query = """
        query hypervisor($id: String!){
            uniswapV3Hypervisor(
                id: $id
            ) {
                id
                created
                baseLower
                baseUpper
                totalSupply
                maxTotalSupply
                deposit0Max
                deposit1Max
                grossFeesClaimed0
                grossFeesClaimed1
                grossFeesClaimedUSD
                feesReinvested0
                feesReinvested1
                feesReinvestedUSD
                tvl0
                tvl1
                tvlUSD
                pool{
                    id
                    fee
                    token0{
                        symbol
                        decimals
                    }
                    token1{
                        symbol
                        decimals
                    }
                }
            }
        }
        """
        variables = {"id": hypervisor_address.lower()}
        response = await self.gamma_client.query(query, variables)
        return response["data"]["uniswapV3Hypervisor"]

    async def _get_all_data(self):
        query_basics = """
        {
            uniswapV3Hypervisors(
                first:1000
            ){
                id
                created
                baseLower
                baseUpper
                totalSupply
                maxTotalSupply
                deposit0Max
                deposit1Max
                grossFeesClaimed0
                grossFeesClaimed1
                grossFeesClaimedUSD
                feesReinvested0
                feesReinvested1
                feesReinvestedUSD
                tvl0
                tvl1
                tvlUSD
                pool{
                    id
                    fee
                    token0{
                        symbol
                        decimals
                    }
                    token1{
                        symbol
                        decimals
                    }
                }
            }
        }
        """

        basics_response = await self.gamma_client.query(query_basics)
        basics = basics_response["data"]["uniswapV3Hypervisors"]
        pool_addresses = [hypervisor["pool"]["id"] for hypervisor in basics]

        query_pool = """
        query slot0($pools: [String!]!){
            pools(
                where: {
                    id_in: $pools
                }
            ) {
                id
                sqrtPrice
                tick
                observationIndex
                feesUSD
                totalValueLockedUSD
            }
        }
        """
        variables = {"pools": pool_addresses}
        pools_response = await self.uniswap_client.query(query_pool, variables)
        pools_data = pools_response["data"]["pools"]
        pools = {pool.pop("id"): pool for pool in pools_data}

        self.basics_data = basics
        self.pools_data = pools


class HypervisorInfo(HypervisorData):
    def empty_returns(self):
        return {
            period: {
                "cumFeeReturn": 0.0,
                "feeApr": 0,
                "feeApy": 0,
                "totalPeriodSeconds": 0,
            }
            for period in DAYS_IN_PERIOD
        }

    def _calculate_returns(self, data):
        # Calculations require more than 1 rebalance
        if (not data) or (len(data) < 2):
            return self.empty_returns()

        df_rebalances = DataFrame(data)
        df_rebalances = df_rebalances[
            [
                "timestamp",
                "grossFeesUSD",
                "protocolFeesUSD",
                "netFeesUSD",
                "totalAmountUSD",
            ]
        ].astype(np.float64)
        df_rebalances = df_rebalances[df_rebalances.totalAmountUSD > 0]

        if df_rebalances.empty:
            return self.empty_returns()

        df_rebalances.sort_values("timestamp", inplace=True)
        latest_rebalance_ts = df_rebalances.loc[df_rebalances.index[-1], "timestamp"]

        # Calculate fee return rate for each rebalance event
        df_rebalances[
            "feeRate"
        ] = df_rebalances.grossFeesUSD / df_rebalances.totalAmountUSD.shift(1)
        df_rebalances["totalRate"] = (
            df_rebalances.totalAmountUSD / df_rebalances.totalAmountUSD.shift(1) - 1
        )

        # Time since last rebalance
        df_rebalances["periodSeconds"] = df_rebalances.timestamp.diff()

        # Calculate returns for using last 1, 7, and 30 days data
        results = {}
        for period, days in DAYS_IN_PERIOD.items():
            timestamp_start = timestamp_ago(timedelta(days=days))
            #  If no items for timestamp larger than timestamp_start
            n_valid_rows = len(df_rebalances[df_rebalances.timestamp > timestamp_start])
            if n_valid_rows < 2:
                timestamp_start = latest_rebalance_ts - (
                    FALLBACK_DAYS * SECONDS_IN_DAYS
                )
            df_period = df_rebalances.loc[
                df_rebalances.timestamp > timestamp_start
            ].copy()

            if df_period.empty:
                # if no rebalances in the last 24 hours, calculate using the 24 hours prior to the last rebalance
                timestamp_start = df_rebalances.timestamp.max() - DAY_SECONDS
                df_period = df_rebalances.loc[
                    df_rebalances.timestamp > timestamp_start
                ].copy()

            # Time since first reblance
            df_period["totalPeriodSeconds"] = df_period.periodSeconds.cumsum()

            # Compound fee return rate for each rebalance
            df_period["cumFeeReturn"] = (1 + df_period.feeRate).cumprod() - 1
            df_period["cumTotalReturn"] = (1 + df_period.totalRate).cumprod() - 1

            # Last row is the cumulative results
            returns = df_period[["totalPeriodSeconds", "cumFeeReturn"]].tail(
                1
            )  # , 'cumTotalReturn'

            # Extrapolate linearly to annual rate
            returns["feeApr"] = returns.cumFeeReturn * (
                YEAR_SECONDS / returns.totalPeriodSeconds
            )

            # Extrapolate by compounding
            returns["feeApy"] = (
                1 + returns.cumFeeReturn * (DAY_SECONDS / returns.totalPeriodSeconds)
            ) ** 365 - 1

            results[period] = returns.to_dict("records")[0]

        if results["monthly"]["feeApy"] == np.inf:
            results["monthly"] = results["weekly"]

        return results

    async def basic_stats(self, hypervisor_address):
        data = await self._get_hypervisor_data(hypervisor_address)
        return data

    async def calculate_returns(self, hypervisor_address):
        data = await self.get_rebalance_data(hypervisor_address, timedelta(days=360))
        return self._calculate_returns(data)

    async def all_returns(self, get_data=True):

        if get_data:
            await self._get_all_rebalance_data(timedelta(days=360))

        results = {}
        for hypervisor in self.all_rebalance_data:
            if hypervisor["id"] not in EXCLUDED_HYPERVISORS:
                results[hypervisor["id"]] = self._calculate_returns(
                    hypervisor["rebalances"]
                )

        return results

    async def all_data(self, get_data=True):

        if get_data:
            await self._get_all_data()

        basics = self.basics_data
        pools = self.pools_data

        returns = await self.all_returns(get_data=get_data)

        results = {}
        for hypervisor in basics:
            try:
                hypervisor_id = hypervisor["id"]
                hypervisor_name = f'{hypervisor["pool"]["token0"]["symbol"]}-{hypervisor["pool"]["token1"]["symbol"]}-{hypervisor["pool"]["fee"]}'
                pool_id = hypervisor["pool"]["id"]
                decimals0 = hypervisor["pool"]["token0"]["decimals"]
                decimals1 = hypervisor["pool"]["token1"]["decimals"]
                tick = int(pools[pool_id]["tick"]) if pools[pool_id]["tick"] else 0
                baseLower = int(hypervisor["baseLower"])
                baseUpper = int(hypervisor["baseUpper"])
                totalSupply = int(hypervisor["totalSupply"])
                maxTotalSupply = int(hypervisor["maxTotalSupply"])
                capacityUsed = (
                    totalSupply / maxTotalSupply if maxTotalSupply > 0 else "No cap"
                )

                results[hypervisor_id] = {
                    "createDate": timestamp_to_date(
                        int(hypervisor["created"]), "%d %b, %Y"
                    ),
                    "poolAddress": pool_id,
                    "name": hypervisor_name,
                    "decimals0": decimals0,
                    "decimals1": decimals1,
                    "depositCap0": int(hypervisor["deposit0Max"]) / 10**decimals0,
                    "depositCap1": int(hypervisor["deposit1Max"]) / 10**decimals1,
                    "grossFeesClaimed0": int(hypervisor["grossFeesClaimed0"])
                    / 10**decimals0,
                    "grossFeesClaimed1": int(hypervisor["grossFeesClaimed1"])
                    / 10**decimals1,
                    "grossFeesClaimedUSD": hypervisor["grossFeesClaimedUSD"],
                    "feesReinvested0": int(hypervisor["feesReinvested0"])
                    / 10**decimals0,
                    "feesReinvested1": int(hypervisor["feesReinvested1"])
                    / 10**decimals1,
                    "feesReinvestedUSD": hypervisor["feesReinvestedUSD"],
                    "tvl0": int(hypervisor["tvl0"]) / 10**decimals0,
                    "tvl1": int(hypervisor["tvl1"]) / 10**decimals1,
                    "tvlUSD": hypervisor["tvlUSD"],
                    "totalSupply": totalSupply,
                    "maxTotalSupply": maxTotalSupply,
                    "capacityUsed": capacityUsed,
                    "sqrtPrice": pools[pool_id]["sqrtPrice"],
                    "tick": tick,
                    "baseLower": baseLower,
                    "baseUpper": baseUpper,
                    "inRange": bool(baseLower <= tick <= baseUpper),
                    "observationIndex": pools[pool_id]["observationIndex"],
                    "poolTvlUSD": pools[pool_id]["totalValueLockedUSD"],
                    "poolFeesUSD": pools[pool_id]["feesUSD"],
                    "returns": returns.get(hypervisor_id),
                }
            except Exception as e:
                logger.warning(f"Failed on hypervisor {hypervisor['id']}")
                logger.exception(e)
                pass

        return results
