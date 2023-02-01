from v3data.masterchef_v2 import MasterchefV2Info, UserRewardsV2
from database.collection_endpoint import db_allRewards2_manager


async def info(protocol: str, chain: str):
    # TODO: if statement check database content ( maybe datetime field)
    _mngr = db_allRewards2_manager(mongo_url=MONGO_DB_URL)
    result = await _mngr.get_data(chain=chain, protocol=protocol)
    return result
    # masterchef_info = MasterchefV2Info(protocol, chain)
    # return await masterchef_info.output(get_data=True)


async def user_rewards(protocol: str, chain: str, user_address: str):
    user_rewards = UserRewardsV2(user_address, protocol, chain)
    return await user_rewards.output(get_data=True)
