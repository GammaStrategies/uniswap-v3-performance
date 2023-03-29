import asyncio

from v3data import GammaClient
from v3data.constants import XGAMMA_ADDRESS
from v3data.enums import Chain, Protocol
from v3data.pricing import gamma_price


class AccountData:
    def __init__(self, protocol: Protocol, chain: Chain, account_address: str):
        self.gamma_client = GammaClient(protocol, chain)
        self.gamma_client_mainnet = GammaClient(Protocol.UNISWAP, Chain.MAINNET)
        self.address = account_address.lower()
        self.reward_hypervisor_address = XGAMMA_ADDRESS
        self.decimal_factor = 10**18
        self.data: dict

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
        query accountXgamma(
            $accountAddress: String!,
            $rewardHypervisorAddress: String!
        ){
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
            initial_usd = float(share["initialUSD"])
            share_of_pool = int(share["shares"]) / int(
                share["hypervisor"]["totalSupply"]
            )
            tvl_usd = float(share["hypervisor"]["tvlUSD"])

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

            initial_token_current_usd = (
                token * price_token_in_base * price_base_in_usd
            ) + (base * price_base_in_usd)
            current_usd = share_of_pool * tvl_usd

            hypervisor_returns_percentage = (
                (current_usd / initial_token_current_usd) - 1
                if initial_token_current_usd > 0
                else 0
            )

            returns[hypervisor_address] = {
                "initialTokenUSD": initial_usd,
                "initialTokenCurrentUSD": initial_token_current_usd,
                "currentUSD": current_usd,
                "netMarketReturnsUSD": current_usd - initial_usd,
                "netMarketReturnsPercentage": f"{(current_usd /initial_usd) - 1:.2%}"
                if initial_usd > 0
                else "N/A",
                "hypervisorReturnsUSD": current_usd - initial_token_current_usd,
                "hypervisorReturnsPercentage": f"{hypervisor_returns_percentage:.2%}"
                if initial_token_current_usd > 0
                else "N/A",
            }

        return returns

    async def output(self, get_data=True):
        if get_data:
            await self._get_data()

        hypervisor_data = self.data["hypervisor"]
        xgamma_data = self.data["xgamma"]

        has_hypervisor_data = bool(hypervisor_data.get("account"))
        has_xgamma_data = bool(xgamma_data.get("account"))

        if not (has_hypervisor_data or has_xgamma_data):
            return {}

        if has_hypervisor_data:
            owner = hypervisor_data["account"]["parent"]["id"]
        else:
            owner = xgamma_data["account"]["parent"]["id"]

        account_info = {
            "owner": owner,
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

        if has_xgamma_data:
            reward_hypervisor_shares = xgamma_data["account"]["rewardHypervisorShares"]
            xgamma_shares = 0
            for shares in reward_hypervisor_shares:
                if (
                    shares.get("rewardHypervisor", {}).get("id")
                    == self.reward_hypervisor_address
                ):
                    xgamma_shares = int(shares["shares"])

            total_gamma_staked = int(xgamma_data["rewardHypervisor"]["totalGamma"])
            xgamma_virtual_price = total_gamma_staked / int(
                xgamma_data["rewardHypervisor"]["totalSupply"]
            )

            # Get pricing
            gamma_price_usd = await gamma_price()

            gamma_staked = (xgamma_shares * xgamma_virtual_price) / self.decimal_factor
            gamma_deposited = (
                int(xgamma_data["account"]["gammaDeposited"]) / self.decimal_factor
            )
            gamma_earned_realized = (
                int(xgamma_data["account"]["gammaEarnedRealized"]) / self.decimal_factor
            )
            gamma_staked_share = gamma_staked / (
                total_gamma_staked / self.decimal_factor
            )
            pending_gamma_earned = gamma_staked - gamma_deposited
            total_gamma_earned = gamma_staked - gamma_deposited + gamma_earned_realized
            account_info.update(
                {
                    "gammaStaked": gamma_staked,
                    "gammaStakedUSD": gamma_staked * gamma_price_usd,
                    "gammaDeposited": gamma_deposited,
                    "pendingGammaEarned": pending_gamma_earned,
                    "pendingGammaEarnedUSD": pending_gamma_earned * gamma_price_usd,
                    "totalGammaEarned": total_gamma_earned,
                    "totalGammaEarnedUSD": total_gamma_earned * gamma_price_usd,
                    "gammaStakedShare": f"{gamma_staked_share:.2%}",
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

        if has_hypervisor_data:
            returns = self._returns()
            for hypervisor in hypervisor_data["account"]["hypervisorShares"]:
                if int(hypervisor["shares"]) <= 0:  # Workaround before fix in subgraph
                    continue
                hypervisor_id = hypervisor["hypervisor"]["id"]
                shares = int(hypervisor["shares"])
                total_supply = int(hypervisor["hypervisor"]["totalSupply"])
                share_of_supply = shares / total_supply if total_supply > 0 else 0
                tvl_usd = float(hypervisor["hypervisor"]["tvlUSD"])
                decimal0 = int(hypervisor["hypervisor"]["pool"]["token0"]["decimals"])
                decimal1 = int(hypervisor["hypervisor"]["pool"]["token1"]["decimals"])
                tvl0_decimal = float(hypervisor["hypervisor"]["tvl0"]) / 10**decimal0
                tvl1_decimal = float(hypervisor["hypervisor"]["tvl1"]) / 10**decimal1

                account_info[hypervisor_id] = {
                    "shares": shares,
                    "shareOfSupply": share_of_supply,
                    "balance0": tvl0_decimal * share_of_supply,
                    "balance1": tvl1_decimal * share_of_supply,
                    "balanceUSD": tvl_usd * share_of_supply,
                    "returns": returns[hypervisor_id],
                }

        return account_info
