import pandas as pd
import numpy as np
from v3data import VisorClient


class DailyChart:
    def __init__(self, days=20):
        self.days = days
        self.visor_client = VisorClient()

    def _get_all_flows(self):
        """Daily chart flows bar chart for hypervisors"""
        query = """
        query hypervisorDaily($days: Int!){
            uniswapV3Hypervisors(
                first: 1000
            ){
                id
                dayData(
                    first: $days
                    orderBy: date
                    orderDirection: desc
                ){
                    date
                    depositedUSD
                    withdrawnUSD
                    protocolFeesCollectedUSD
                    feesReinvestedUSD
                }
            }
        }
        """
        variables = {
            'days': self.days
        }
        hypervisors = self.visor_client.query(query, variables)['data']['uniswapV3Hypervisors']

        data = [day_data for hypervisor in hypervisors for day_data in hypervisor['dayData']]

        return data

    def _get_hypervisor_flows(self, hypervisor_address):
        """Daily chart flows bar chart for hypervisors"""
        query = """
        query hypervisorDaily($hypervisor: String!, $days: Int!){
            uniswapV3HypervisorDayDatas(
                where: {hypervisor: $hypervisor}
                first: $days
                orderBy: date
                orderDirection: desc
            ){
                date
                depositedUSD
                withdrawnUSD
                protocolFeesCollectedUSD
                feesReinvestedUSD
            }
        }
        """
        variables = {
            "hypervisor": hypervisor_address.lower(),
            'days': self.days
        }
        return self.visor_client.query(query, variables)['data']['uniswapV3HypervisorDayDatas']

    def asset_flows(self, hypervisor_address=None):

        if hypervisor_address:
            data = self._get_hypervisor_flows(hypervisor_address)
            df_flows = pd.DataFrame(data, dtype=np.float64)
        else:
            data = self._get_all_flows()
            df_flows = pd.DataFrame(data, dtype=np.float64)
            df_flows = df_flows.groupby('date').sum().reset_index()

        df_flows['netDepositedUSD'] = df_flows.depositedUSD - df_flows.withdrawnUSD

        df_flows.sort_values('date', inplace=True)
        df_flows['key'] = pd.to_datetime(df_flows.date, unit='s').dt.strftime('%Y-%m-%d')
        df_flows.drop(columns=['depositedUSD', 'withdrawnUSD', 'date'], inplace=True)
        df_flows.rename(columns={
            "feesReinvestedUSD": "Re-invested uniswap fees",
            "protocolFeesCollectedUSD": "Visor Fees",
            "netDepositedUSD": "Net deposits & withdraws"
        }, inplace=True)

        return df_flows.melt(id_vars='key', var_name="group").to_dict('records')

    def tvl(self):
        """Total TVL chart broken down by hypervisor"""
        query = """
        query hypervisorDaily($days: Int!){
            uniswapV3Hypervisors(
                first: 1000
            ){
                id
                pool{
                    token0{
                        symbol
                        decimals
                    }
                    token1{
                        symbol
                        decimals
                    }
                }
                dayData(
                    first: $days
                    orderBy: date
                    orderDirection: desc
                    where:{
                        tvlUSD_gt: 0
                    }
                ){
                    date
                    tvl0
                    tvl1
                    tvlUSD
                }
            }
        }
        """
        variables = {'days': self.days}
        data = self.visor_client.query(query, variables)['data']['uniswapV3Hypervisors']

        df_all = pd.DataFrame()
        for hypervisor in data:
            df_hypervisor = pd.DataFrame(hypervisor['dayData'], dtype=np.float64)
            df_hypervisor['hypervisor'] = hypervisor['id']
            df_hypervisor['name'] = f"{hypervisor['pool']['token0']['symbol']}-{hypervisor['pool']['token1']['symbol']}"
            df_all = pd.concat([df_all, df_hypervisor])

        df_all.date = pd.to_datetime(df_all.date, unit='s').dt.strftime('%Y-%m-%dT%H:%M:%SZ')

        df_all.rename(columns={
            "name": "group",
            "tvlUSD": "value"
        }, inplace=True)

        return df_all[['date', 'group', 'value']].to_dict('records')
