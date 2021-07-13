from v3data import VisorClient, PricingClient


class VisorUser:
    def __init__(self, user_address):
        self.visor_client = VisorClient()
        self.pricing_client = PricingClient()
        self.address = user_address

    def info(self):
        query_users = """
        query userData($userAddress: String!) {
            user(
                id: $userAddress
            ){
                visorsOwned {
                    id
                    hypervisorShares {
                        hypervisor {
                            id
                        }
                        shares
                    }
                }
            }
        }
        """
        variables = {"userAddress": self.address}
        data = self.visor_client.query(query_users, variables)['data']['user']

        if not data:
            return {}

        tvl = self.pricing_client.hypervisors_tvl()

        visors = {}
        for visor in data['visorsOwned']:
            visor_id = visor['id']
            visors[visor_id] = {}
            for hypervisor in visor['hypervisorShares']:
                hypervisor_id = hypervisor['hypervisor']['id']
                shareOfSupply = int(hypervisor['shares']) / int(tvl[hypervisor_id]['totalSupply'])

                visors[visor_id][hypervisor_id] = {
                    "shares": hypervisor['shares'],
                    "shareOfSupply": shareOfSupply,
                    "balance0": tvl[hypervisor_id]['tvl0Decimal'] * shareOfSupply,
                    "balance1": tvl[hypervisor_id]['tvl1Decimal'] * shareOfSupply,
                    "balanceUSD": float(tvl[hypervisor_id]['tvlUSD']) * shareOfSupply
                }

        return visors
