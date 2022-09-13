from v3data import GammaClient, MasterChefContract
from v3data.constants import BLOCKS_IN_YEAR
from v3data.pricing import token_price_from_address


class MasterchefData:
    def __init__(self, chain: str = "mainnet"):
        self.chain = chain
        self.gamma_client = GammaClient(chain)
        self.data = {}

    async def _get_masterchef_data(self):
        query = """
        {
            masterChefs {
                id
                rewardPerBlock
                totalAllocPoint
                rewardToken{
                    id
                    symbol
                    decimals
                }
                pools {
                    id
                    allocPoint
                    lastRewardBlock
                    totalStaked
                    hypervisor{
                        id
                        symbol
                        pricePerShare
                    }
                }
            }
        }
        """

        response = await self.gamma_client.query(query)
        self.data = response["data"]["masterChefs"]

    async def _get_user_data(self, user_address):
        query = """
        query userRewards($userAddress: String!){
            account(id: $userAddress) {
                masterChefPoolAccounts {
                    amount
                    masterChefPool {
                        poolId
                        masterChef {
                            id
                            rewardToken { 
                                id
                                symbol
                                decimals
                            }
                        }
                        hypervisor { 
                            id
                            symbol
                        }
                    }
                }
            }
        }
        """
        variables = {"userAddress": user_address}

        response = await self.gamma_client.query(query, variables)
        self.data = response["data"]["account"]


class MasterchefInfo(MasterchefData):
    async def output(self, get_data=True):
        if get_data:
            await self._get_masterchef_data()

        info = {}

        for masterchef in self.data:
            rewardTokenPrice = await token_price_from_address(
                self.chain, masterchef["rewardToken"]["id"]
            )
            rewardTokenPriceUsdc = rewardTokenPrice["token_in_usdc"]
            reward_per_block = (
                int(masterchef["rewardPerBlock"])
                / 10 ** masterchef["rewardToken"]["decimals"]
            )
            info[masterchef["id"]] = {
                "rewardToken": masterchef["rewardToken"]["id"],
                "rewardTokenSymbol": masterchef["rewardToken"]["symbol"],
                "rewardPerBlock": reward_per_block,
                "totalAllocPoint": masterchef["totalAllocPoint"],
                "pools": {
                    pool["hypervisor"]["id"]: {
                        "hypervisorSymbol": pool["hypervisor"]["symbol"],
                        "allocPoint": pool["allocPoint"],
                        "lastRewardBlock": pool["lastRewardBlock"],
                        "apr": rewardTokenPriceUsdc
                        * reward_per_block
                        * (int(pool["allocPoint"]) / int(masterchef["totalAllocPoint"]))
                        * BLOCKS_IN_YEAR[self.chain]
                        / (
                            int(pool["totalStaked"])
                            * float(pool["hypervisor"]["pricePerShare"])
                        ),
                    }
                    for pool in masterchef["pools"]
                },
            }

        return info


class UserRewards(MasterchefData):
    def __init__(self, user_address: str, chain: str = "mainnet"):
        super().__init__(chain)
        self.user_address = user_address.lower()

    async def output(self, get_data=True):
        if get_data:
            await self._get_user_data(self.user_address)

        if not self.data:
            return {}

        info = {}
        for pool in self.data["masterChefPoolAccounts"]:
            hypervisor_id = pool["masterChefPool"]["hypervisor"]["id"]
            hypervisor_symbol = pool["masterChefPool"]["hypervisor"]["symbol"]
            hypervisor_decimal = 18
            masterchef_id = pool["masterChefPool"]["masterChef"]["id"]
            pool_id = int(pool["masterChefPool"]["poolId"])
            reward_token_id = pool["masterChefPool"]["masterChef"]["rewardToken"]["id"]
            reward_token_symbol = pool["masterChefPool"]["masterChef"]["rewardToken"][
                "symbol"
            ]
            reward_decimals = int(
                pool["masterChefPool"]["masterChef"]["rewardToken"]["decimals"]
            )

            if not info.get(hypervisor_id):
                info[hypervisor_id] = {"hypervisorSymbol": hypervisor_symbol}
            info[hypervisor_id][reward_token_id] = {
                "stakedAmount": int(pool["amount"]) / 10**hypervisor_decimal,
                "pendingRewards": self._get_pending_reward(
                    masterchef_id,
                    pool_id,
                )
                / 10**reward_decimals,
                "rewardTokenSymbol": reward_token_symbol,
            }

        return info

    def _get_pending_reward(self, masterchef, pool_id):
        masterchef_contract = MasterChefContract(masterchef, self.chain)
        return masterchef_contract.pending_rewards(pool_id, self.user_address).call()
