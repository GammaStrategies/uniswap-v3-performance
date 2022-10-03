from v3data.hypes.fees_data import FeesData
from v3data.utils import sub_in_256


class Fees(FeesData):
    async def output(self, hypervisor_addresses: list[str] = None, get_data=True):
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
                base_fees_0_usd = base_fees_0 * priceBaseInUSD
                base_fees_1_usd = base_fees_1 * priceTokenInBase * priceBaseInUSD
                base_tokens_owed_0_usd = base_tokens_owed_0 * priceBaseInUSD
                base_tokens_owed_1_usd = (
                    base_tokens_owed_1 * priceTokenInBase * priceBaseInUSD
                )
                limit_fees_0_usd = limit_fees_0 * priceBaseInUSD
                limit_fees_1_usd = limit_fees_1 * priceTokenInBase * priceBaseInUSD
                limit_tokens_owed_0_usd = limit_tokens_owed_0 * priceBaseInUSD
                limit_tokens_owed_1_usd = (
                    limit_tokens_owed_1 * priceTokenInBase * priceBaseInUSD
                )
            elif baseTokenIndex == 1:
                base_fees_0_usd = base_fees_0 * priceTokenInBase * priceBaseInUSD
                base_fees_1_usd = base_fees_1 * priceBaseInUSD
                base_tokens_owed_0_usd = (
                    base_tokens_owed_0 * priceTokenInBase * priceBaseInUSD
                )
                base_tokens_owed_1_usd = base_tokens_owed_1 * priceBaseInUSD
                limit_fees_0_usd = limit_fees_0 * priceTokenInBase * priceBaseInUSD
                limit_fees_1_usd = limit_fees_1 * priceBaseInUSD
                limit_tokens_owed_0_usd = (
                    limit_tokens_owed_0 * priceTokenInBase * priceBaseInUSD
                )
                limit_tokens_owed_1_usd = limit_tokens_owed_1 * priceBaseInUSD
            else:
                base_fees_0_usd = 0
                base_fees_1_usd = 0
                base_tokens_owed_0_usd = 0
                base_tokens_owed_1_usd = 1
                limit_fees_0_usd = 0
                limit_fees_1_usd = 0
                limit_tokens_owed_0_usd = 0
                limit_tokens_owed_1_usd = 0

            uncollected_fees_total = (
                base_fees_0_usd
                + base_fees_1_usd
                + base_tokens_owed_0_usd
                + base_tokens_owed_1_usd
                + limit_fees_0_usd
                + limit_fees_1_usd
                + limit_tokens_owed_0_usd
                + limit_tokens_owed_1_usd
            )

            results[hypervisor["id"]] = {
                "symbol": hypervisor["symbol"],
                "baseFees0": base_fees_0 / 10**decimals_0,
                "baseFees1": base_fees_1 / 10**decimals_1,
                "baseTokensOwed0": base_tokens_owed_0 / 10**decimals_0,
                "baseTokensOwed1": base_tokens_owed_1 / 10**decimals_1,
                "limitFees0": limit_fees_0 / 10**decimals_0,
                "limitFees1": limit_fees_1 / 10**decimals_1,
                "limitTokensOwed0": limit_tokens_owed_0 / 10**decimals_0,
                "limitTokensOwed1": limit_tokens_owed_1 / 10**decimals_1,
                "baseFees0USD": base_fees_0_usd,
                "baseFees1USD": base_fees_1_usd,
                "baseTokensOwed0USD": base_tokens_owed_0_usd,
                "baseTokensOwed1USD": base_tokens_owed_1_usd,
                "limitFees0USD": limit_fees_0_usd,
                "limitFees1USD": limit_fees_1_usd,
                "limitTokensOwed0USD": limit_tokens_owed_0_usd,
                "limitTokensOwed1USD": limit_tokens_owed_1_usd,
                "totalFees0": (
                    base_fees_0
                    + base_tokens_owed_0
                    + limit_fees_0
                    + limit_tokens_owed_0
                )
                / 10**decimals_0,
                "totalFees1": (
                    base_fees_1
                    + base_tokens_owed_1
                    + limit_fees_1
                    + limit_tokens_owed_1
                )
                / 10**decimals_1,
                "totalFeesUSD": uncollected_fees_total,
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
