from v3data.masterchef_v2 import MasterchefV2Info, UserRewardsV2
from database.collection_endpoint import db_allRewards2_manager
from v3data.config import MONGO_DB_URL


async def info(protocol: str, chain: str):
    try:
        _mngr = db_allRewards2_manager(mongo_url=MONGO_DB_URL)
        result = await _mngr.get_last_data(chain=chain, protocol=protocol)
        if result == {}:
            raise ValueError(" no data in database ?")
        return result
    except:
        # DB may not respond
        logger.warning(
            " Could not get database allRewards2 data for {protocol} in {chain}. Return calculated data."
        )
        masterchef_info = MasterchefV2Info(protocol, chain)
        return await masterchef_info.output(get_data=True)


async def user_rewards(protocol: str, chain: str, user_address: str):
    user_rewards = UserRewardsV2(user_address, protocol, chain)
    return await user_rewards.output(get_data=True)
