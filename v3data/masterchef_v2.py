from v3data import GammaClient, RewarderContract
from v3data.constants import YEAR_SECONDS
from v3data.pricing import token_price_from_address
from v3data.config import DISABLE_POOL_APR


class MasterchefV2Data:
    def __init__(self, protocol: str, chain: str = "mainnet"):
        self.protocol = protocol
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
                        allocPoint
                        rewarder {
                            id
                            lastRewardTimestamp
                            rewardPerSecond
                            totalAllocPoint
                            rewardToken {
                                id
                                symbol
                                decimals
                            }
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
        query userRewards($userAddress: String!) {
            account(id: $userAddress) {
                mcv2RewarderPoolAccounts {
                    amount
                    rewarderPool {
                        rewarder {
                            id
                            rewardToken {
                                id
                                symbol
                                decimals
                            }
                        }
                        pool {
                            masterChef { id }
                            poolId
                            hypervisor {
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

    async def _get_user_data_pool(self, user_address):
        query = """
        query userRewards($userAddress: String!){
            account(id: $userAddress) {
                mcv2PoolAccounts {
                    amount
                    pool {
                        poolId
                        masterChef { id }
                        hypervisor {
                            id
                            symbol
                        }
                        rewarders(where: {allocPoint_gt: 0}) {
                            allocPoint
                            rewarder {
                                id
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
                for rewarderPool in pool["rewarders"]:
                    reward_token = rewarderPool["rewarder"]["rewardToken"]["id"]
                    reward_token_symbol = rewarderPool["rewarder"]["rewardToken"][
                        "symbol"
                    ]
                    reward_per_second = (
                        int(rewarderPool["rewarder"]["rewardPerSecond"])
                        / 10 ** rewarderPool["rewarder"]["rewardToken"]["decimals"]
                    )

                    reward_token_price = await token_price_from_address(
                        self.chain, rewarderPool["rewarder"]["rewardToken"]["id"]
                    )

                    total_alloc_point = int(rewarderPool["rewarder"]["totalAllocPoint"])

                    if total_alloc_point > 0:
                        weighted_reward_per_second = (
                            reward_per_second
                            * int(rewarderPool["allocPoint"])
                            / int(rewarderPool["rewarder"]["totalAllocPoint"])
                        )
                    else:
                        weighted_reward_per_second = 0

                    if DISABLE_POOL_APR and pool["poolId"] in ["16", "17"]:
                        weighted_reward_per_second = 0

                    rewarder_info[rewarderPool["rewarder"]["id"]] = {
                        "rewardToken": reward_token,
                        "rewardTokenSymbol": reward_token_symbol,
                        "rewardPerSecond": weighted_reward_per_second,
                        "allocPoint": rewarderPool["allocPoint"],
                    }

                    # Weighted reward_per_second_usdc
                    reward_per_second_usdc += (
                        weighted_reward_per_second * reward_token_price["token_in_usdc"]
                    )

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

                if DISABLE_POOL_APR and pool["poolId"] in ["16", "17"]:
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
            if self.protocol == "quickswap":
                await self._get_user_data_pool(self.user_address)
            else:
                await self._get_user_data(self.user_address)

        if not self.data:
            return {}

        info = []

        if self.protocol == "quickswap":
            for account in self.data["mcv2PoolAccounts"]:
                pool = account["pool"]
                masterchef_id = pool["masterChef"]["id"]

                hypervisor_id = pool["hypervisor"]["id"]
                hypervisor_symbol = pool["hypervisor"]["symbol"]
                hypervisor_decimal = 18

                pool_id = int(pool["poolId"])

                for rewarder in pool["rewarders"]:

                    rewarder_info = rewarder["rewarder"]
                    if int(rewarder_info["rewardPerSecond"]) <= 0:
                        continue

                    rewarder_id = rewarder_info["id"]
                    reward_token_id = rewarder_info["rewardToken"]["id"]
                    reward_token_symbol = rewarder_info["rewardToken"]["symbol"]

                    info.append(
                        {
                            "masterchef": masterchef_id,
                            "poolId": pool_id,
                            "hypervisor": hypervisor_id,
                            "hypervisorSymbol": hypervisor_symbol,
                            "rewarder": rewarder_id,
                            "rewardToken": reward_token_id,
                            "rewardTokenSymbol": reward_token_symbol,
                            "stakedAmount": int(account["amount"])
                            / 10**hypervisor_decimal,
                        }
                    )
        else:
            for account in self.data["mcv2RewarderPoolAccounts"]:

                masterchef_id = account["rewarderPool"]["pool"]["masterChef"]["id"]

                hypervisor_id = account["rewarderPool"]["pool"]["hypervisor"]["id"]
                hypervisor_symbol = account["rewarderPool"]["pool"]["hypervisor"][
                    "symbol"
                ]
                hypervisor_decimal = 18

                pool_id = int(account["rewarderPool"]["pool"]["poolId"])

                rewarder_id = account["rewarderPool"]["rewarder"]["id"]
                reward_token_id = account["rewarderPool"]["rewarder"]["rewardToken"][
                    "id"
                ]
                reward_token_symbol = account["rewarderPool"]["rewarder"][
                    "rewardToken"
                ]["symbol"]

                info.append(
                    {
                        "masterchef": masterchef_id,
                        "poolId": pool_id,
                        "hypervisor": hypervisor_id,
                        "hypervisorSymbol": hypervisor_symbol,
                        "rewarder": rewarder_id,
                        "rewardToken": reward_token_id,
                        "rewardTokenSymbol": reward_token_symbol,
                        "stakedAmount": int(account["amount"])
                        / 10**hypervisor_decimal,
                    }
                )

        return {"stakes": info}

    def _get_pending_reward(self, rewarder, pool_id):
        masterchef_contract = RewarderContract(rewarder, self.chain)
        return masterchef_contract.pending_rewards(pool_id, self.user_address).call()
