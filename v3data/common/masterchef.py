from v3data.masterchef import MasterchefInfo, UserRewards
from v3data.enums import Chain, Protocol


async def info(protocol: Protocol, chain: Chain):
    masterchef_info = MasterchefInfo(protocol, chain)
    return await masterchef_info.output(get_data=True)


async def user_rewards(protocol: Protocol, chain: Chain, user_address: str):
    user_rewards = UserRewards(user_address, protocol, chain)
    return await user_rewards.output(get_data=True)
