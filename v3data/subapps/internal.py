"""Internal Endpoints"""

import asyncio

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from v3data.config import DEPLOYMENTS
from v3data.enums import Chain, Protocol
from v3data.hype_fees.fees_yield import fee_returns_all

app_internal = FastAPI()


class InternalFeeYield(BaseModel):
    """APR and APY in allData"""

    totalApr: float = 0
    totalApy: float = 0
    lpApr: float = 0
    lpApy: float = 0
    status: str = "No data"


class InternalFeeReturnsOutput(BaseModel):
    """Output model for internal fee returns"""

    symbol: str
    daily: InternalFeeYield = InternalFeeYield()
    weekly: InternalFeeYield = InternalFeeYield()
    monthly: InternalFeeYield = InternalFeeYield()


@app_internal.get("/{protocol}/{chain}/returns")
async def fee_returns(protocol: Protocol, chain: Chain) -> dict[str, InternalFeeReturnsOutput]:
    """Returns APR and APY for specific protocol and chain"""
    if (protocol, chain) not in DEPLOYMENTS:
        raise HTTPException(
            status_code=400, detail=f"{protocol} on {chain} not available."
        )

    results = await asyncio.gather(
        fee_returns_all(protocol, chain, 1, return_total=True),
        fee_returns_all(protocol, chain, 7, return_total=True),
        fee_returns_all(protocol, chain, 30, return_total=True),
        return_exceptions=True,
    )

    result_map = {"daily": results[0], "weekly": results[1], "monthly": results[2]}

    output = {}

    valid_results = (
        result_map["daily"]["lp"]
        if not isinstance(result_map["daily"], Exception)
        else result_map["weekly"]["lp"]
        if not isinstance(result_map["weekly"], Exception)
        else result_map["monthly"]["lp"]
    )

    for hype_address in valid_results:
        output[hype_address] = InternalFeeReturnsOutput(
            symbol=valid_results[hype_address]["symbol"]
        )

        for period_name, period_result in result_map.items():
            if isinstance(period_result, Exception):
                continue
            status_total = period_result["total"][hype_address]["status"]
            status_lp = period_result["lp"][hype_address]["status"]
            setattr(
                output[hype_address],
                period_name,
                InternalFeeYield(
                    totalApr=period_result["total"][hype_address]["feeApr"],
                    totalApy=period_result["total"][hype_address]["feeApy"],
                    lpApr=period_result["lp"][hype_address]["feeApr"],
                    lpApy=period_result["lp"][hype_address]["feeApy"],
                    status=f"Total:{status_total}, LP: {status_lp}",
                ),
            )

    return output
