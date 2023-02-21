from v3data.masterchef import MasterchefInfo, UserRewards


async def info(protocol: str, chain: str):
    masterchef_info = MasterchefInfo(protocol, chain)
    return await masterchef_info.output(get_data=True)


async def user_rewards(protocol: str, chain: str, user_address: str):
    user_rewards = UserRewards(user_address, protocol, chain)
    return await user_rewards.output(get_data=True)
