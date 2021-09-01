from v3data import VisorClient


class VisorVaultData:
    def __init__(self, visor_address):
        self.visor_client = VisorClient()
        self.address = visor_address.lower()
        self.decimal_factor = 10 ** 18

    def _get_data(self):
        query = """
        query visorData($visorAddress: String!) {
            visrToken(id: "0xf938424f7210f31df2aee3011291b658f872e91e"){
                totalStaked
            }
            visor(
                id: $visorAddress
            ){
                owner { id }
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
        """
        variables = {"visorAddress": self.address}
        self.data = self.visor_client.query(query, variables)['data']


class VisorVaultInfo(VisorVaultData):
    def _returns(self):

        returns = {}
        for share in self.data['visor']['hypervisorShares']:
            hypervisor_address = share['hypervisor']['id']
            initial_token0 = int(share['initialToken0'])
            initial_token1 = int(share['initialToken1'])
            initial_USD = float(share['initialUSD'])
            shareOfPool = int(share['shares']) / int(share['hypervisor']['totalSupply'])
            tvl_USD = float(share['hypervisor']['tvlUSD'])

            conversion = share['hypervisor']['conversion']

            base_token_index = int(conversion['baseTokenIndex'])
            price_token_in_base = float(conversion['priceTokenInBase'])
            price_base_in_usd = float(conversion['priceBaseInUSD'])

            if base_token_index == 0:
                token = initial_token1
                base = initial_token0
            elif base_token_index == 1:
                token = initial_token0
                base = initial_token1

            initial_token_current_USD = (token * price_token_in_base * price_base_in_usd) + (base * price_base_in_usd)
            current_USD = shareOfPool * tvl_USD

            returns[hypervisor_address] = {
                'initialTokenUSD': initial_USD,
                'initialTokenCurrentUSD': initial_token_current_USD,
                'currentUSD': current_USD,
                'netMarketReturns': current_USD - initial_USD,
                'netMarketReturnsPercentage': f"{1 - (initial_USD / current_USD):.2%}",
                'hypervisorReturns': current_USD - initial_token_current_USD,
                'hypervisorReturnsPercentage': f"{1 - (initial_token_current_USD / current_USD):.2%}"
            }

        return returns

    def output(self, get_data=True):

        if get_data:
            self._get_data()

        if not self.data['visor']:
            return {}

        visor_owner = self.data['visor']['owner']['id']
        visrStaked = int(self.data['visor']['visrStaked'])
        visrDeposited = int(self.data['visor']['visrDeposited'])
        visrEarnedRealized = int(self.data['visor']['visrEarnedRealized'])
        visor_info = {
            "owner": visor_owner,
            "visrStaked": visrStaked / self.decimal_factor,
            "visrDeposited": visrDeposited / self.decimal_factor,
            "totalVisrEarned": (visrStaked - visrDeposited + visrEarnedRealized) / self.decimal_factor,
            "visrStakedShare": f"{visrStaked / int(self.data['visrToken']['totalStaked']):.2%}"
        }

        returns = self._returns()

        for hypervisor in self.data['visor']['hypervisorShares']:
            hypervisor_id = hypervisor['hypervisor']['id']
            shares = int(hypervisor['shares'])
            totalSupply = int(hypervisor['hypervisor']['totalSupply'])
            shareOfSupply = shares / totalSupply if totalSupply > 0 else 0
            tvlUSD = float(hypervisor['hypervisor']['tvlUSD'])
            decimal0 = int(hypervisor['hypervisor']['pool']['token0']['decimals'])
            decimal1 = int(hypervisor['hypervisor']['pool']['token1']['decimals'])
            tvl0_decimal = float(hypervisor['hypervisor']['tvl0']) / 10 ** decimal0
            tvl1_decimal = float(hypervisor['hypervisor']['tvl1']) / 10 ** decimal1

            visor_info[hypervisor_id] = {
                "shares": shares,
                "shareOfSupply": shareOfSupply,
                "balance0": tvl0_decimal * shareOfSupply,
                "balance1": tvl1_decimal * shareOfSupply,
                "balanceUSD": tvlUSD * shareOfSupply,
                "returns": returns[hypervisor_id]
            }

        return visor_info
