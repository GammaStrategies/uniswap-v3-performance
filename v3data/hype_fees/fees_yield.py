import logging

import numpy as np
from pandas import DataFrame

from v3data.hype_fees.data import FeeGrowthSnapshotData
from v3data.hype_fees.fees import Fees
from v3data.hype_fees.schema import FeesData, FeesSnapshot, FeeYield
from v3data.constants import X128, DAY_SECONDS, YEAR_SECONDS

logger = logging.getLogger(__name__)

YIELD_PER_DAY_MAX = 300


class FeesYield:
    def __init__(self, data: [FeesData], protocol: str, chain: str) -> None:
        self.data = data
        self.protocol = protocol
        self.chain = chain

    def calculate_returns(self) -> FeeYield:
        snapshots = [self.get_fees(entry) for entry in self.data]
        df_snapshots = DataFrame(snapshots, dtype=np.float64)

        #  Require at least two rows to calculate yield
        if len(df_snapshots) < 2:
            logger.info("No hypervisor data - skipping calculations")
            return FeeYield(
                apr=0,
                apy=0,
                status="Insufficient Data",
            )

        df_snapshots = df_snapshots.set_index("block").sort_index()
        df_snapshots["elapsed_time"] = df_snapshots.timestamp.diff()
        df_snapshots["fee0_growth"] = df_snapshots.total_fees_0.diff().clip(lower=0)
        df_snapshots["fee1_growth"] = df_snapshots.total_fees_1.diff().clip(lower=0)

        df_snapshots["fee_growth_usd"] = (
            df_snapshots.fee0_growth * df_snapshots.price_0
            + df_snapshots.fee1_growth * df_snapshots.price_1
        )
        df_snapshots["period_yield"] = (
            df_snapshots.fee_growth_usd / df_snapshots.tvl_usd
        )
        df_snapshots["yield_per_day"] = (
            df_snapshots.period_yield * YEAR_SECONDS / df_snapshots.elapsed_time
        )

        has_outlier = (df_snapshots.yield_per_day > YIELD_PER_DAY_MAX).any()
        df_snapshots = df_snapshots[df_snapshots.yield_per_day < YIELD_PER_DAY_MAX]

        df_snapshots["total_period_seconds"] = df_snapshots.elapsed_time.cumsum()
        df_snapshots["cum_fee_return"] = (1 + df_snapshots.period_yield).cumprod() - 1

        df_returns = df_snapshots[["total_period_seconds", "cum_fee_return"]].tail(1)

        # This is a failsafe for if there are outliers
        if df_returns.empty:
            logger.info("Empty returns")
            return FeeYield(
                apr=0,
                apy=0,
                status="Insufficient good data",
            )

        # Extrapolate linearly to annual rate
        df_returns["fee_apr"] = df_returns.cum_fee_return * (
            YEAR_SECONDS / df_returns.total_period_seconds
        )

        # Extrapolate by compounding
        df_returns["fee_apy"] = (
            1
            + df_returns.cum_fee_return
            * (DAY_SECONDS / df_returns.total_period_seconds)
        ) ** 365 - 1

        df_returns = df_returns.fillna(0).replace({np.inf: 0, -np.inf: 0})

        returns = df_returns.to_dict("records")[0]

        returns["fee_apr"] = max(returns["fee_apr"], 0)
        returns["fee_apy"] = max(returns["fee_apy"], 0)

        return FeeYield(
            apr=returns["fee_apr"] if returns["fee_apr"] else 0,
            apy=returns["fee_apy"] if returns["fee_apy"] else 0,
            status="Outlier removed" if has_outlier else "Good",
        )

    def get_fees(self, fees_data: FeesData) -> FeesSnapshot:
        fees = Fees(fees_data, self.protocol, self.chain)
        fee_amounts_x128 = fees.fee_amounts()

        total_fees_0 = (
            (
                fee_amounts_x128.base.value0
                + fee_amounts_x128.limit.value0
                + fees_data.base_position.tokens_owed.value0
                + fees_data.limit_position.tokens_owed.value0
            )
            / 10**fees_data.decimals.value0
            / X128
        )

        total_fees_1 = (
            (
                fee_amounts_x128.base.value1
                + fee_amounts_x128.limit.value1
                + fees_data.base_position.tokens_owed.value1
                + fees_data.limit_position.tokens_owed.value1
            )
            / 10**fees_data.decimals.value1
            / X128
        )

        return FeesSnapshot(
            block=fees_data.block,
            timestamp=fees_data.timestamp,
            tvl_usd=fees_data.tvl_usd,
            total_fees_0=total_fees_0,
            total_fees_1=total_fees_1,
            price_0=fees_data.price.value0,
            price_1=fees_data.price.value1,
        )


async def fee_returns_all(protocol: str, chain: str, days: int):
    fees_data = FeeGrowthSnapshotData(days, protocol, chain)
    await fees_data.get_data()

    results = {}
    for hypervisor_id, fees_data in fees_data.data.items():
        fees_yield = FeesYield(fees_data, protocol, chain)
        returns = fees_yield.calculate_returns()
        results[hypervisor_id] = {
            "symbol": fees_data[0].symbol,
            "feeApr": returns.apr,
            "feeApy": returns.apy,
            "status": returns.status
        }
    return results
