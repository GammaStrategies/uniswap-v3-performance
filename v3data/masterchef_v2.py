"""Module for Masterchef V2 related data"""

from v3data import GammaClient
from v3data.constants import YEAR_SECONDS
from v3data.enums import Chain, Protocol
from v3data.pricing import token_prices


class MasterchefV2Data:
    def __init__(self, protocol: Protocol, chain: Chain = Chain.MAINNET):
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

        pricing = await token_prices(self.chain)

        for masterChef in self.data:
            pool_info = {}
            for pool in masterChef["pools"]:
                pool_apr = 0
                reward_per_second_usdc = 0
                rewarder_info = {}
                staked_lp_amount = int(pool["totalStaked"])
                staked_lp_usdc = staked_lp_amount * float(
                    pool["hypervisor"]["pricePerShare"]
                )
                for rewarder_pool in pool["rewarders"]:
                    reward_token = rewarder_pool["rewarder"]["rewardToken"]["id"]
                    reward_token_symbol = rewarder_pool["rewarder"]["rewardToken"][
                        "symbol"
                    ]
                    reward_per_second = (
                        int(rewarder_pool["rewarder"]["rewardPerSecond"])
                        / 10 ** rewarder_pool["rewarder"]["rewardToken"]["decimals"]
                    )

                    reward_token_price = pricing.get(
                        rewarder_pool["rewarder"]["rewardToken"]["id"], 0
                    )

                    total_alloc_point = int(
                        rewarder_pool["rewarder"]["totalAllocPoint"]
                    )

                    if total_alloc_point > 0:
                        weighted_reward_per_second = (
                            reward_per_second
                            * int(rewarder_pool["allocPoint"])
                            / int(rewarder_pool["rewarder"]["totalAllocPoint"])
                        )
                    else:
                        weighted_reward_per_second = 0

                    try:
                        rewarder_apr = (
                            weighted_reward_per_second
                            * reward_token_price
                            * YEAR_SECONDS
                            / staked_lp_usdc
                        )
                    except ZeroDivisionError:
                        rewarder_apr = 0

                    rewarder_info[rewarder_pool["rewarder"]["id"]] = {
                        "rewardToken": reward_token,
                        "rewardTokenDecimals": rewarder_pool["rewarder"]["rewardToken"][
                            "decimals"
                        ],
                        "rewardTokenSymbol": reward_token_symbol,
                        "rewardPerSecond": weighted_reward_per_second,
                        "apr": rewarder_apr,
                        "allocPoint": rewarder_pool["allocPoint"],
                    }

                    # Weighted reward_per_second_usdc
                    reward_per_second_usdc += (
                        weighted_reward_per_second * reward_token_price
                    )

                    pool_apr += rewarder_apr

                pool_info[pool["hypervisor"]["id"]] = {
                    "stakeTokenSymbol": pool["stakeToken"]["symbol"],
                    "stakedAmount": staked_lp_amount
                    / 10 ** int(pool["stakeToken"]["decimals"]),
                    "stakedAmountUSD": staked_lp_usdc,
                    "apr": pool_apr,
                    "lastRewardTimestamp": pool["lastRewardTimestamp"],
                    "rewarders": rewarder_info,
                }

            info[masterChef["id"]] = {"pools": pool_info}
        return info


class UserRewardsV2(MasterchefV2Data):
    def __init__(
        self, user_address: str, protocol: Protocol, chain: Chain = Chain.MAINNET
    ):
        super().__init__(protocol, chain)
        self.user_address = user_address.lower()

    async def output(self, get_data=True):
        if get_data:
            if self.protocol == Protocol.QUICKSWAP:
                await self._get_user_data_pool(self.user_address)
            else:
                await self._get_user_data(self.user_address)

        if not self.data:
            return {}

        info = []

        if self.protocol == Protocol.QUICKSWAP:
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
