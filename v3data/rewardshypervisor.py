from v3data import VisorClient

class RewardsHypervisorData:
    def __init__(self):
        self.visor_client = VisorClient()
        self.address = "0xc9f27a50f82571c1c8423a42970613b8dbda14ef"
        self.decimal_factor = 10 ** 18
        self.data = {}

    def _get_data(self):

        query = """
        {
            rewardHypervisor(
                id:"0xc9f27a50f82571c1c8423a42970613b8dbda14ef"
            ) {
                totalVisr
                totalSupply
            }
        }
        """
        variables = {
            "id": self.address
        }
        self.data = self.visor_client.query(query, variables)['data']

class RewardsHypervisorCalculations(RewardsHypervisorData):
    def basic_info(self, get_data=True):
        if get_data:
            self._get_data()
        data = self.data['rewardHypervisor']

        visr_staked = int(data['totalVisr']) / self.decimal_factor
        vvisr_total = int(data['totalSupply']) / self.decimal_factor
        visr_per_vvisr = visr_staked / vvisr_total

        return {
            "visr_staked": visr_staked,
            "vvisr_total": vvisr_total,
            "visr_per_vvisr": visr_per_vvisr
        }

class RewardsHypervisorInfo(RewardsHypervisorCalculations):
    def output(self, get_data=True):
        return self.basic_info(get_data=get_data)
        