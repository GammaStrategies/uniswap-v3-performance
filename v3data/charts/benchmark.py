import datetime as dt
import numpy as np
import pandas as pd

from v3data import GammaClient, UniswapV2Client, UniswapV3Client
from v3data.utils import date_to_timestamp
from v3data.constants import WETH_ADDRESS
from v3data.charts.config import BASE_POOLS_CONFIG, WETH_USDC_POOL


class Benchmark:
    def __init__(self, protocol: str, chain: str, address, start_date, end_date):
        self.chain = chain
        self.gamma_client = GammaClient(protocol, chain)
        self.v3_client = UniswapV3Client(protocol, chain)
        self.v2_client = UniswapV2Client()
        self.address = address
        self._init_dates(start_date, end_date)
        self.weth_token = None
        self.base_token_index = None

    def _init_dates(self, start_date, end_date):
        THIRTY_DAYS = dt.timedelta(days=30)
        current_date = dt.date.today()

        if start_date:
            if (not end_date) or (end_date < start_date):
                # start date provided but no end date
                end_date = start_date + THIRTY_DAYS
        else:
            if end_date:
                # end date provided but no start date
                start_date = end_date - THIRTY_DAYS
            else:
                # missing start date and end date
                start_date = current_date - THIRTY_DAYS
                end_date = current_date

        self.start_timestamp = date_to_timestamp(start_date)
        self.end_timestamp = date_to_timestamp(end_date)

    async def _get_hypervisor_data(self):
        query_hypervisor = """
        query hypervisorPricng($id: String!, $startDate: Int!, $endDate: Int!){
            uniswapV3Hypervisor(id: $id) {
                id
                pool {
                    id
                    token0{
                        id
                        symbol
                    }
                    token1{
                        id
                        symbol
                    }
                }
                dayData(
                    where:{
                        date_gte: $startDate
                        date_lt: $endDate
                        close_gt: 0
                    }
                ){
                    date
                    close
                }
            }
        }
        """
        variables_hypervisor = {
            "id": self.address,
            "startDate": self.start_timestamp,
            "endDate": self.end_timestamp,
        }

        hypervisor_response = await self.gamma_client.query(
            query_hypervisor, variables_hypervisor
        )
        return hypervisor_response["data"]["uniswapV3Hypervisor"]

    async def _get_v3_data(self, lp_pool):
        query = """
        query v3pricing(
            $lpPool: String!,
            $basePool: String!,
            $ethPool: String!,
            $startDate: Int!,
            $endDate: Int!,
        ){
            lpDayData: poolDayDatas(
                where: {
                    pool: $lpPool
                    date_gte: $startDate
                    date_lt: $endDate
                }
            ){
                date
                token0Price
                token1Price
            }
            baseDayData: poolDayDatas(
                where: {
                    pool: $basePool
                    date_gte: $startDate
                    date_lt: $endDate
                }
            ){
                date
                token0Price
                token1Price
            }
            ethDayData: poolDayDatas(
                where: {
                    pool: $ethPool
                    date_gte: $startDate
                    date_lt: $endDate
                }
            ){
                date
                ethPriceUsdc: token0Price
            }
        }
        """

        variables = {
            "lpPool": lp_pool,
            "basePool": self.base_pool["v3"]["pool"],
            "ethPool": WETH_USDC_POOL[self.chain],
            "startDate": self.start_timestamp,
            "endDate": self.end_timestamp,
        }
        response = await self.v3_client.query(query, variables)
        return response["data"]

    async def _get_v2_data(self, token0, token1):
        # Get V2 data

        query_v2 = """
        query v2LpPricing(
            $token0: String!,
            $token1: String!,
            $startDate: Int!,
            $endDate: Int!,
            $v2Pair: String!
        ){
            lpDayData: pairDayDatas(
                where: {
                    token0: $token0,
                    token1: $token1,
                    date_gte: $startDate,
                    date_lt: $endDate
                }
            ){
                date
                totalSupply
                reserve0
                reserve1
                reserveUSD
            }
            ethDayData: pairDayDatas(
                where: {
                    pairAddress: "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc"
                    date_gte: $startDate,
                    date_lt: $endDate
                }
            ){
                date
                reserve0
                reserve1
            }
            baseDayData: pairDayDatas(
                where: {
                    pairAddress: $v2Pair,
                    date_gte: $startDate,
                    date_lt: $endDate
                }
            ){
                date
                reserve0
                reserve1
            }
        }
        """

        variables_v2 = {
            "token0": token0,
            "token1": token1,
            "startDate": self.start_timestamp,
            "endDate": self.end_timestamp,
            "v2Pair": self.base_pool["v2"]["pool"],
        }
        v2_response = await self.v2_client.query(query_v2, variables_v2)
        return v2_response["data"]

    async def get_data(self, v2=False):
        # Get hypervisor position
        hypervisor_data = await self._get_hypervisor_data()

        if not hypervisor_data:
            return None

        if not hypervisor_data["dayData"]:
            return None

        lp_pool = hypervisor_data["pool"]["id"]
        token0 = hypervisor_data["pool"]["token0"]["id"]
        token1 = hypervisor_data["pool"]["token1"]["id"]

        self.weth_token = 0 if token0 == WETH_ADDRESS else 1

        # Determine base token
        base_pool0 = BASE_POOLS_CONFIG[self.chain].get(token0, {})
        base_pool1 = BASE_POOLS_CONFIG[self.chain].get(token1, {})

        token0_priority = base_pool0.get("priority", 0)
        token1_priority = base_pool1.get("priority", 0)

        if token0_priority > token1_priority:
            self.base_token_index = 0
            self.base_pool = base_pool0
        elif token1_priority > token0_priority:
            self.base_token_index = 1
            self.base_pool = base_pool1
        else:
            self.base_token_index = None

        # Get token prices from v3 pool
        v3_data = await self._get_v3_data(lp_pool)

        # Get v2 data if needed
        v2_data = {}
        if v2:
            v2_data = await self._get_v2_data(token0, token1)

        return {
            "token0_symbol": hypervisor_data["pool"]["token0"]["symbol"],
            "token1_symbol": hypervisor_data["pool"]["token1"]["symbol"],
            "hypervisor": hypervisor_data["dayData"],
            "v2": v2_data,
            "v3": v3_data,
        }

    async def chart(self, v2=False):
        data = await self.get_data()

        if not data:
            return []

        # Load Hypervisor pricing
        df_hypervisor = pd.DataFrame(data["hypervisor"], dtype=np.float64).set_index(
            "date"
        )

        if v2:
            # Load V2 pricing
            df_lp = pd.DataFrame(data["v2"]["lpDayData"], dtype=np.float64).set_index(
                "date"
            )
            df_lp["v2lpPrice"] = df_lp.reserveUSD / df_lp.totalSupply

        #. Dataframe for token prices
        df_lp = pd.DataFrame(data["v3"]["lpDayData"], dtype=np.float64).set_index("date")

        if self.base_token_index == 0:
            df_lp["tokenPriceInBase"] = df_lp.token0Price
        elif self.base_token_index == 1:
            df_lp["tokenPriceInBase"] = df_lp.token1Price


        # Load Base token pricing
        df_base = pd.DataFrame(data["v3"]["baseDayData"], dtype=np.float64).set_index(
            "date"
        )
        df_eth = pd.DataFrame(data["v3"]["ethDayData"], dtype=np.float64).set_index(
            "date"
        )
        df_base = df_base.join(df_eth)
        if self.base_pool["v3"]["usdc_token_index"] == 0:
            df_base["basePriceUsdc"] = df_base.token0Price
        elif self.base_pool["v3"]["usdc_token_index"] == 1:
            df_base["basePriceUsdc"] = df_base.token1Price
        elif self.base_pool["v3"]["usdc_token_index"] == 2:
            df_base["basePriceUsdc"] = df_base.token0Price * df_base.ethPriceUsdc
        elif self.base_pool["v3"]["usdc_token_index"] == 3:
            df_base["basePriceUsdc"] = df_base.token1Price * df_base.ethPriceUsdc
        else:
            df_base["basePriceUsdc"] = 1

        df_all = df_hypervisor.join(
            [df_lp[["tokenPriceInBase"]], df_base[["basePriceUsdc"]]]
        )

        #. Convert prices to USDC
        df_all["tokenPriceUsdc"] = df_all.tokenPriceInBase * df_all.basePriceUsdc

        df_all = df_all[["close", "tokenPriceUsdc", "basePriceUsdc"]]
        df_all = df_all.div(df_all.iloc[0])  # Normalise to first value

        if df_all.iloc[-1]["tokenPriceUsdc"] >= df_all.iloc[-1]["basePriceUsdc"]:
            df_all = df_all.drop(columns="tokenPriceUsdc")
            df_all = df_all.rename(
                columns={
                    "close": "Hypervisor",
                    "basePriceUsdc": data["token1_symbol"]
                    if self.base_token_index == 1
                    else data["token0_symbol"]
                }
            )
        else:
            df_all = df_all.drop(columns="basePriceUsdc")
            df_all = df_all.rename(
                columns={
                    "close": "Hypervisor",
                    "tokenPriceUsdc": data["token0_symbol"]
                    if self.base_token_index == 1
                    else data["token1_symbol"]
                }
            )

        df_all = pd.melt(df_all.reset_index(), ["date"], var_name="group")
        df_all["date"] = pd.to_datetime(df_all.date, unit="s").dt.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        return df_all.to_dict("records")
