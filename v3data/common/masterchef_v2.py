from v3data.masterchef_v2 import MasterchefV2Info, UserRewardsV2


async def info(protocol: str, chain: str):
    masterchef_info = MasterchefV2Info(protocol, chain)
    return await masterchef_info.output(get_data=True)


async def user_rewards(protocol: str, chain: str, user_address: str):
    user_rewards = UserRewardsV2(user_address, protocol, chain)
    return await user_rewards.output(get_data=True)
