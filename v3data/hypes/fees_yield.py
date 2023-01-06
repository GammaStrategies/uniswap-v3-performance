import logging

import numpy as np
import pandas as pd

from v3data.constants import DAY_SECONDS, YEAR_SECONDS
from v3data.hypes.fees import Fees
from v3data.hypes.fees_yield_data import YieldData

YIELD_PER_DAY_MAX = 30

logger = logging.getLogger(__name__)


class FeesYield(YieldData):
    async def output(self, get_data=True):

        if get_data:
            await self.get_data()

        results = {}
        for hypervisor_address, hypervisors in self.data["hype_data"].items():
            symbol, hype_data = await self._aggregate_blocks(
                hypervisor_address, hypervisors
            )

            logger.info((f"Processing {symbol}: {hypervisor_address}"))
            returns = self._calculate_returns(hype_data)

            if returns:
                returns["symbol"] = symbol
                results[hypervisor_address] = returns

        return results

    def _calculate_returns(self, hype_data):
        df_hype = pd.DataFrame(hype_data, dtype=np.float64)

        if df_hype.empty:
            logger.info("No hypervisor data - skipping calculations")
            return

        df_hype = df_hype.set_index("block").sort_index()
        df_hype["elapsedTime"] = df_hype.timestamp.diff()
        df_hype["fee0Growth"] = df_hype.totalFees0.diff().clip(lower=0)
        df_hype["fee1Growth"] = df_hype.totalFees1.diff().clip(lower=0)

        logger.debug("\n\t" + df_hype.to_string().replace("\n", "\n\t"))

        df_hype["feeGrowthUSD"] = (
            df_hype.fee0Growth * df_hype.price0 + df_hype.fee1Growth * df_hype.price1
        )
        df_hype["periodYield"] = df_hype.feeGrowthUSD / df_hype.tvlUSD
        df_hype["yieldPerDay"] = (
            df_hype.periodYield * YEAR_SECONDS / df_hype["elapsedTime"]
        )

        has_outlier = (df_hype.yieldPerDay > YIELD_PER_DAY_MAX).any()
        df_hype = df_hype[df_hype.yieldPerDay < YIELD_PER_DAY_MAX]

        df_hype["totalPeriodSeconds"] = df_hype.elapsedTime.cumsum()
        df_hype["cumFeeReturn"] = (1 + df_hype.periodYield).cumprod() - 1

        logger.debug(
            "\n\t"
            + df_hype[
                [
                    "feeGrowthUSD",
                    "tvlUSD",
                    "periodYield",
                    "yieldPerDay",
                    "totalPeriodSeconds",
                    "cumFeeReturn",
                ]
            ]
            .to_string()
            .replace("\n", "\n\t")
        )

        df_returns = df_hype[["totalPeriodSeconds", "cumFeeReturn"]].tail(1)

        if df_returns.empty:
            logger.info("Empty returns")
            return

        # Extrapolate linearly to annual rate
        df_returns["feeApr"] = df_returns.cumFeeReturn * (
            YEAR_SECONDS / df_returns.totalPeriodSeconds
        )

        # Extrapolate by compounding
        df_returns["feeApy"] = (
            1 + df_returns.cumFeeReturn * (DAY_SECONDS / df_returns.totalPeriodSeconds)
        ) ** 365 - 1

        df_returns = df_returns.fillna(0).replace({np.inf: 0, -np.inf: 0})

        returns = df_returns.to_dict("records")[0]

        returns["feeApr"] = max(returns["feeApr"], 0)
        returns["feeApy"] = max(returns["feeApy"], 0)

        return {
            "feeApr": returns["feeApr"] if returns["feeApr"] else 0,
            "feeApy": returns["feeApy"] if returns["feeApy"] else 0,
            "hasOutlier": str(has_outlier),
        }

    async def _aggregate_blocks(self, hypervisor_address, hypervisors):
        symbol = ""
        hype_data = []
        for block, hypervisor in hypervisors.items():
            symbol = hypervisor["symbol"]
            fees = Fees(self.protocol, self.chain)
            fees.data = [hypervisor]
            output = await fees._hypervisor_fees(get_data=False)
            if not output.get(hypervisor_address):
                continue
            hype_fees = output[hypervisor_address]
            hype_data.append(
                {
                    "block": block,
                    "timestamp": hypervisor["timestamp"],
                    "tvlUSD": hypervisor["tvlUSD"],
                    "totalFees0": (
                        hype_fees["base"]["fees0"]
                        + hype_fees["base"]["owed0"]
                        + hype_fees["limit"]["fees0"]
                        + hype_fees["limit"]["owed0"]
                    ),
                    "totalFees1": (
                        hype_fees["base"]["fees1"]
                        + hype_fees["base"]["owed1"]
                        + hype_fees["limit"]["fees1"]
                        + hype_fees["limit"]["owed1"]
                    ),
                    "price0": hype_fees["tokens"]["price0"],
                    "price1": hype_fees["tokens"]["price1"],
                }
            )

        return symbol, hype_data
