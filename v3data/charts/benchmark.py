import numpy as np
import pandas as pd

from v3data import VisorClient, UniswapV2Client
from v3data.utils import year_month_day_to_timestamp
from v3data.constants import WETH_ADDRESS

V2_BASE_POOLS = {
    # WBTC
    "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": {
        "pool": "0x004375dff511095cc5a197a54140a24efef3a416",
        "usdc_token_index": 1,
        "priority": 1

    },
    # WETH
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": {
        "pool": "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc",
        "usdc_token_index": 0,
        "priority": 2
    },
    # DAI
    "0x6b175474e89094c44da98b954eedeac495271d0f": {
        "pool": "0xae461ca67b15dc8dc81ce7615e0320da1a9ab8d5",
        "usdc_token_index": 1,
        "priority": 3
    },
    # USDT
    "0xdac17f958d2ee523a2206206994597c13d831ec7": {
        "pool": "0x3041cbd36888becc7bbcbc0045e3b1f144466f5f",
        "usdc_token_index": 0,
        "priority": 4
    },
    # USDC
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {
        "pool": "0x3041cbd36888becc7bbcbc0045e3b1f144466f5f",  # Use a dummy pool
        "usdc_token_index": None,
        "priority": 5
    }
}


class Benchmark:
    def __init__(self, address, start_year, start_month, start_day=1, n_months=1):
        self.visor_client = VisorClient()
        self.v2_client = UniswapV2Client()
        self.address = address
        self._init_dates(start_year, start_month, start_day, n_months)
        self.weth_token = None
        self.base_token_index = None

    def _init_dates(self, start_year, start_month, start_day, n_months):
        additional_years, end_month = divmod(start_month + n_months, 12)
        end_year = start_year + additional_years
        self.start_date = year_month_day_to_timestamp(start_year, start_month, start_day)
        self.end_date = year_month_day_to_timestamp(end_year, end_month, 30)

    def get_data(self):
        # Get hypervisor position
        query_hypervisor = """
        query hypervisorPricng($id: String!, $startDate: Int!, $endDate: Int!){
            uniswapV3Hypervisor(id: $id) {
                id
                pool {
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
            "startDate": self.start_date,
            "endDate": self.end_date
        }

        hypervisor_data = self.visor_client.query(
            query_hypervisor, variables_hypervisor)['data']['uniswapV3Hypervisor']

        if not hypervisor_data['dayData']:
            return None

        token0 = hypervisor_data['pool']['token0']['id']
        token1 = hypervisor_data['pool']['token1']['id']

        self.weth_token = 0 if token0 == WETH_ADDRESS else 1

        # Determine base token
        base_pool0 = V2_BASE_POOLS.get(token0, {})
        base_pool1 = V2_BASE_POOLS.get(token1, {})

        token0_priority = base_pool0.get('priority', 0)
        token1_priority = base_pool1.get('priority', 0)

        if token0_priority > token1_priority:
            self.base_token_index = 0
            self.base_pool = base_pool0
        elif token1_priority > token0_priority:
            self.base_token_index = 1
            self.base_pool = base_pool1
        else:
            self.base_token_index = None

        hypervisor_daily = hypervisor_data['dayData']

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
            "startDate": self.start_date,
            "endDate": self.end_date,
            "v2Pair": self.base_pool['pool']
        }
        v2_data = self.v2_client.query(query_v2, variables_v2)['data']

        return {
            "token0_symbol": hypervisor_data['pool']['token0']['symbol'],
            "token1_symbol": hypervisor_data['pool']['token1']['symbol'],
            "hypervisor": hypervisor_daily,
            "v2": v2_data
        }

    def chart(self):
        data = self.get_data()

        if not data:
            return []

        # Load Hypervisor pricing
        df_hypervisor = pd.DataFrame(data['hypervisor'], dtype=np.float64).set_index('date')

        # Load V2 pricing
        df_lp = pd.DataFrame(data['v2']['lpDayData'], dtype=np.float64).set_index('date')
        df_lp['v2lpPrice'] = df_lp.reserveUSD / df_lp.totalSupply

        # if self.weth_token == 0:
        #     df_lp['tokenPriceEth'] = df_lp.reserve0 / df_lp.reserve1
        # elif self.weth_token == 1:
        #     df_lp['tokenPriceEth'] = df_lp.reserve1 / df_lp.reserve0

        if self.base_token_index == 0:
            df_lp['tokenPriceInBase'] = df_lp.reserve0 / df_lp.reserve1
        elif self.base_token_index == 1:
            df_lp['tokenPriceInBase'] = df_lp.reserve1 / df_lp.reserve0

        # # Load ETH pricing
        # df_eth = pd.DataFrame(data['v2']['ethDayData'], dtype=np.float64).set_index('date')
        # df_eth['ethPriceUsdc'] = df_eth.reserve0 / df_eth.reserve1

        # Load Base token pricing
        df_base = pd.DataFrame(data['v2']['baseDayData'], dtype=np.float64).set_index('date')
        if self.base_pool['usdc_token_index'] == 0:
            df_base['basePriceUsdc'] = df_base.reserve0 / df_base.reserve1
        elif self.base_pool['usdc_token_index'] == 1:
            df_base['basePriceUsdc'] = df_base.reserve1 / df_base.reserve0
        else:
            df_base['basePriceUsdc'] = df_base.reserve0 / df_base.reserve0

        df_all = df_hypervisor.join([
            df_lp[['v2lpPrice', 'tokenPriceInBase']],
            df_base[['basePriceUsdc']]
        ])

        df_all['tokenPriceUsdc'] = df_all.tokenPriceInBase * df_all.basePriceUsdc

        df_all = df_all[['close', 'v2lpPrice', 'tokenPriceUsdc', 'basePriceUsdc']]
        df_all = df_all.div(df_all.iloc[0])  # Normalise to first value
        df_all = df_all.rename(columns={
            'close': 'Hypervisor',
            'v2lpPrice': 'Uniswap V2 LP',
            'tokenPriceUsdc': data["token0_symbol"] if self.base_token_index == 1 else data["token1_symbol"],
            'basePriceUsdc': data["token1_symbol"] if self.base_token_index == 1 else data["token0_symbol"]
        })
        df_all = pd.melt(df_all.reset_index(), ['date'], var_name='group')
        df_all['date'] = pd.to_datetime(df_all.date, unit='s').dt.strftime('%Y-%m-%dT%H:%M:%SZ')

        return df_all.to_dict("records")
