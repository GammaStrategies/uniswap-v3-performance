from v3data import GammaClient
from v3data.constants import XGAMMA_ADDRESS


class AccountData:
    def __init__(self, visor_address):
        self.gamma_client = GammaClient()
        self.address = visor_address.lower()
        self.reward_hypervisor_address = XGAMMA_ADDRESS
        self.decimal_factor = 10 ** 18

    def _get_data(self):
        query = """
        query accountData($accountAddress: String!, $rewardHypervisorAddress: String!) {
            account(
                id: $accountAddress
            ){
                parent { id }
                gammaDeposited
                gammaEarnedRealized
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
                rewardHypervisorShares{
                    rewardHypervisor { id }
                    shares
                }
            }
            rewardHypervisor(
                id: $rewardHypervisorAddress
            ){
                totalGamma
                totalSupply
            }
        }
        """
        variables = {
            "accounAddress": self.address,
            "rewardHypervisorAddress": self.reward_hypervisor_address
        }
        self.data = self.gamma_client.query(query, variables)['data']


class AccountInfo(AccountData):
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

        if not self.data['account']:
            return {}

        reward_hypervisor_shares = self.data['visor']['rewardHypervisorShares']
        xgamma_shares = 0
        for shares in reward_hypervisor_shares:
            if shares.get('rewardHypervisor', {}).get('id') == self.reward_hypervisor_address:
                xgamma_shares = int(shares['shares'])
                
        totalGammaStaked = int(self.data['rewardHypervisor']['totalGamma'])
        xgamma_virtual_price = totalGammaStaked / int(self.data['rewardHypervisor']['totalSupply'])

        account_owner = self.data['account']['parent']['id']
        gammaStaked = xgamma_shares * xgamma_virtual_price
        gammaDeposited = int(self.data['account']['gammaDeposited'])
        gammaEarnedRealized = int(self.data['account']['gammaEarnedRealized'])
        visor_info = {
            "owner": account_owner,
            "visrStaked": gammaStaked / self.decimal_factor,
            "visrDeposited": gammaDeposited / self.decimal_factor,
            "totalVisrEarned": (gammaStaked - gammaDeposited + gammaEarnedRealized) / self.decimal_factor,
            "visrStakedShare": f"{gammaStaked / totalGammaStaked:.2%}"
        }

        returns = self._returns()

        for hypervisor in self.data['account']['hypervisorShares']:
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
