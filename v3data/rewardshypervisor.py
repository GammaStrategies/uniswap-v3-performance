from v3data import XgammaClient

class RewardsHypervisorData:
    def __init__(self):
        self.client = XgammaClient()
        self.decimal_factor = 10 ** 18
        self.data = {}

    def _get_data(self):

        query = """
        {
            xgamma(
                id:"xgamma"
            ) {
                gammaStaked
                totalSupply
            }
        }
        """

        self.data = self.client.query(query)['data']

class RewardsHypervisorCalculations(RewardsHypervisorData):
    def basic_info(self, get_data=True):
        if get_data:
            self._get_data()
        data = self.data['xgamma']

        gamma_staked = int(data['gammaStaked']) / self.decimal_factor
        xgamma_total = int(data['totalSupply']) / self.decimal_factor
        gamma_per_xgamma = gamma_staked / xgamma_total

        return {
            "gamma_staked": gamma_staked,
            "xgamma_total": xgamma_total,
            "gamma_per_xgamma": gamma_per_xgamma
        }

class RewardsHypervisorInfo(RewardsHypervisorCalculations):
    def output(self, get_data=True):
        return self.basic_info(get_data=get_data)
        