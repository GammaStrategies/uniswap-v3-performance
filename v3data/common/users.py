from v3data.accounts import AccountInfo
from v3data.enums import Chain, Protocol
from v3data.users import UserInfo
from fastapi import Response

from database.collection_endpoint import database_local, convert_chain_name
from v3data.config import MONGO_DB_URL


async def user_data(protocol: Protocol, chain: Chain, address: str):
    user_info = UserInfo(protocol, chain, address)
    return await user_info.output(get_data=True)


async def account_data(protocol: Protocol, chain: Chain, address: str):
    account_info = AccountInfo(protocol, chain, address)
    return await account_info.output()


async def get_user_data_db(
    chain: Chain,
    address: str,
    block_ini: int = 0,
    block_end: int = 0,
    response: Response | None = None,
):
    db_name = f"{convert_chain_name(chain)}_gamma"
    local_db_helper = database_local(mongo_url=MONGO_DB_URL, db_name=db_name)
    return await local_db_helper.get_user_status(
        address=address, block_ini=block_ini, block_end=block_end
    )
