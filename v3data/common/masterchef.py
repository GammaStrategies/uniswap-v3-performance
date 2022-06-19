from v3data.masterchef import MasterchefInfo, UserRewards


async def info(chain: str):
    masterchef_info = MasterchefInfo(chain)
    return await masterchef_info.output(get_data=True)

async def user_rewards(chain: str, user_address: str):
    user_rewards = UserRewards(user_address, chain)
    return await user_rewards.output(get_data=True)
