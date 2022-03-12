from v3data import GammaClient
from v3data.accounts import AccountInfo
from v3data.constants import XGAMMA_ADDRESS


class UserData:
    def __init__(self, chain: str, user_address: str):
        self.chain = chain
        self.gamma_client = GammaClient(chain)
        self.address = user_address.lower()
        self.decimal_factor = 10**18
        self.data = {}

    async def _get_data(self):
        query = """
        query userData($userAddress: String!, $rewardHypervisorAddress: String!) {
            user(
                id: $userAddress
            ){
                accountsOwned {
                    id
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
            "userAddress": self.address,
            "rewardHypervisorAddress": XGAMMA_ADDRESS,
        }
        response = await self.gamma_client.query(query, variables)
        self.data = response["data"]


class UserInfo(UserData):
    async def output(self, get_data=True):

        if get_data:
            await self._get_data()

        if not self.data.get("user"):
            return {}

        accounts = {}
        for account in self.data["user"]["accountsOwned"]:
            account_address = account["id"]
            account_info = AccountInfo(self.chain, account_address)
            account_info.data = {
                "account": account,
                "rewardHypervisor": self.data["rewardHypervisor"],
            }
            accounts[account_address] = await account_info.output(get_data=False)

        return accounts
