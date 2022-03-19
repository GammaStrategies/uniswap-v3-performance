from fastapi import APIRouter
from v3data.simulator import SimulatorInfo

router = APIRouter(prefix="/simulator")


@router.get("/tokenList")
async def token_list():
    tokens = await SimulatorInfo("mainnet").token_list()

    return tokens


@router.get("/poolTicks")
async def pool_ticks(poolAddress: str):
    ticks = await SimulatorInfo("mainnet").pool_ticks(poolAddress)

    return ticks


@router.get("/poolFromTokens")
async def pool_from_tokens(token0: str, token1: str):
    pools = await SimulatorInfo("mainnet").pools_from_tokens(token0, token1)

    return pools


@router.get("/pool24HrVolume")
async def pool_ticks(poolAddress: str):
    volume = await SimulatorInfo("mainnet").pool_volume(poolAddress)

    return volume
