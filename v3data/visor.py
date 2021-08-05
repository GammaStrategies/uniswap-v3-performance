from v3data import VisorClient


class VisorVault:
    def __init__(self, visor_address):
        self.visor_client = VisorClient()
        self.address = visor_address.lower()
        self.decimal_factor = 10 ** 18

    def _get_data(self):
        query = """
        query visorData($visorAddress: String!) {
            visor(
                id: $visorAddress
            ){
                owner {
                    id
                }
                visrStaked
                hypervisorShares {
                    hypervisor {
                        id
                        pool{
                            token0{ decimals }
                            token1{ decimals }
                        }
                        totalSupply
                        tvl0
                        tvl1
                        tvlUSD
                    }
                    shares
                }
            }
        }
        """
        variables = {"visorAddress": self.address}
        self.data = self.visor_client.query(query, variables)['data']['visor']

    def info(self, get_data=True):

        if get_data:
            self._get_data()

        if not self.data:
            return {}

        visor_owner = self.data['owner']['id']
        visor_info = {
            "owner": visor_owner,
            "visrStaked": int(self.data['visrStaked']) / self.decimal_factor
        }
        for hypervisor in self.data['hypervisorShares']:
            hypervisor_id = hypervisor['hypervisor']['id']
            shares = int(hypervisor['shares'])
            totalSupply = int(hypervisor['hypervisor']['totalSupply'])
            shareOfSupply = shares / totalSupply if totalSupply > 0 else 0
            tvlUSD = float(hypervisor['hypervisor']['tvlUSD'])
            tvl0_decimal = float(hypervisor['hypervisor']['tvl0']) / 10 ** int(hypervisor['hypervisor']['pool']['token0']['decimals'])
            tvl1_decimal = float(hypervisor['hypervisor']['tvl1']) / 10 ** int(hypervisor['hypervisor']['pool']['token1']['decimals'])
            
            visor_info[hypervisor_id] = {
                "shares": shares,
                    "shareOfSupply": shareOfSupply,
                    "balance0": tvl0_decimal * shareOfSupply,
                    "balance1": tvl1_decimal * shareOfSupply,
                    "balanceUSD": tvlUSD * shareOfSupply
            }

        return visor_info
