from fastapi import Response, status

from v3data.hypervisor import HypervisorInfo
from v3data.toplevel import TopLevelData
from v3data.hypes.fees import Fees
from v3data.hypes.fees_yield import FeesYield
from v3data.hype_fees.fees import fees_usd_all
from v3data.hype_fees.fees_yield import fee_returns_all


async def hypervisor_basic_stats(
    protocol: str, chain: str, hypervisor_address: str, response: Response
):
    hypervisor_info = HypervisorInfo(protocol, chain)
    basic_stats = await hypervisor_info.basic_stats(hypervisor_address)

    if basic_stats:
        return basic_stats
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return "Invalid hypervisor address or not enough data"


async def hypervisor_apy(
    protocol: str, chain: str, hypervisor_address, response: Response
):
    hypervisor_info = HypervisorInfo(protocol, chain)
    returns = await hypervisor_info.calculate_returns(hypervisor_address)

    if returns:
        return {"hypervisor": hypervisor_address, "returns": returns}
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return "Invalid hypervisor address or not enough data"


async def aggregate_stats(protocol: str, chain: str):
    top_level = TopLevelData(protocol, chain)
    top_level_data = await top_level.all_stats()

    return {
        "totalValueLockedUSD": top_level_data["tvl"],
        "pairCount": top_level_data["pool_count"],
        "totalFeesClaimedUSD": top_level_data["fees_claimed"],
    }


async def recent_fees(protocol: str, chain: str, hours: int = 24):
    top_level = TopLevelData(protocol, chain)
    recent_fees = await top_level.recent_fees(hours)

    return {"periodHours": hours, "fees": recent_fees}


async def hypervisors_return(protocol: str, chain: str):
    hypervisor_info = HypervisorInfo(protocol, chain)

    return await hypervisor_info.all_returns()


async def hypervisors_all(protocol: str, chain: str):
    hypervisor_info = HypervisorInfo(protocol, chain)
    return await hypervisor_info.all_data()


async def uncollected_fees(protocol: str, chain: str, hypervisor_address: str):
    fees = Fees(protocol, chain)
    return await fees.output([hypervisor_address])


async def uncollected_fees_all(protocol: str, chain: str):
    fees = Fees(protocol, chain)
    return await fees.output()


async def uncollected_fees_all_fg(protocol: str, chain: str):
    return await fees_usd_all(protocol, chain)


async def fee_returns(protocol: str, chain: str, days: int):
    fees_yield = FeesYield(days, protocol, chain)
    output = await fees_yield.get_fees_yield()
    return output


async def fee_returns_fg(protocol: str, chain: str, days: int):
    return await fee_returns_all(protocol, chain, days)
