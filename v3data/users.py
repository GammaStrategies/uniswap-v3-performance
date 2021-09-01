from v3data import VisorClient
from v3data.visor import VisorVaultInfo


class UserData:
    def __init__(self, user_address):
        self.visor_client = VisorClient()
        self.address = user_address.lower()
        self.decimal_factor = 10 ** 18
        self.data = {}

    def _get_data(self):
        query = """
        query userData($userAddress: String!) {
            visrToken(id: "0xf938424f7210f31df2aee3011291b658f872e91e"){
                totalStaked
            }
            user(
                id: $userAddress
            ){
                visorsOwned {
                    id
                    owner{ id }
                    visrStaked
                    visrDeposited
                    visrEarnedRealized
                    hypervisorShares {
                        hypervisor {
                            id
                            pool{
                                token0{ decimals }
                                token1{ decimals }
                            }
                            conversion {
                                baseTokenIndex
                                priceTokenInBase
                                priceBaseInUSD
                            }
                            totalSupply
                            tvl0
                            tvl1
                            tvlUSD
                        }
                        shares
                        initialToken0
                        initialToken1
                        initialUSD
                    }
                }
            }
        }
        """
        variables = {"userAddress": self.address}
        self.data = self.visor_client.query(query, variables)['data']


class UserInfo(UserData):
    def output(self, get_data=True):

        if get_data:
            self._get_data()

        if not self.data.get('user'):
            return {}

        visors = {}
        for visor in self.data['user']['visorsOwned']:
            visor_address = visor['id']
            visor_vault_info = VisorVaultInfo(visor_address)
            visor_vault_info.data = {
                'visrToken': self.data['visrToken'],
                'visor': visor,
            }
            visors[visor_address] = visor_vault_info.output(get_data=False)

        return visors
