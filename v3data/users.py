import asyncio
from v3data import GammaClient
from v3data.accounts import AccountInfo
from v3data.constants import XGAMMA_ADDRESS
from v3data.enums import Chain, Protocol


class UserData:
    def __init__(self, protocol: Protocol, chain: Chain, user_address: str):
        self.protocol = protocol
        self.chain = chain
        self.gamma_client = GammaClient(protocol, chain)
        self.gamma_client_mainnet = GammaClient(Protocol.UNISWAP, Chain.MAINNET)
        self.address = user_address.lower()
        self.decimal_factor = 10**18
        self.data = {}

    async def _get_data(self):
        query = """
        query userHypervisor($userAddress: String!) {
            user(
                id: $userAddress
            ){
                accountsOwned {
                    id
                    parent { id }
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

        query_xgamma = """
        query userXgamma($userAddress: String!, $rewardHypervisorAddress: String!) {
            user(
                id: $userAddress
            ){
                accountsOwned {
                    id
                    parent { id }
                    gammaDeposited
                    gammaEarnedRealized
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
        variables_xgamma = {
            "userAddress": self.address,
            "rewardHypervisorAddress": XGAMMA_ADDRESS,
        }

        hypervisor_response, xgamma_response = await asyncio.gather(
            self.gamma_client.query(query, variables),
            self.gamma_client_mainnet.query(query_xgamma, variables_xgamma),
        )

        self.data = {
            "hypervisor": hypervisor_response["data"],
            "xgamma": xgamma_response["data"],
        }


class UserInfo(UserData):
    async def output(self, get_data=True):

        if get_data:
            await self._get_data()

        hypervisor_data = self.data["hypervisor"]
        xgamma_data = self.data["xgamma"]

        has_hypervisor_data = hypervisor_data.get("user")
        has_xgamma_data = xgamma_data.get("user")

        if not (has_hypervisor_data or has_xgamma_data):
            return {}

        if has_hypervisor_data:
            hypervisor_lookup = {
                account.pop("id"): account
                for account in hypervisor_data["user"]["accountsOwned"]
            }
        else:
            hypervisor_lookup = {}

        if has_xgamma_data:
            xgamma_lookup = {
                account.pop("id"): account
                for account in xgamma_data["user"]["accountsOwned"]
            }
        else:
            xgamma_lookup = {}

        # combine accounts owned for both hype and xgamma
        all_accounts = set(list(hypervisor_lookup.keys()) + list(xgamma_lookup.keys()))

        accounts = {}
        # for accountHypervisor in hypervisor_data["user"]["accountsOwned"]:
        for account_address in all_accounts:
            # account_address = accountHypervisor["id"]
            account_info = AccountInfo(self.protocol, self.chain, account_address)
            account_info.data = {
                "hypervisor": {"account": hypervisor_lookup.get(account_address)},
                "xgamma": {
                    "account": xgamma_lookup.get(account_address),
                    "rewardHypervisor": xgamma_data["rewardHypervisor"],
                },
            }
            accounts[account_address] = await account_info.output(get_data=False)

        return accounts
