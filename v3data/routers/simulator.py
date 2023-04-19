from fastapi import APIRouter

from v3data.enums import Chain, Protocol
from v3data.simulator import SimulatorInfo

router = APIRouter(prefix="/simulator")


@router.get("/tokenList")
async def token_list():
    tokens = await SimulatorInfo(Protocol.UNISWAP, Chain.MAINNET).token_list()

    return tokens


@router.get("/poolTicks")
async def pool_ticks(poolAddress: str):
    ticks = await SimulatorInfo(
        Protocol.UNISWAP,
        Chain.MAINNET
    ).pool_ticks(poolAddress)

    return ticks


@router.get("/poolFromTokens")
async def pool_from_tokens(token0: str, token1: str):
    pools = await SimulatorInfo(
        Protocol.UNISWAP,
        Chain.MAINNET
    ).pools_from_tokens(token0, token1)

    return pools


@router.get("/pool24HrVolume")
async def pool_24hr_volume(poolAddress: str):
    volume = await SimulatorInfo(Protocol.UNISWAP, Chain.MAINNET).pool_volume(
        poolAddress
    )

    return volume
