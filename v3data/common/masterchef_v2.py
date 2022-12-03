from v3data.masterchef_v2 import MasterchefV2Info


async def info(protocol: str, chain: str):
    masterchef_info = MasterchefV2Info(protocol, chain)
    return await masterchef_info.output(get_data=True)
