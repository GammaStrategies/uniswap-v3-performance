from fastapi import Response, status

from v3data.hypervisor import HypervisorInfo
from v3data.toplevel import TopLevelData
from v3data.hypes.fees import Fees
from v3data.hypes.fees_yield import FeesYield
from v3data.hypes.impermanent_data import ImpermanentDivergence

from database.collection_endpoint import (
    db_returns_manager,
    db_allData_manager,
    db_allRewards2_manager,
    db_static_manager,
    db_aggregateStats_manager,
)
from v3data.config import MONGO_DB_URL

import logging

logger = logging.getLogger(__name__)


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


async def aggregate_stats(protocol: str, chain: str, response: Response = None):

    try:
        _mngr = db_aggregateStats_manager(mongo_url=MONGO_DB_URL)
        result = await _mngr.get_data(chain=chain, protocol=protocol)
        if response:
            response.headers["X-Database"] = "true"
            response.headers["X-Database-itemUpdated"] = "{}".format(
                result.pop("datetime", "")
            )
        return result
    except:
        logger.warning(
            " Could not get database aggregateStats data for {protocol} in {chain}. Return calculated data."
        )
        if response:
            response.headers["X-Database"] = "false"
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


async def hypervisors_return(protocol: str, chain: str, response: Response = None):
    average_returns_mngr = db_returns_manager(mongo_url=MONGO_DB_URL)

    av_result = await average_returns_mngr.get_hypervisors_returns_average(
        chain=chain, protocol=protocol
    )
    if len(av_result) > 0:
        # add request
        if response:
            response.headers["X-Database"] = "true"

        result = dict()
        # CONVERT result so is equal to original
        for hypervisor in av_result:

            result[hypervisor["_id"]] = dict()
            try:
                result[hypervisor["_id"]]["daily"] = {
                    "totalPeriodSeconds": hypervisor["returns"]["1"]["max_timestamp"]
                    - hypervisor["returns"]["1"]["min_timestamp"],
                    "cumFeeReturn": 0,
                    "feeApr": hypervisor["returns"]["1"]["av_feeApr"],
                    "feeApy": hypervisor["returns"]["1"]["av_feeApy"],
                }
            except:
                result[hypervisor["_id"]]["daily"] = {
                    "totalPeriodSeconds": 0,
                    "cumFeeReturn": 0,
                    "feeApr": 0,
                    "feeApy": 0,
                }
            try:
                result[hypervisor["_id"]]["weekly"] = {
                    "totalPeriodSeconds": hypervisor["returns"]["7"]["max_timestamp"]
                    - hypervisor["returns"]["7"]["min_timestamp"],
                    "cumFeeReturn": 0,
                    "feeApr": hypervisor["returns"]["7"]["av_feeApr"],
                    "feeApy": hypervisor["returns"]["7"]["av_feeApy"],
                }
            except:
                result[hypervisor["_id"]]["weekly"] = {
                    "totalPeriodSeconds": 0,
                    "cumFeeReturn": 0,
                    "feeApr": 0,
                    "feeApy": 0,
                }
            try:
                result[hypervisor["_id"]]["monthly"] = {
                    "totalPeriodSeconds": hypervisor["returns"]["30"]["max_timestamp"]
                    - hypervisor["returns"]["30"]["min_timestamp"],
                    "cumFeeReturn": 0,
                    "feeApr": hypervisor["returns"]["30"]["av_feeApr"],
                    "feeApy": hypervisor["returns"]["30"]["av_feeApy"],
                }
            except:
                result[hypervisor["_id"]]["monthly"] = {
                    "totalPeriodSeconds": 0,
                    "cumFeeReturn": 0,
                    "feeApr": 0,
                    "feeApy": 0,
                }
            try:
                result[hypervisor["_id"]]["allTime"] = {
                    "totalPeriodSeconds": hypervisor["returns"]["30"]["max_timestamp"]
                    - hypervisor["returns"]["30"]["min_timestamp"],
                    "cumFeeReturn": 0,
                    "feeApr": hypervisor["returns"]["30"]["av_feeApr"],
                    "feeApy": hypervisor["returns"]["30"]["av_feeApy"],
                }
            except:
                result[hypervisor["_id"]]["allTime"] = {
                    "totalPeriodSeconds": 0,
                    "cumFeeReturn": 0,
                    "feeApr": 0,
                    "feeApy": 0,
                }
        return result

    else:
        # no database result
        if response:
            response.headers["X-Database"] = "false"
        logger.warning(" falling back to original returns result [using rebalances]")
        hypervisor_info = HypervisorInfo(protocol, chain)
        return await hypervisor_info.all_returns()


async def hypervisors_average_return(
    protocol: str, chain: str, response: Response = None
):
    if response:
        response.headers["X-Database"] = "true"
    average_returns_mngr = db_returns_manager(mongo_url=MONGO_DB_URL)
    return await average_returns_mngr.get_hypervisors_average(
        chain=chain, protocol=protocol
    )


async def hypervisor_average_return(
    protocol: str, chain: str, hypervisor_address: str, response: Response = None
):
    if response:
        response.headers["X-Database"] = "true"
    average_returns_mngr = db_returns_manager(mongo_url=MONGO_DB_URL)
    return await average_returns_mngr.get_hypervisor_average(
        chain=chain, hypervisor_address=hypervisor_address, protocol=protocol
    )


async def hypervisors_all(protocol: str, chain: str, response: Response = None):
    try:
        # Database result
        _mngr = db_allData_manager(mongo_url=MONGO_DB_URL)
        result = await _mngr.get_data(chain=chain, protocol=protocol)
        if response:
            response.headers["X-Database"] = "true"
            response.headers["X-Database-itemUpdated"] = "{}".format(
                result.pop("datetime", "")
            )
        return result
    except:
        # Calculated result
        logger.warning(
            " Could not get database allData for {protocol} in {chain}. Return calculated data."
        )
        if response:
            response.headers["X-Database"] = "false"
        hypervisor_info = HypervisorInfo(protocol, chain)
        return await hypervisor_info.all_data()


async def uncollected_fees(protocol: str, chain: str, hypervisor_address: str):
    fees = Fees(protocol, chain)
    return await fees.output([hypervisor_address])


async def uncollected_fees_all(protocol: str, chain: str):
    fees = Fees(protocol, chain)
    return await fees.output()


async def fee_returns(protocol: str, chain: str, days: int):
    fees_yield = FeesYield(days, protocol, chain)
    output = await fees_yield.get_fees_yield()
    return output


async def impermanent_divergence(protocol: str, chain: str, days: int):
    impermanent_manager = ImpermanentDivergence(
        period_days=days, protocol=protocol, chain=chain
    )
    output = await impermanent_manager.get_impermanent_data()
    return output
