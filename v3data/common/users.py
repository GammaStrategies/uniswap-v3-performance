from v3data.accounts import AccountInfo
from v3data.users import UserInfo


async def user_data(protocol: str, chain: str, address: str):
    user_info = UserInfo(protocol, chain, address)
    return await user_info.output(get_data=True)


async def account_data(protocol: str, chain: str, address: str):
    account_info = AccountInfo(protocol, chain, address)
    return await account_info.output()
