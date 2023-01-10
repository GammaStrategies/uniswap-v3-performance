import asyncio
from datetime import timedelta

from v3data import GammaClient, LlamaClient, UniswapV3Client
from v3data.hypes.fees import Fees

from v3data.utils import timestamp_ago
from v3data.constants import BLOCK_TIME_SECONDS
from v3data.hypes.fees_yield import FeesYield


class ImpermanentResult(FeesYield):
    async def _get_hypervisor_data_at_block(self, block, hypervisors=None):

        if hypervisors:
            # defined hypervisors data query
            query = """
                    query hypervisor($block: Int!, $ids: [String!]!){
                        uniswapV3Hypervisors(
                            block: {
                                number: $block
                            }
                            where: {
                                id_in: $ids
                            }
                        ){
                            id
                            symbol
                            tvlUSD
                            tvl0
                            tvl1
                            totalSupply
                            baseTokensOwed0
                            baseTokensOwed1
                            limitTokensOwed0
                            limitTokensOwed1
                            baseLiquidity
                            baseLower
                            baseUpper
                            baseTokensOwed0
                            baseTokensOwed1
                            baseFeeGrowthInside0LastX128
                            baseFeeGrowthInside1LastX128
                            limitLiquidity
                            limitLower
                            limitUpper
                            limitTokensOwed0
                            limitTokensOwed1
                            limitFeeGrowthInside0LastX128
                            limitFeeGrowthInside1LastX128
                            pool{
                                id
                                token0 {decimals}
                                token1 {decimals}
                            }
                            conversion {
                                baseTokenIndex
                                priceTokenInBase
                                priceBaseInUSD
                            }
                        }
                    }
                    """
            variables = {"block": int(block), "ids": hypervisors}
        else:
            # all possible hypervisor data query
            query = """
                    query hypervisor($block: Int!){
                        uniswapV3Hypervisors(
                            block: {
                                number: $block
                            }
                        ){
                            id
                            symbol
                            tvlUSD
                            tvl0
                            tvl1
                            totalSupply
                            baseTokensOwed0
                            baseTokensOwed1
                            limitTokensOwed0
                            limitTokensOwed1
                            baseLiquidity
                            baseLower
                            baseUpper
                            baseTokensOwed0
                            baseTokensOwed1
                            baseFeeGrowthInside0LastX128
                            baseFeeGrowthInside1LastX128
                            limitLiquidity
                            limitLower
                            limitUpper
                            limitTokensOwed0
                            limitTokensOwed1
                            limitFeeGrowthInside0LastX128
                            limitFeeGrowthInside1LastX128
                            pool{
                                id
                                token0 {decimals}
                                token1 {decimals}
                            }
                            conversion {
                                baseTokenIndex
                                priceTokenInBase
                                priceBaseInUSD
                            }
                        }
                    }
                    """
            variables = {"block": int(block)}

        response = await self.gamma_client.query(query, variables)

        return response

    async def _get_pool_data_at_block(
        self, block, pool_address, base_lower, base_upper, limit_lower, limit_upper
    ):
        pool_query = """
        query pool(
            $block: Int!
            $poolAddress: String!
            $baseLower: Int!
            $baseUpper: Int!
            $limitLower: Int!
            $limitUpper: Int!
        ){
            pool(
                id: $poolAddress
                block: {number: $block}
            ){
                id
                tick
                feeGrowthGlobal0X128
                feeGrowthGlobal1X128
            }
            baseLower: ticks(
                block: {number: $block}
                where: {
                poolAddress: $poolAddress
                tickIdx: $baseLower
                }
            ){
                tickIdx
                feeGrowthOutside0X128
                feeGrowthOutside1X128
            },
            baseUpper: ticks(
                block: {number: $block}
                where: {
                poolAddress: $poolAddress
                tickIdx: $baseUpper
                }
            ){
                tickIdx
                feeGrowthOutside0X128
                feeGrowthOutside1X128
            },
            limitLower: ticks(
                block: {number: $block}
                where: {
                poolAddress: $poolAddress
                tickIdx: $limitLower
                }
            ){
                tickIdx
                feeGrowthOutside0X128
                feeGrowthOutside1X128
            },
            limitUpper: ticks(
                block: {number: $block}
                where: {
                poolAddress: $poolAddress
                tickIdx: $limitUpper
                }
            ){
                tickIdx
                feeGrowthOutside0X128
                feeGrowthOutside1X128
            }
        }
        """

        variables = {
            "block": int(block),
            "poolAddress": pool_address,
            "baseLower": base_lower,
            "baseUpper": base_upper,
            "limitLower": limit_lower,
            "limitUpper": limit_upper,
        }

        response = await self.uniswap_client.query(pool_query, variables)

        return response["data"]

    async def get_impermanent_data(self, get_data=True):

        if get_data:
            await self.get_data()

        # get hypervisors data
        hypervisor_dta = self._hypervisor_data_by_blocks

        # get pool data
        pool_data = self._pool_data

        # prepare n fill data structure
        data_by_hypervisor = {}
        #  { <hypervisor id> : [ <initial data>, <current data> ]
        #                        <data> includes "self._get_hypervisor_data_at_block()", "block" and "token0_usd_price" , "token1_usd_price" fields

        # only start and end block datas are used
        for idx, block in enumerate(
            [self.data["initial_block"], self.data["current_block"]]
        ):
            for hypervisor in hypervisor_dta[block]:

                pool = None
                try:
                    tick_id = self.tick_id(
                        block=block,
                        address=hypervisor["pool"]["id"],
                        baseLower=hypervisor["baseLower"],
                        baseUpper=hypervisor["baseUpper"],
                        limitLower=hypervisor["limitLower"],
                        limitUpper=hypervisor["limitUpper"],
                    )
                    pool = pool_data[tick_id]
                except:
                    continue

                # add to structure
                if not hypervisor["id"] in data_by_hypervisor:
                    data_by_hypervisor[hypervisor["id"]] = [
                        dict(),
                        dict(),
                    ]  # init block , end block data

                # convert types
                hypervisor = self._convert_dataTypes(hypervisor)

                # add block and timestamp to hypervisor
                hypervisor["block"] = block
                hypervisor["timestamp"] = self._block_ts_map[block]

                # add usd prices
                (
                    hypervisor["token0_usd_price"],
                    hypervisor["token1_usd_price"],
                ) = self._calc_USD_prices(hypervisor=hypervisor)

                # get uncollected base fees
                decimals_0 = int(hypervisor["pool"]["token0"]["decimals"])
                decimals_1 = int(hypervisor["pool"]["token1"]["decimals"])

                try:
                    base_fees_0, base_fees_1 = Fees.calc_fees(
                        fee_growth_global_0=int(pool["pool"]["feeGrowthGlobal0X128"]),
                        fee_growth_global_1=int(pool["pool"]["feeGrowthGlobal1X128"]),
                        tick_current=int(pool["pool"]["tick"]),
                        tick_lower=int(hypervisor["baseLower"]),
                        tick_upper=int(hypervisor["baseUpper"]),
                        fee_growth_outside_0_lower=int(
                            pool["baseLower"][0]["feeGrowthOutside0X128"]
                        ),
                        fee_growth_outside_1_lower=int(
                            pool["baseLower"][0]["feeGrowthOutside1X128"]
                        ),
                        fee_growth_outside_0_upper=int(
                            pool["baseUpper"][0]["feeGrowthOutside0X128"]
                        ),
                        fee_growth_outside_1_upper=int(
                            pool["baseUpper"][0]["feeGrowthOutside1X128"]
                        ),
                        liquidity=int(hypervisor["baseLiquidity"]),
                        fee_growth_inside_last_0=int(
                            hypervisor["baseFeeGrowthInside0LastX128"]
                        ),
                        fee_growth_inside_last_1=int(
                            hypervisor["baseFeeGrowthInside1LastX128"]
                        ),
                    )
                    # convert
                    base_fees_0 /= 10**decimals_0
                    base_fees_1 /= 10**decimals_1

                except:
                    base_fees_0 = 0
                    base_fees_1 = 0
                # get uncollected limit fees
                try:
                    limit_fees_0, limit_fees_1 = Fees.calc_fees(
                        fee_growth_global_0=int(pool["pool"]["feeGrowthGlobal0X128"]),
                        fee_growth_global_1=int(pool["pool"]["feeGrowthGlobal1X128"]),
                        tick_current=int(pool["pool"]["tick"]),
                        tick_lower=int(hypervisor["limitLower"]),
                        tick_upper=int(hypervisor["limitUpper"]),
                        fee_growth_outside_0_lower=int(
                            pool["limitLower"][0]["feeGrowthOutside0X128"]
                        ),
                        fee_growth_outside_1_lower=int(
                            pool["limitLower"][0]["feeGrowthOutside1X128"]
                        ),
                        fee_growth_outside_0_upper=int(
                            pool["limitUpper"][0]["feeGrowthOutside0X128"]
                        ),
                        fee_growth_outside_1_upper=int(
                            pool["limitUpper"][0]["feeGrowthOutside1X128"]
                        ),
                        liquidity=int(hypervisor["limitLiquidity"]),
                        fee_growth_inside_last_0=int(
                            hypervisor["limitFeeGrowthInside0LastX128"]
                        ),
                        fee_growth_inside_last_1=int(
                            hypervisor["limitFeeGrowthInside1LastX128"]
                        ),
                    )
                    # convert
                    limit_fees_0 /= 10**decimals_0
                    limit_fees_1 /= 10**decimals_1

                except:
                    limit_fees_0 = 0
                    limit_fees_1 = 0

                # set uncollected fees field
                hypervisor["uncollected_fees0"] = (
                    base_fees_0
                    + limit_fees_0
                    + hypervisor["baseTokensOwed0"]
                    + hypervisor["limitTokensOwed0"]
                )
                hypervisor["uncollected_fees1"] = (
                    base_fees_1
                    + limit_fees_1
                    + hypervisor["baseTokensOwed1"]
                    + hypervisor["limitTokensOwed1"]
                )

                # add to structure
                data_by_hypervisor[hypervisor["id"]][idx] = hypervisor

        # build result
        all_data = {}
        for hypervisor_id, struct in data_by_hypervisor.items():

            if len(struct[0].keys()) == 0:
                # hypervisor didnt exist at start block
                # zero sum content
                struct[0] = struct[1]

            # time passed
            blocks_passed = int(struct[1]["block"]) - int(struct[0]["block"])
            seconds_passed = int(struct[1]["timestamp"]) - int(struct[0]["timestamp"])

            if struct[0]["totalSupply"] != 0 and struct[1]["totalSupply"] != 0:

                initial_tvl0 = struct[0]["tvl0"] + struct[0]["uncollected_fees0"]
                initial_tvl1 = struct[0]["tvl1"] + struct[0]["uncollected_fees1"]

                current_tvl0 = struct[1]["tvl0"] + struct[1]["uncollected_fees0"]
                current_tvl1 = struct[1]["tvl1"] + struct[1]["uncollected_fees1"]

                # hodl usd
                ini_hodl_usd = (
                    initial_tvl0 * struct[0]["token0_usd_price"]
                    + initial_tvl1 * struct[0]["token1_usd_price"]
                ) / struct[0]["totalSupply"]
                cur_hodl_usd = (
                    current_tvl0 * struct[1]["token0_usd_price"]
                    + current_tvl1 * struct[1]["token1_usd_price"]
                ) / struct[1]["totalSupply"]
                vs_hodl_usd = (
                    ((cur_hodl_usd - ini_hodl_usd) / ini_hodl_usd)
                    if ini_hodl_usd != 0
                    else 0
                )

                # hodl deposited tokens proportion ( use curr prices with initial qtties)
                ini_hodl_deposited = (
                    initial_tvl0 * struct[1]["token0_usd_price"]
                    + initial_tvl1 * struct[1]["token1_usd_price"]
                ) / struct[1]["totalSupply"]
                cur_hodl_deposited = cur_hodl_usd
                vs_hodl_deposited = (
                    ((cur_hodl_deposited - ini_hodl_deposited) / ini_hodl_deposited)
                    if ini_hodl_deposited != 0
                    else 0
                )

                # hodl token0
                ini_hodl_token0 = (
                    initial_tvl0
                    + (
                        initial_tvl1
                        * (
                            struct[0]["token1_usd_price"]
                            / struct[0]["token0_usd_price"]
                        )
                    )
                ) / struct[0]["totalSupply"]
                cur_hodl_token0 = (
                    current_tvl0
                    + (
                        current_tvl1
                        * (
                            struct[1]["token1_usd_price"]
                            / struct[1]["token0_usd_price"]
                        )
                    )
                ) / struct[1]["totalSupply"]
                vs_hodl_token0 = (
                    ((cur_hodl_token0 - ini_hodl_token0) / ini_hodl_token0)
                    if ini_hodl_token0 != 0
                    else 0
                )

                # hodl token1
                ini_hodl_token1 = (
                    initial_tvl1
                    + (
                        initial_tvl0
                        * (
                            struct[0]["token0_usd_price"]
                            / struct[0]["token1_usd_price"]
                        )
                    )
                ) / struct[0]["totalSupply"]
                cur_hodl_token1 = (
                    current_tvl1
                    + (
                        current_tvl0
                        * (
                            struct[1]["token0_usd_price"]
                            / struct[1]["token1_usd_price"]
                        )
                    )
                ) / struct[1]["totalSupply"]
                vs_hodl_token1 = (
                    ((cur_hodl_token1 - ini_hodl_token1) / ini_hodl_token1)
                    if ini_hodl_token1 != 0
                    else 0
                )

            else:
                vs_hodl_usd = vs_hodl_deposited = vs_hodl_token0 = vs_hodl_token1 = 0

            # add to result
            all_data[hypervisor_id] = {
                "id": hypervisor_id,
                "symbol": struct[0]["symbol"],
                "blocks_passed": blocks_passed,
                "seconds_passed": seconds_passed,
                "vs_hodl_usd": vs_hodl_usd,
                "vs_hodl_deposited": vs_hodl_deposited,
                "vs_hodl_token0": vs_hodl_token0,
                "vs_hodl_token1": vs_hodl_token1,
                # test fields TODO: remove
                "ini_supply": struct[0]["totalSupply"],
                "ini_tvl0": struct[0]["tvl0"],
                "ini_tvl1": struct[0]["tvl1"],
                "ini_tvlUSD": struct[0]["tvlUSD"],
                "ini_uncollected_fees0": struct[0]["uncollected_fees0"],
                "ini_uncollected_fees1": struct[0]["uncollected_fees1"],
                "ini_token0_usd_price": struct[0]["token0_usd_price"],
                "ini_token1_usd_price": struct[0]["token1_usd_price"],
                "end_supply": struct[1]["totalSupply"],
                "end_tvl0": struct[1]["tvl0"],
                "end_tvl1": struct[1]["tvl1"],
                "end_tvlUSD": struct[1]["tvlUSD"],
                "end_uncollected_fees0": struct[1]["uncollected_fees0"],
                "end_uncollected_fees1": struct[1]["uncollected_fees1"],
                "end_token0_usd_price": struct[1]["token0_usd_price"],
                "end_token1_usd_price": struct[1]["token1_usd_price"],
                "symbol_1": struct[1]["symbol"],
            }

        return all_data

    # HELPERs
    def _convert_dataTypes(self, hypervisor: dict) -> dict:
        # convert data
        decimals_0 = int(hypervisor["pool"]["token0"]["decimals"])
        decimals_1 = int(hypervisor["pool"]["token1"]["decimals"])

        # TODO: convert conversion fields

        hypervisor["tvl0"] = int(hypervisor["tvl0"]) / (10**decimals_0)
        hypervisor["tvl1"] = int(hypervisor["tvl1"]) / (10**decimals_1)
        hypervisor["tvlUSD"] = float(hypervisor["tvlUSD"])
        hypervisor["totalSupply"] = int(hypervisor["totalSupply"]) / (
            10**18
        )  # TODO: change to softcode

        hypervisor["baseTokensOwed0"] = int(hypervisor["baseTokensOwed0"]) / (
            10**decimals_0
        )
        hypervisor["baseTokensOwed1"] = int(hypervisor["baseTokensOwed1"]) / (
            10**decimals_1
        )
        hypervisor["limitTokensOwed0"] = int(hypervisor["limitTokensOwed0"]) / (
            10**decimals_0
        )
        hypervisor["limitTokensOwed1"] = int(hypervisor["limitTokensOwed1"]) / (
            10**decimals_1
        )

        return hypervisor

    def _calc_USD_prices(self, hypervisor: dict) -> tuple:
        """use conversion subgraph field to retrieve USD token prices

         Args:
           conversion (dict):  {   baseTokenIndex
                                   priceTokenInBase
                                   priceBaseInUSD
                               }

         Returns:
           tuple: token0 usd price ,token1 usd price
         """

        decimals_0 = int(hypervisor["pool"]["token0"]["decimals"])
        decimals_1 = int(hypervisor["pool"]["token1"]["decimals"])

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

        return token0_price * (10**decimals_0), token1_price * (10**decimals_1)
