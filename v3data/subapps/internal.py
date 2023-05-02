import asyncio

from fastapi import FastAPI, HTTPException

from v3data.config import DEPLOYMENTS
from v3data.enums import Chain, Protocol
from v3data.hype_fees.fees_yield import fee_returns_all

app_internal = FastAPI()


@app_internal.get("/{protocol}/{chain}/returns")
async def fee_returns(protocol: Protocol, chain: Chain):
    """Returns APR and APY for specific protocol and chain"""
    if (protocol, chain) not in DEPLOYMENTS:
        raise HTTPException(status_code=400, detail=f"{protocol} on {chain} not available.")

    daily, weekly, monthly = await asyncio.gather(
        fee_returns_all(protocol, chain, 1),
        fee_returns_all(protocol, chain, 7),
        fee_returns_all(protocol, chain, 30),
        return_exceptions=True
    )

