import asyncio
from datetime import timedelta

import numpy as np
from pandas import DataFrame, to_datetime

from v3data import GammaClient
from v3data.config import DEFAULT_TIMEZONE, GROSS_FEES_MAX
from v3data.constants import DAYS_IN_PERIOD, GAMMA_ADDRESS, XGAMMA_ADDRESS
from v3data.enums import Chain, Protocol
from v3data.pricing import token_price
from v3data.utils import timestamp_ago


class GammaData:
    def __init__(self, chain: Chain, days, timezone=DEFAULT_TIMEZONE):
        self.gamma_client = GammaClient(Protocol.UNISWAP, chain)
        self.days = days
        self.timezone = timezone
        self.address = GAMMA_ADDRESS
        self.decimal_factor = 10**18
        self.data = {}

    async def _get_data(self):
        query = """
        query(
            $xgammaAddress: String!,
            $gammaAddress: String!,
            $days: Int!,
            $timezone: String!
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
            rewardHypervisor(
                id: $xgammaAddress
            ) {
                totalGamma
                totalSupply
            }
        }
        """
        variables = {
            "gammaAddress": self.address,
            "xgammaAddress": XGAMMA_ADDRESS,
            "days": self.days,
            "timezone": self.timezone,
        }
        response = await self.gamma_client.query(query, variables)
        self.data = response["data"]


class GammaCalculations(GammaData):
    def __init__(self, chain: Chain, days=30):
        super().__init__(chain=chain, days=days)

    async def basic_info(self, get_data=True):
        if get_data:
            await self._get_data()

        return {
            "totalDistributed": int(self.data["protocolDistribution"]["distributed"])
            / self.decimal_factor,
            "totalDistributedUSD": float(
                self.data["protocolDistribution"]["distributedUSD"]
            ),
            "totalStaked": int(self.data["rewardHypervisor"]["totalGamma"])
            / self.decimal_factor,
            "totalSupply": int(self.data["token"]["totalSupply"]) / self.decimal_factor,
        }

    def yield_table(self):
        df_dist = DataFrame(
            self.data["distributionDayDatas"], dtype=np.float64
        ).set_index("date")
        df_rh = DataFrame(
            self.data["rewardHypervisorDayDatas"], dtype=np.float64
        ).set_index("date")
        df_data = df_dist.join(df_rh, how="outer")
        df_data = df_data.sort_values("date")
        df_data.totalGamma = df_data.totalGamma.fillna(method="ffill").fillna(
            method="bfill"
        )
        df_data[["distributed", "distributedUSD"]] = df_data[
            ["distributed", "distributedUSD"]
        ].fillna(value=0)
        df_data["dailyYield"] = df_data.distributed / df_data.totalGamma

        return df_data

    async def gamma_yield(self, get_data=True):
        """Gets estimates such as APY, visor distributed"""

        if get_data:
            await self._get_data()

        if not self.data["distributionDayDatas"]:
            return self._empty_yield()

        df_data = self.yield_table()

        results = {}
        for period, days in DAYS_IN_PERIOD.items():
            df_period = df_data.tail(days).copy()
            n_days = len(df_period)
            annual_scaling_factor = 365 / n_days

            df_period["cumReturn"] = (1 + df_period["dailyYield"]).cumprod() - 1
            period_yield = df_period["cumReturn"].iat[-1]

            results[period] = {}
            results[period]["yield"] = period_yield
            results[period]["apr"] = period_yield * annual_scaling_factor
            results[period]["apy"] = (
                1 + period_yield / n_days
            ) ** 365 - 1  # compounded daily
            results[period]["estimatedAnnualDistribution"] = (
                df_period.distributed.sum() / self.decimal_factor
            ) * annual_scaling_factor
            results[period]["estimatedAnnualDistributionUSD"] = (
                df_period.distributedUSD.sum() * annual_scaling_factor
            )

        return results

    def _empty_yield(self):
        results = {}
        for period, days in DAYS_IN_PERIOD.items():
            results[period] = {}
            results[period]["yield"] = 0
            results[period]["apr"] = 0
            results[period]["apy"] = 0
            results[period]["estimatedAnnualDistribution"] = 0
            results[period]["estimatedAnnualDistributionUSD"] = 0

        return results

    async def distributions(self, days, get_data=True):
        if get_data:
            await self._get_data()

        df_data = self.yield_table()
        df_data = df_data[df_data.distributed > 0]

        df_data.reset_index(inplace=True)
        df_data.rename(columns={"date": "timestamp"}, inplace=True)
        df_data["date"] = to_datetime(df_data.timestamp, unit="s").dt.strftime(
            "%m/%d/%Y"
        )
        df_data["apr"] = df_data.dailyYield * 365
        df_data["apy"] = (1 + df_data.dailyYield) ** 365 - 1
        df_data.distributed = df_data.distributed / self.decimal_factor

        results = (
            df_data[
                ["timestamp", "date", "distributed", "distributedUSD", "apr", "apy"]
            ]
            .tail(days)
            .to_dict("records")
        )

        # results = [
        #     {
        #         "timestamp": day["date"],
        #         "date": timestamp_to_date(int(day["date"]), "%m/%d/%Y"),
        #         "distributed": float(day["distributed"]) / self.decimal_factor,
        #         "distributedUSD": float(day["distributedUSD"]),
        #     }
        #     for day in self.data["distributionDayDatas"]
        # ]

        return results


class GammaInfo(GammaCalculations):
    def __init__(self, chain: Chain, days=30):
        super().__init__(chain=chain, days=days)

    async def output(self):
        gamma_pricing, _ = await asyncio.gather(token_price("GAMMA"), self._get_data())

        return {
            "info": await self.basic_info(get_data=False),
            "yield": await self.gamma_yield(get_data=False),
            "price": gamma_pricing,
        }


class GammaYield(GammaCalculations):
    def __init__(self, chain: Chain, days=30):
        super().__init__(chain=chain, days=days)

    async def output(self):
        return await self.gamma_yield(get_data=True)


class GammaDistribution(GammaCalculations):
    def __init__(self, chain: Chain, days=60, timezone=DEFAULT_TIMEZONE):
        super().__init__(chain=chain, days=days)

    async def output(self, days):
        distributions = await self.distributions(days=days, get_data=True)

        return {"feeDistribution": distributions[::-1], "latest": distributions[-1]}


class ProtocolFeesData:
    def __init__(self, chain: Chain = Chain.MAINNET):
        self.gamma_client = GammaClient(Protocol.UNISWAP, chain)

    def _get_data(self, time_delta):
        query = """
        query  protocolFees(
            $xgammaAddress: String!,
            $timestamp_start: Int!,
            $grossFeesMax: Int!
        ) {
            uniswapV3Rebalances(
                where: {
                    timestamp_gt: $timestamp_start
                    grossFeesUSD_lt: $grossFeesMax
                }
            ) {
                timestamp
                protocolFeesUSD
            }
            rewardHypervisor(id: $xgammaAddress) {
                totalGamma
            }
        }
        """
        variables = {
            "xgammaAddress": XGAMMA_ADDRESS,
            "timestamp_start": timestamp_ago(time_delta),
            "groossFeesMax": GROSS_FEES_MAX,
        }
        self.data = self.gamma_client.query(query, variables)["data"]


class ProtocolFeesCalculations(ProtocolFeesData):
    def __init__(self, days=30):
        super().__init__()
        self.days = days

    def _empty_fees(self):
        results = {}
        for period, days in DAYS_IN_PERIOD.items():
            results[period] = {}
            results[period]["collected_usd"] = 0
            results[period]["collected_gamma"] = 0
            results[period]["yield"] = 0
            results[period]["apr"] = 0
            results[period]["apy"] = 0

        return results

    async def collected_fees(self, get_data=True):
        if get_data:
            self._get_data(timedelta(days=self.days))

        rebalances = self.data["uniswapV3Rebalances"]
        results = self._empty_fees()

        if not rebalances:
            return results

        df_rebalances = DataFrame(rebalances, dtype=np.float64)

        gamma_prices = await token_price("GAMMA")
        gamma_in_usd = gamma_prices["token_in_usdc"]

        gamma_staked_usd = (
            gamma_in_usd * int(self.data["rewardHypervisor"]["totalGamma"]) / 10**18
        )

        for period, days in DAYS_IN_PERIOD.items():
            df_period = df_rebalances[
                df_rebalances.timestamp > timestamp_ago(timedelta(days=days))
            ].copy()

            total_fees_in_period = df_period.protocolFeesUSD.sum()
            fees_per_day = total_fees_in_period / days

            daily_yield = fees_per_day / gamma_staked_usd
            fees_apr = daily_yield * 365
            fees_apy = (1 + daily_yield) ** 365 - 1

            results[period] = {}
            results[period]["collected_usd"] = fees_per_day
            results[period]["collected_gamma"] = fees_per_day / gamma_staked_usd
            results[period]["yield"] = daily_yield
            results[period]["apr"] = fees_apr
            results[period]["apy"] = fees_apy

        return results
