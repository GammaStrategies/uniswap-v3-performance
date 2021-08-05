from v3data import VisorClient


class VisorUser:
    def __init__(self, user_address):
        self.visor_client = VisorClient()
        self.address = user_address.lower()
        self.decimal_factor = 10 ** 18
        self.data = {}

    def _get_data(self):
        query = """
        query userData($userAddress: String!) {
            user(
                id: $userAddress
            ){
                visorsOwned {
                    id
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
        }
        """
        variables = {"userAddress": self.address}
        self.data = self.visor_client.query(query, variables)['data']['user']

    def info(self, get_data=True):

        if get_data:
            self._get_data()

        if not self.data:
            return {}

        visors = {}
        for visor in self.data['visorsOwned']:
            visor_id = visor['id']
            visors[visor_id] = {
                "visrStaked": int(visor['visrStaked']) / self.decimal_factor
            }
            for hypervisor in visor['hypervisorShares']:
                hypervisor_id = hypervisor['hypervisor']['id']
                shares = int(hypervisor['shares'])
                totalSupply = int(hypervisor['hypervisor']['totalSupply'])
                shareOfSupply = shares / totalSupply if totalSupply > 0 else 0
                tvlUSD = float(hypervisor['hypervisor']['tvlUSD'])
                tvl0_decimal = float(hypervisor['hypervisor']['tvl0']) / 10 ** int(hypervisor['hypervisor']['pool']['token0']['decimals'])
                tvl1_decimal = float(hypervisor['hypervisor']['tvl1']) / 10 ** int(hypervisor['hypervisor']['pool']['token1']['decimals'])

                visors[visor_id][hypervisor_id] = {
                    "shares": shares,
                    "shareOfSupply": shareOfSupply,
                    "balance0": tvl0_decimal * shareOfSupply,
                    "balance1": tvl1_decimal * shareOfSupply,
                    "balanceUSD": tvlUSD * shareOfSupply
                }

        return visors
