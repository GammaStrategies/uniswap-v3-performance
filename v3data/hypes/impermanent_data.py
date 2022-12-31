
import asyncio
from datetime import timedelta

from v3data import GammaClient, LlamaClient, UniswapV3Client
from v3data.hypes.fees import Fees

from v3data.utils import timestamp_ago
from v3data.constants import BLOCK_TIME_SECONDS
from v3data.hypes.fees_yield_data import YieldData




class ImpermanentData(YieldData):

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
        self, block, pool_address, base_lower, base_upper, limit_lower, limit_upper):
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


    async def get_data(self):
        
        # define blocks to gather info from
        initial_timestamp = timestamp_ago(timedelta(days=self.period_days))
        current_timestamp = timestamp_ago(timedelta(minutes=5))
        initial_block, current_block = await asyncio.gather(
            self.llama_client.block_from_timestamp(initial_timestamp),
            self.llama_client.block_from_timestamp(current_timestamp),
        )

        # get hypervisors data
        hypervisor_dta = await asyncio.gather(*[self._get_hypervisor_data_at_block(block) for block in [initial_block, current_block]])
        
        # get pool data   
        pool_data = [await asyncio.gather(*[
                self._get_pool_data_at_block(
                    initial_block if block_index == 0 else current_block,
                    hypervisor_dta[block_index]["data"]["uniswapV3Hypervisors"][hyper_index]["pool"]["id"],
                    hypervisor_dta[block_index]["data"]["uniswapV3Hypervisors"][hyper_index]["baseLower"],
                    hypervisor_dta[block_index]["data"]["uniswapV3Hypervisors"][hyper_index]["baseUpper"],
                    hypervisor_dta[block_index]["data"]["uniswapV3Hypervisors"][hyper_index]["limitLower"],
                    hypervisor_dta[block_index]["data"]["uniswapV3Hypervisors"][hyper_index]["limitUpper"],
                )
                for hyper_index in range(len(hypervisor_dta[block_index]["data"]["uniswapV3Hypervisors"]))
            ]) for block_index in range(len(hypervisor_dta))
            ]

        # prepare n fill data structure
        data_by_hypervisor = {} 
            #  { <hypervisor id> : [ <initial data>, <current data> ]
            #                        <data> includes "self._get_hypervisor_data_at_block()", "block" and "token0_usd_price" , "token1_usd_price" fields
                    
        for block_index in range(len(hypervisor_dta)):
            for hyper_index in range(len(hypervisor_dta[block_index]["data"]["uniswapV3Hypervisors"])):
                
                # create ease to access vars
                hypdta = hypervisor_dta[block_index]["data"]["uniswapV3Hypervisors"][hyper_index]
                pooldta = pool_data[block_index][hyper_index]

                # if not hypdta["pool"]["id"] == pooldta["pool"]["id"]:
                #     # should not be here ERR
                #     stop_here = ""

                # add to structure
                if not hypdta["id"] in data_by_hypervisor:
                    data_by_hypervisor[hypdta["id"]] = [dict(),dict()] # init block , end block data 
            
                # convert types
                hypdta = self._convert_dataTypes(hypdta)
                
                # add block and timestamp to hypervisor
                hypdta["block"] = initial_block if block_index == 0 else current_block
                hypdta["timestamp"] = initial_timestamp if block_index == 0 else current_timestamp

                # add usd prices
                hypdta["token0_usd_price"],hypdta["token1_usd_price"] = self._calc_USD_prices(hypervisor=hypdta)

                
                # get uncollected base fees
                decimals_0 = int(hypdta["pool"]["token0"]["decimals"])
                decimals_1 = int(hypdta["pool"]["token1"]["decimals"])

                try:
                    base_fees_0, base_fees_1 = Fees.calc_fees(
                        fee_growth_global_0=int(pooldta["pool"]["feeGrowthGlobal0X128"]),
                        fee_growth_global_1=int(pooldta["pool"]["feeGrowthGlobal1X128"]),
                        tick_current=int(pooldta["pool"]["tick"]),
                        tick_lower=int(hypdta["baseLower"]),
                        tick_upper=int(hypdta["baseUpper"]),
                        fee_growth_outside_0_lower=int(pooldta["baseLower"][0]["feeGrowthOutside0X128"]),
                        fee_growth_outside_1_lower=int(pooldta["baseLower"][0]["feeGrowthOutside1X128"]),
                        fee_growth_outside_0_upper=int(pooldta["baseUpper"][0]["feeGrowthOutside0X128"]),
                        fee_growth_outside_1_upper=int(pooldta["baseUpper"][0]["feeGrowthOutside1X128"]),
                        liquidity=int(hypdta["baseLiquidity"]),
                        fee_growth_inside_last_0=int(hypdta["baseFeeGrowthInside0LastX128"]),
                        fee_growth_inside_last_1=int(hypdta["baseFeeGrowthInside1LastX128"]),
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
                        fee_growth_global_0=int(pooldta["pool"]["feeGrowthGlobal0X128"]),
                        fee_growth_global_1=int(pooldta["pool"]["feeGrowthGlobal1X128"]),
                        tick_current=int(pooldta["pool"]["tick"]),
                        tick_lower=int(hypdta["limitLower"]),
                        tick_upper=int(hypdta["limitUpper"]),
                        fee_growth_outside_0_lower=int(pooldta["limitLower"][0]["feeGrowthOutside0X128"]),
                        fee_growth_outside_1_lower=int(pooldta["limitLower"][0]["feeGrowthOutside1X128"]),
                        fee_growth_outside_0_upper=int(pooldta["limitUpper"][0]["feeGrowthOutside0X128"]),
                        fee_growth_outside_1_upper=int(pooldta["limitUpper"][0]["feeGrowthOutside1X128"]),
                        liquidity=int(hypdta["limitLiquidity"]),
                        fee_growth_inside_last_0=int(hypdta["limitFeeGrowthInside0LastX128"]),
                        fee_growth_inside_last_1=int(hypdta["limitFeeGrowthInside1LastX128"]),
                    )
                    # convert
                    limit_fees_0 /= 10**decimals_0
                    limit_fees_1 /= 10**decimals_1

                except:
                    limit_fees_0 = 0
                    limit_fees_1 = 0

                # set uncollected fees field
                hypdta["uncollected_fees0"] = base_fees_0+limit_fees_0+hypdta["baseTokensOwed0"]+hypdta["limitTokensOwed0"]
                hypdta["uncollected_fees1"] = base_fees_1+limit_fees_1+hypdta["baseTokensOwed1"]+hypdta["limitTokensOwed1"]


                # add to structure
                data_by_hypervisor[hypdta["id"]][block_index] = hypdta



        # build result
        all_data = {}
        for hypervisor_id, struct in data_by_hypervisor.items():

            if len(struct[0].keys())==0:
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
                ini_HODL_USD = (initial_tvl0*struct[0]["token0_usd_price"] + initial_tvl1*struct[0]["token1_usd_price"])/struct[0]["totalSupply"] 
                cur_HODL_USD = (current_tvl0*struct[1]["token0_usd_price"] + current_tvl1*struct[1]["token1_usd_price"])/struct[1]["totalSupply"]
                vs_HODL_USD = ((cur_HODL_USD-ini_HODL_USD)/ini_HODL_USD) if ini_HODL_USD != 0 else 0

                # hodl deposited tokens proportion ( use curr prices with initial qtties)
                ini_HODL_deposited = (initial_tvl0*struct[1]["token0_usd_price"] + initial_tvl1*struct[1]["token1_usd_price"])/struct[1]["totalSupply"]
                cur_HODL_deposited = cur_HODL_USD
                vs_HODL_deposited = ((cur_HODL_deposited-ini_HODL_deposited)/ini_HODL_deposited) if ini_HODL_deposited != 0 else 0 

                # hodl token0
                ini_HODL_token0 = (initial_tvl0 + (initial_tvl1*(struct[0]["token1_usd_price"]/struct[0]["token0_usd_price"])))/struct[0]["totalSupply"]
                cur_HODL_token0 = (current_tvl0 + (current_tvl1*(struct[1]["token1_usd_price"]/struct[1]["token0_usd_price"])))/struct[1]["totalSupply"]
                vs_HODL_token0 = ((cur_HODL_token0-ini_HODL_token0)/ini_HODL_token0) if ini_HODL_token0 != 0 else 0

                # hodl token1
                ini_HODL_token1 = (initial_tvl1 + (initial_tvl0*(struct[0]["token0_usd_price"]/struct[0]["token1_usd_price"])))/struct[0]["totalSupply"]
                cur_HODL_token1 = (current_tvl1 + (current_tvl0*(struct[1]["token0_usd_price"]/struct[1]["token1_usd_price"])))/struct[1]["totalSupply"]
                vs_HODL_token1 = ((cur_HODL_token1-ini_HODL_token1)/ini_HODL_token1) if ini_HODL_token1 != 0 else 0

            else:
                vs_HODL_USD = vs_HODL_deposited = vs_HODL_token0 = vs_HODL_token1 = 0

            # add to result
            all_data[hypervisor_id] = {

                "id":hypervisor_id, # test field TODO: remove
                "symbol_0":struct[0]["symbol"], # test field TODO: remove

                "blocks_passed":blocks_passed,
                "seconds_passed":seconds_passed,

                "vs_HODL_USD":vs_HODL_USD,
                "vs_HODL_deposited":vs_HODL_deposited,
                "vs_HODL_token0":vs_HODL_token0,
                "vs_HODL_token1":vs_HODL_token1,

                # test fields TODO: remove
                "ini_supply":struct[0]["totalSupply"],
                "ini_tvl0":struct[0]["tvl0"],
                "ini_tvl1":struct[0]["tvl1"],
                "ini_tvlUSD":struct[0]["tvlUSD"],
                "ini_uncollected_fees0":struct[0]["uncollected_fees0"],
                "ini_uncollected_fees1":struct[0]["uncollected_fees1"],
                "ini_token0_usd_price":struct[0]["token0_usd_price"],
                "ini_token1_usd_price":struct[0]["token1_usd_price"],
                
                "end_supply":struct[1]["totalSupply"],
                "end_tvl0":struct[1]["tvl0"],
                "end_tvl1":struct[1]["tvl1"],
                "end_tvlUSD":struct[1]["tvlUSD"],
                "end_uncollected_fees0":struct[1]["uncollected_fees0"],
                "end_uncollected_fees1":struct[1]["uncollected_fees1"],
                "end_token0_usd_price":struct[1]["token0_usd_price"],
                "end_token1_usd_price":struct[1]["token1_usd_price"],

                "symbol_1":struct[1]["symbol"],

                }


        self.data = {
            "initial_block": initial_block,
            "current_block": current_block,
            "hype_data": all_data,
        }



   # HELPERs
    def _convert_dataTypes(self, hypervisor:dict)->dict:
        # convert data
        decimals_0 = int(hypervisor["pool"]["token0"]["decimals"])
        decimals_1 = int(hypervisor["pool"]["token1"]["decimals"])

        # TODO: convert conversion fields

        hypervisor["tvl0"] = int(hypervisor["tvl0"])/(10**decimals_0)
        hypervisor["tvl1"] = int(hypervisor["tvl1"])/(10**decimals_1)
        hypervisor["tvlUSD"] = float(hypervisor["tvlUSD"])
        hypervisor["totalSupply"] = int(hypervisor["totalSupply"])/(10**18) #TODO: change to softcode

        hypervisor["baseTokensOwed0"] = int(hypervisor["baseTokensOwed0"])/(10**decimals_0)
        hypervisor["baseTokensOwed1"] = int(hypervisor["baseTokensOwed1"])/(10**decimals_1)
        hypervisor["limitTokensOwed0"] = int(hypervisor["limitTokensOwed0"])/(10**decimals_0)
        hypervisor["limitTokensOwed1"] = int(hypervisor["limitTokensOwed1"])/(10**decimals_1)

    
        return hypervisor

    def _calc_USD_prices(self, hypervisor:dict)->tuple:
        """ use conversion subgraph field to retrieve USD token prices

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
        
        return token0_price*(10**decimals_0),token1_price*(10**decimals_1)



