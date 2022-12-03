from v3data import GammaClient


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


class MasterchefV2Info(MasterchefV2Data):
    async def output(self, get_data=True):
        if get_data:
            await self._get_masterchef_data()

        info = {}

        for masterChef in self.data:
            pool_info = {}
            for pool in masterChef["pools"]:
                rewarder_info = {}
                for rewarder in pool["rewarders"]:
                    rewarder_info[rewarder["id"]] = {
                        "rewardToken": rewarder["rewardToken"]["id"],
                        "rewardTokenSymbol": rewarder["rewardToken"]["symbol"],
                        "rewardPerSecond": rewarder["rewardPerSecond"]
                    }
                pool_info[pool["hypervisor"]["id"]] = {
                    "stakeTokenSymbol": pool["stakeToken"]["symbol"],
                    "apr": 0,
                    "lastRewardTimestamp": pool["lastRewardTimestamp"],
                    "rewarders": rewarder_info
                }

            info[masterChef["id"]] = {
                "pools": pool_info
            }

        return info
