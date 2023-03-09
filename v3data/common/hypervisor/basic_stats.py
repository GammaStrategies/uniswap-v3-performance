from datetime import date
from pydantic import BaseModel
from fastapi import Response, status
from v3data.enums import Chain, Protocol

from v3data.hypervisor import HypervisorInfo


class HypervisorBasicInfoOutput(BaseModel):
    createDate: date
    poolAddress: str
    name: str
    token0: str
    token1: str
    decimals0: int
    decimals1: int
    depositCap0: float
    depositCap1: float
    grossFeesClaimed0: float
    grossFeesClaimed1: float
    grossFeesClaimedUSD: float
    feesReinvested0: float
    feesReinvested1: float
    feesReinvestedUSD: float
    tvl0: float
    tvl1: float
    tvlUSD: float
    totalSupply: float
    maxTotalSupply: float
    capacityUsed: str
    sqrtPrice: int
    tick: int
    baseLower: int
    baseUpper: int
    inRange: bool
    observationIndex: int
    poolTvlUSD: float
    poolFeesUSD: float


async def hypervisor_basic_stats(
    protocol: Protocol, chain: Chain, hypervisor_address: str, response: Response
) -> HypervisorBasicInfoOutput:
    hypervisor_info = HypervisorInfo(protocol, chain)
    basic_stats = await hypervisor_info.basic_stats(hypervisor_address)

    if basic_stats:
        return basic_stats
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return "Invalid hypervisor address or not enough data"
