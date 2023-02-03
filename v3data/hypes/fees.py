from datetime import timedelta
import logging
from v3data.hypes.fees_data import FeesData
from v3data.utils import sub_in_256, timestamp_ago

logger = logging.getLogger(__name__)


class Fees(FeesData):
    async def output(self, hypervisor_addresses=None, get_data=True):
        fees_data = await self._hypervisor_fees(hypervisor_addresses, get_data)

        results = {}
        for hypervisor_id, hypervisor in fees_data.items():
            base_fees_0 = hypervisor["base"]["fees0"]
            base_fees_1 = hypervisor["base"]["fees1"]
            base_tokens_owed_0 = hypervisor["base"]["owed0"]
            base_tokens_owed_1 = hypervisor["base"]["owed1"]

            limit_fees_0 = hypervisor["limit"]["fees0"]
            limit_fees_1 = hypervisor["limit"]["fees1"]
            limit_tokens_owed_0 = hypervisor["limit"]["owed0"]
            limit_tokens_owed_1 = hypervisor["limit"]["owed1"]

            token0_price = hypervisor["tokens"]["price0"]
            token1_price = hypervisor["tokens"]["price1"]

            total_fees_0 = (
                base_fees_0 + base_tokens_owed_0 + limit_fees_0 + limit_tokens_owed_0
            )

            total_fees_1 = (
                base_fees_1 + base_tokens_owed_1 + limit_fees_1 + limit_tokens_owed_1
            )

            results[hypervisor_id] = {
                "symbol": hypervisor["symbol"],
                "baseFees0": base_fees_0 / 10 ** hypervisor["tokens"]["decimals0"],
                "baseFees1": base_fees_1 / 10 ** hypervisor["tokens"]["decimals1"],
                "baseTokensOwed0": base_tokens_owed_0
                / 10 ** hypervisor["tokens"]["decimals0"],
                "baseTokensOwed1": base_tokens_owed_1
                / 10 ** hypervisor["tokens"]["decimals1"],
                "limitFees0": limit_fees_0 / 10 ** hypervisor["tokens"]["decimals0"],
                "limitFees1": limit_fees_1 / 10 ** hypervisor["tokens"]["decimals1"],
                "limitTokensOwed0": limit_tokens_owed_0
                / 10 ** hypervisor["tokens"]["decimals0"],
                "limitTokensOwed1": limit_tokens_owed_1
                / 10 ** hypervisor["tokens"]["decimals1"],
                "baseFees0USD": base_fees_0 * token0_price,
                "baseFees1USD": base_fees_1 * token1_price,
                "baseTokensOwed0USD": base_tokens_owed_0 * token0_price,
                "baseTokensOwed1USD": base_tokens_owed_1 * token1_price,
                "limitFees0USD": limit_fees_0 * token0_price,
                "limitFees1USD": limit_fees_1 * token1_price,
                "limitTokensOwed0USD": limit_tokens_owed_0 * token0_price,
                "limitTokensOwed1USD": limit_tokens_owed_1 * token1_price,
                "totalFees0": total_fees_0 / 10 ** hypervisor["tokens"]["decimals0"],
                "totalFees1": total_fees_1 / 10 ** hypervisor["tokens"]["decimals1"],
                "totalFeesUSD": total_fees_0 * token0_price
                + total_fees_1 * token1_price,
            }

        return results

    async def _hypervisor_fees(self, hypervisor_addresses=None, get_data=True):
        if get_data:
            await self._get_data(hypervisor_addresses)

        results = {}
        for hypervisor in self.data:

            decimals_0 = int(hypervisor["pool"]["token0"]["decimals"])
            decimals_1 = int(hypervisor["pool"]["token1"]["decimals"])

            if not hypervisor.get("ticks"):
                continue

            try:
                base_fees_0, base_fees_1 = self.calc_fees(
                    fee_growth_global_0=int(
                        hypervisor["ticks"]["pool"]["feeGrowthGlobal0X128"]
                    ),
                    fee_growth_global_1=int(
                        hypervisor["ticks"]["pool"]["feeGrowthGlobal1X128"]
                    ),
                    tick_current=int(hypervisor["ticks"]["pool"]["tick"]),
                    tick_lower=int(hypervisor["baseLower"]),
                    tick_upper=int(hypervisor["baseUpper"]),
                    fee_growth_outside_0_lower=int(
                        hypervisor["ticks"]["baseLower"][0]["feeGrowthOutside0X128"]
                    ),
                    fee_growth_outside_1_lower=int(
                        hypervisor["ticks"]["baseLower"][0]["feeGrowthOutside1X128"]
                    ),
                    fee_growth_outside_0_upper=int(
                        hypervisor["ticks"]["baseUpper"][0]["feeGrowthOutside0X128"]
                    ),
                    fee_growth_outside_1_upper=int(
                        hypervisor["ticks"]["baseUpper"][0]["feeGrowthOutside1X128"]
                    ),
                    liquidity=int(hypervisor["baseLiquidity"]),
                    fee_growth_inside_last_0=int(
                        hypervisor["baseFeeGrowthInside0LastX128"]
                    ),
                    fee_growth_inside_last_1=int(
                        hypervisor["baseFeeGrowthInside1LastX128"]
                    ),
                )
            except IndexError:
                base_fees_0 = 0
                base_fees_1 = 0

            base_tokens_owed_0 = float(hypervisor["baseTokensOwed0"])
            base_tokens_owed_1 = float(hypervisor["baseTokensOwed1"])

            try:
                limit_fees_0, limit_fees_1 = self.calc_fees(
                    fee_growth_global_0=int(
                        hypervisor["ticks"]["pool"]["feeGrowthGlobal0X128"]
                    ),
                    fee_growth_global_1=int(
                        hypervisor["ticks"]["pool"]["feeGrowthGlobal1X128"]
                    ),
                    tick_current=int(hypervisor["ticks"]["pool"]["tick"]),
                    tick_lower=int(hypervisor["limitLower"]),
                    tick_upper=int(hypervisor["limitUpper"]),
                    fee_growth_outside_0_lower=int(
                        hypervisor["ticks"]["limitLower"][0]["feeGrowthOutside0X128"]
                    ),
                    fee_growth_outside_1_lower=int(
                        hypervisor["ticks"]["limitLower"][0]["feeGrowthOutside1X128"]
                    ),
                    fee_growth_outside_0_upper=int(
                        hypervisor["ticks"]["limitUpper"][0]["feeGrowthOutside0X128"]
                    ),
                    fee_growth_outside_1_upper=int(
                        hypervisor["ticks"]["limitUpper"][0]["feeGrowthOutside1X128"]
                    ),
                    liquidity=int(hypervisor["limitLiquidity"]),
                    fee_growth_inside_last_0=int(
                        hypervisor["limitFeeGrowthInside0LastX128"]
                    ),
                    fee_growth_inside_last_1=int(
                        hypervisor["limitFeeGrowthInside1LastX128"]
                    ),
                )
            except IndexError:
                limit_fees_0 = 0
                limit_fees_1 = 0

            limit_tokens_owed_0 = float(hypervisor["limitTokensOwed0"])
            limit_tokens_owed_1 = float(hypervisor["limitTokensOwed1"])

            # Convert to USD
            baseTokenIndex = int(hypervisor["conversion"]["baseTokenIndex"])
            priceTokenInBase = float(hypervisor["conversion"]["priceTokenInBase"])
            priceBaseInUSD = float(hypervisor["conversion"]["priceBaseInUSD"])

            if baseTokenIndex == 0:
                token0_price = priceBaseInUSD
                token1_price = priceTokenInBase * priceBaseInUSD
            elif baseTokenIndex == 1:
                token0_price = priceTokenInBase * priceBaseInUSD
                token1_price = priceBaseInUSD
            else:
                token0_price = 0
                token1_price = 0

            results[hypervisor["id"]] = {
                "id": hypervisor["id"],
                "symbol": hypervisor["symbol"],
                "base": {
                    "fees0": base_fees_0,
                    "fees1": base_fees_1,
                    "owed0": base_tokens_owed_0,
                    "owed1": base_tokens_owed_1,
                },
                "limit": {
                    "fees0": limit_fees_0,
                    "fees1": limit_fees_1,
                    "owed0": limit_tokens_owed_0,
                    "owed1": limit_tokens_owed_1,
                },
                "tokens": {
                    "price0": token0_price,
                    "price1": token1_price,
                    "decimals0": decimals_0,
                    "decimals1": decimals_1,
                },
            }

        return results

    async def output_for_returns_calc(self, hypervisor_address, get_data=True):
        fees = await self.output(hypervisor_address, get_data)

        gross_fees = max(
            (
                fees["base_fees_0_usd"]
                + fees["base_fees_1_usd"]
                + fees["limit_fees_0_usd"]
                + fees["limit_fees_1_usd"]
            ),
            0,
        )

        return {
            "id": "uncollected_fees",
            "timestamp": timestamp_ago(timedelta(0)),
            "grossFeesUSD": gross_fees,
            "protocolFeesUSD": gross_fees * 0.1,
            "netFeesUSD": gross_fees * 0.9,
            "totalAmountUSD": fees["tvl_usd"],
        }

    @staticmethod
    def calc_fees(
        fee_growth_global_0,
        fee_growth_global_1,
        tick_current,
        tick_lower,
        tick_upper,
        fee_growth_outside_0_lower,
        fee_growth_outside_1_lower,
        fee_growth_outside_0_upper,
        fee_growth_outside_1_upper,
        liquidity,
        fee_growth_inside_last_0,
        fee_growth_inside_last_1,
    ):
        X128 = 2**128

        if tick_current >= tick_lower:
            fee_growth_below_pos_0 = fee_growth_outside_0_lower
            fee_growth_below_pos_1 = fee_growth_outside_1_lower
        else:
            fee_growth_below_pos_0 = sub_in_256(
                fee_growth_global_0, fee_growth_outside_0_lower
            )
            fee_growth_below_pos_1 = sub_in_256(
                fee_growth_global_1, fee_growth_outside_1_lower
            )

        if tick_current >= tick_upper:
            fee_growth_above_pos_0 = sub_in_256(
                fee_growth_global_0, fee_growth_outside_0_upper
            )
            fee_growth_above_pos_1 = sub_in_256(
                fee_growth_global_1, fee_growth_outside_1_upper
            )
        else:
            fee_growth_above_pos_0 = fee_growth_outside_0_upper
            fee_growth_above_pos_1 = fee_growth_outside_1_upper

        fees_accum_now_0 = sub_in_256(
            sub_in_256(fee_growth_global_0, fee_growth_below_pos_0),
            fee_growth_above_pos_0,
        )
        fees_accum_now_1 = sub_in_256(
            sub_in_256(fee_growth_global_1, fee_growth_below_pos_1),
            fee_growth_above_pos_1,
        )

        uncollectedFees_0 = (
            liquidity * (sub_in_256(fees_accum_now_0, fee_growth_inside_last_0))
        ) / X128
        uncollectedFees_1 = (
            liquidity * (sub_in_256(fees_accum_now_1, fee_growth_inside_last_1))
        ) / X128

        return uncollectedFees_0, uncollectedFees_1
