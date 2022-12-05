from v3data import GammaClient, MasterChefContract, RewarderContract
from v3data.constants import YEAR_SECONDS
from v3data.pricing import token_price_from_address


class MasterchefV2Data:
    def __init__(self, protocol: str, chain: str = "mainnet"):
        self.chain = chain
        self.gamma_client = GammaClient(protocol, chain)
        self.data = {}

    async def _get_masterchef_data(self):
        query = """
        {
            masterChefV2S {
                id
                pools {
                    id
                    lastRewardTimestamp
                    poolId
                    stakeToken {
                        id
                        symbol
                        decimals
                    }
                    totalStaked
                    hypervisor {
                        id
                        symbol
                        pricePerShare
                    }
                    rewarders {
                        id
                        lastRewardTimestamp
                        rewardPerSecond
                        rewardToken {
                            id
                            symbol
                            decimals
                        }
                    }
                }
            }
        }
        """

        response = await self.gamma_client.query(query)
        self.data = response["data"]["masterChefV2S"]

    async def _get_user_data(self, user_address):
        query = """
        query userRewards($userAddress: String!){
            account(id: $userAddress) {
                masterChefV2RewarderAccounts {
                    amount
                    rewarder {
                        id
                        rewardToken {
                            id
                            symbol
                            decimals
                        }
                        masterChefPool {
                            poolId
                            hypervisor{
                                id
                                symbol
                            }
                        }
                    }
                }
            }
        }
        """
        variables = {"userAddress": user_address}

        response = await self.gamma_client.query(query, variables)
        self.data = response["data"]["account"]


class MasterchefV2Info(MasterchefV2Data):
    async def output(self, get_data=True):
        if get_data:
            await self._get_masterchef_data()

        info = {}

        for masterChef in self.data:
            pool_info = {}
            for pool in masterChef["pools"]:
                reward_per_second_usdc = 0
                rewarder_info = {}
                for rewarder in pool["rewarders"]:
                    reward_token = rewarder["rewardToken"]["id"]
                    reward_token_symbol = rewarder["rewardToken"]["symbol"]
                    reward_per_second = (
                        int(rewarder["rewardPerSecond"])
                        / 10 ** rewarder["rewardToken"]["decimals"]
                    )

                    rewardTokenPrice = await token_price_from_address(
                        self.chain, rewarder["rewardToken"]["id"]
                    )

                    reward_per_second_usdc += (
                        reward_per_second * rewardTokenPrice["token_in_usdc"]
                    )

                    rewarder_info[rewarder["id"]] = {
                        "rewardToken": reward_token,
                        "rewardTokenSymbol": reward_token_symbol,
                        "rewardPerSecond": reward_per_second,
                    }

                try:
                    apr = (
                        reward_per_second_usdc
                        * YEAR_SECONDS
                        / (
                            int(pool["totalStaked"])
                            * float(pool["hypervisor"]["pricePerShare"])
                        )
                    )
                except ZeroDivisionError:
                    apr = 0

                pool_info[pool["hypervisor"]["id"]] = {
                    "stakeTokenSymbol": pool["stakeToken"]["symbol"],
                    "apr": apr,
                    "lastRewardTimestamp": pool["lastRewardTimestamp"],
                    "rewarders": rewarder_info,
                }

            info[masterChef["id"]] = {"pools": pool_info}

        return info


class UserRewardsV2(MasterchefV2Data):
    def __init__(self, user_address: str, protocol: str, chain: str = "mainnet"):
        super().__init__(protocol, chain)
        self.user_address = user_address.lower()

    async def output(self, get_data=True):
        if get_data:
            await self._get_user_data(self.user_address)

        if not self.data:
            return {}

        # return self.data

        info = {}
        for account in self.data["masterChefV2RewarderAccounts"]:
            hypervisor_id = account["rewarder"]["masterChefPool"]["hypervisor"]["id"]
            hypervisor_symbol = account["rewarder"]["masterChefPool"]["hypervisor"][
                "symbol"
            ]
            hypervisor_decimal = 18

            # pool_id = int(account["rewarder"]["masterChefPool"]["poolId"])

            reward_token_id = account["rewarder"]["rewardToken"]["id"]
            reward_token_symbol = account["rewarder"]["rewardToken"]["symbol"]
            # reward_decimals = int(account["rewarder"]["rewardToken"]["decimals"])

            if not info.get(hypervisor_id):
                info[hypervisor_id] = {"hypervisorSymbol": hypervisor_symbol}

            info[hypervisor_id][reward_token_id] = {
                "stakedAmount": int(account["amount"]) / 10 ** hypervisor_decimal,
                "rewardTokenSymbol": reward_token_symbol,
            }

        return info

    def _get_pending_reward(self, rewarder, pool_id):
        masterchef_contract = RewarderContract(rewarder, self.chain)
        return masterchef_contract.pending_rewards(pool_id, self.user_address).call()
