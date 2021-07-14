from v3data import VisorClient, PricingClient


class VisorVault:
    def __init__(self, visor_address):
        self.visor_client = VisorClient()
        self.pricing_client = PricingClient()
        self.address = visor_address.lower()

    def info(self):
        query_visor = """
        query visorData($visorAddress: String!) {
            visor(
                id: $visorAddress
            ){
                owner {
                    id
                }
                hypervisorShares {
                    hypervisor {
                        id
                    }
                    shares
                }
            }
        }
        """
        variables = {"visorAddress": self.address}
        data = self.visor_client.query(query_visor, variables)['data']['visor']

        if not data:
            return {}

        visor_owner = data['owner']['id']
        tvl = self.pricing_client.hypervisors_tvl()

        hypervisor_shares = {}
        for record in data['hypervisorShares']:
            hypervisor_id = record['hypervisor']['id']
            shares = int(record['shares'])
            totalSupply = int(tvl[hypervisor_id]['totalSupply'])
            shareOfSupply = shares / totalSupply if totalSupply > 0 else 0
            hypervisor_shares[hypervisor_id] = {
                "owner": visor_owner,
                "shares": shares,
                "shareOfSupply": shareOfSupply,
                "balance0": tvl[hypervisor_id]['tvl0Decimal'] * shareOfSupply,
                "balance1": tvl[hypervisor_id]['tvl1Decimal'] * shareOfSupply,
                "balanceUSD": float(tvl[hypervisor_id]['tvlUSD']) * shareOfSupply
            }

        return hypervisor_shares
