import asyncio
from v3data import GammaClient
from v3data.constants import XGAMMA_ADDRESS
from v3data.pricing import token_price


class AccountData:
    def __init__(self, chain: str, account_address: str):
        self.gamma_client = GammaClient(chain)
        self.gamma_client_mainnet = GammaClient("mainnet")
        self.address = account_address.lower()
        self.reward_hypervisor_address = XGAMMA_ADDRESS
        self.decimal_factor = 10**18

    async def _get_data(self):
        query = """
        query accountHypervisor($accountAddress: String!) {
            account(
                id: $accountAddress
            ){
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
        """
        variables = {
            "accountAddress": self.address,
        }

        query_xgamma = """
        query accountXgamma($accountAddress: String!, $rewardHypervisorAddress: String!) {
            account(
                id: $accountAddress
            ){
                parent { id }
                gammaDeposited
                gammaEarnedRealized
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
        variables_xgamma = {
            "accountAddress": self.address,
            "rewardHypervisorAddress": self.reward_hypervisor_address,
        }

        hypervisor_response, xgamma_response = await asyncio.gather(
            self.gamma_client.query(query, variables),
            self.gamma_client_mainnet.query(query_xgamma, variables_xgamma),
        )

        self.data = {
            "hypervisor": hypervisor_response["data"],
            "xgamma": xgamma_response["data"],
        }


class AccountInfo(AccountData):
    def _returns(self):
        returns = {}
        for share in self.data["hypervisor"]["account"]["hypervisorShares"]:
            if int(share["shares"]) <= 0:  # Workaround before fix in subgraph
                continue
            hypervisor_address = share["hypervisor"]["id"]
            initial_token0 = int(share["initialToken0"])
            initial_token1 = int(share["initialToken1"])
            initial_USD = float(share["initialUSD"])
            shareOfPool = int(share["shares"]) / int(share["hypervisor"]["totalSupply"])
            tvl_USD = float(share["hypervisor"]["tvlUSD"])

            conversion = share["hypervisor"]["conversion"]

            base_token_index = int(conversion["baseTokenIndex"])
            price_token_in_base = float(conversion["priceTokenInBase"])
            price_base_in_usd = float(conversion["priceBaseInUSD"])

            if base_token_index == 0:
                token = initial_token1
                base = initial_token0
            elif base_token_index == 1:
                token = initial_token0
                base = initial_token1
            else:
                token = 0
                base = 0

            initial_token_current_USD = (
                token * price_token_in_base * price_base_in_usd
            ) + (base * price_base_in_usd)
            current_USD = shareOfPool * tvl_USD

            returns[hypervisor_address] = {
                "initialTokenUSD": initial_USD,
                "initialTokenCurrentUSD": initial_token_current_USD,
                "currentUSD": current_USD,
                "netMarketReturnsUSD": current_USD - initial_USD,
                "netMarketReturnsPercentage": f"{(current_USD /initial_USD) - 1:.2%}"
                if initial_USD > 0
                else "N/A",
                "hypervisorReturnsUSD": current_USD - initial_token_current_USD,
                "hypervisorReturnsPercentage": f"{(current_USD / initial_token_current_USD) - 1:.2%}"
                if initial_token_current_USD > 0
                else "N/A",
            }

        return returns

    async def output(self, get_data=True):

        if get_data:
            await self._get_data()

        hypervisor_data = self.data["hypervisor"]
        xgamma_data = self.data["xgamma"]

        if not (hypervisor_data.get("account") or xgamma_data.get("account")):
            return {}

        account_info = {
            "owner": hypervisor_data["account"]["parent"]["id"],
            "gammaStaked": 0,
            "gammaStakedUSD": 0,
            "gammaDeposited": 0,
            "pendingGammaEarned": 0,
            "pendingGammaEarnedUSD": 0,
            "totalGammaEarned": 0,
            "totalGammaEarnedUSD": 0,
            "gammaStakedShare": 0,
            "xgammaAmount": 0,
        }

        if xgamma_data.get("account"):
            reward_hypervisor_shares = xgamma_data["account"]["rewardHypervisorShares"]
            xgamma_shares = 0
            for shares in reward_hypervisor_shares:
                if (
                    shares.get("rewardHypervisor", {}).get("id")
                    == self.reward_hypervisor_address
                ):
                    xgamma_shares = int(shares["shares"])

            totalGammaStaked = int(xgamma_data["rewardHypervisor"]["totalGamma"])
            xgamma_virtual_price = totalGammaStaked / int(
                xgamma_data["rewardHypervisor"]["totalSupply"]
            )

            # Get pricing
            gamma_pricing = await token_price("GAMMA")

            gammaStaked = (xgamma_shares * xgamma_virtual_price) / self.decimal_factor
            gammaDeposited = (
                int(xgamma_data["account"]["gammaDeposited"]) / self.decimal_factor
            )
            gammaEarnedRealized = (
                int(xgamma_data["account"]["gammaEarnedRealized"]) / self.decimal_factor
            )
            gammaStakedShare = gammaStaked / (totalGammaStaked / self.decimal_factor)
            pendingGammaEarned = gammaStaked - gammaDeposited
            totalGammaEarned = gammaStaked - gammaDeposited + gammaEarnedRealized
            account_info.update(
                {
                    "gammaStaked": gammaStaked,
                    "gammaStakedUSD": gammaStaked * gamma_pricing["token_in_usdc"],
                    "gammaDeposited": gammaDeposited,
                    "pendingGammaEarned": pendingGammaEarned,
                    "pendingGammaEarnedUSD": pendingGammaEarned
                    * gamma_pricing["token_in_usdc"],
                    "totalGammaEarned": totalGammaEarned,
                    "totalGammaEarnedUSD": totalGammaEarned * gamma_pricing["token_in_usdc"],
                    "gammaStakedShare": f"{gammaStakedShare:.2%}",
                    "xgammaAmount": xgamma_shares / self.decimal_factor,
                }
            )
            # The below for compatability
            account_info.update(
                {
                    "visrStaked": account_info["gammaStaked"],
                    "visrDeposited": account_info["gammaDeposited"],
                    "totalVisrEarned": account_info["totalGammaEarned"],
                    "visrStakedShare": account_info["gammaStakedShare"],
                }
            )

        returns = self._returns()

        for hypervisor in hypervisor_data["account"]["hypervisorShares"]:
            if int(hypervisor["shares"]) <= 0:  # Workaround before fix in subgraph
                continue
            hypervisor_id = hypervisor["hypervisor"]["id"]
            shares = int(hypervisor["shares"])
            totalSupply = int(hypervisor["hypervisor"]["totalSupply"])
            shareOfSupply = shares / totalSupply if totalSupply > 0 else 0
            tvlUSD = float(hypervisor["hypervisor"]["tvlUSD"])
            decimal0 = int(hypervisor["hypervisor"]["pool"]["token0"]["decimals"])
            decimal1 = int(hypervisor["hypervisor"]["pool"]["token1"]["decimals"])
            tvl0_decimal = float(hypervisor["hypervisor"]["tvl0"]) / 10**decimal0
            tvl1_decimal = float(hypervisor["hypervisor"]["tvl1"]) / 10**decimal1

            account_info[hypervisor_id] = {
                "shares": shares,
                "shareOfSupply": shareOfSupply,
                "balance0": tvl0_decimal * shareOfSupply,
                "balance1": tvl1_decimal * shareOfSupply,
                "balanceUSD": tvlUSD * shareOfSupply,
                "returns": returns[hypervisor_id],
            }

        return account_info
