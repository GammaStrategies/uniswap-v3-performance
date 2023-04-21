import asyncio
from datetime import datetime, timedelta
import logging

from fastapi import Response, status

from database.collection_endpoint import (
    db_allData_manager,
    db_returns_manager,
)
from v3data.common import ExecutionOrderWrapper
from v3data.config import MONGO_DB_URL
from v3data.enums import Chain, Protocol
from v3data.hype_fees.fees import fees_all
from v3data.hype_fees.fees_yield import fee_returns_all
from v3data.hype_fees.impermanent_divergence import impermanent_divergence_all
from v3data.hypervisor import HypervisorInfo, HypervisorData
from v3data.toplevel import TopLevelData

logger = logging.getLogger(__name__)


class AllData(ExecutionOrderWrapper):
    async def _database(self):
        _mngr = db_allData_manager(mongo_url=MONGO_DB_URL)
        result = await _mngr.get_data(chain=self.chain, protocol=self.protocol)
        self.database_datetime = result.pop("datetime", "")
        return result

    async def _subgraph(self):
        hypervisor_info = HypervisorInfo(self.protocol, self.chain)
        return await hypervisor_info.all_data()


class FeeReturns(ExecutionOrderWrapper):
    def __init__(
        self,
        protocol: Protocol,
        chain: Chain,
        days: int,
        current_timestamp: int | None = None,
        response: Response = None,
    ):
        self.days = days
        self.current_timestamp = current_timestamp
        super().__init__(protocol, chain, response)

    async def _database(self):
        returns_manager = db_returns_manager(mongo_url=MONGO_DB_URL)
        result = await returns_manager.get_feeReturns(
            chain=self.chain, protocol=self.protocol, period=self.days
        )
        self.database_datetime = result.pop("datetime", "")
        return result

    async def _subgraph(self):
        return await fee_returns_all(
            protocol=self.protocol,
            chain=self.chain,
            days=self.days,
            current_timestamp=self.current_timestamp,
        )


class HypervisorsReturnsAllPeriods(ExecutionOrderWrapper):
    def __init__(
        self,
        protocol: Protocol,
        chain: Chain,
        hypervisors: list[str] | None = None,
        current_timestamp: int | None = None,
        response: Response = None,
    ):
        self.hypervisors = (
            [hypervisor.lower() for hypervisor in hypervisors] if hypervisors else None
        )
        self.current_timestamp = current_timestamp
        super().__init__(protocol, chain, response)

    async def _database(self):
        average_returns_mngr = db_returns_manager(mongo_url=MONGO_DB_URL)

        av_result = await average_returns_mngr.get_hypervisors_returns_average(
            chain=self.chain, protocol=self.protocol
        )
        if len(av_result) < 0:
            raise Exception

            results_na = {"feeApr": 0, "feeApy": 0, "status": "unavailable on database"}

            result = dict()
            # CONVERT result so is equal to original
            for hypervisor in av_result:
                result[hypervisor["_id"]] = dict()
                try:
                    result[hypervisor["_id"]]["daily"] = {
                        "feeApr": hypervisor["returns"]["1"]["av_feeApr"],
                        "feeApy": hypervisor["returns"]["1"]["av_feeApy"],
                        "status": "database",
                    }
                except Exception:
                    result[hypervisor["_id"]]["daily"] = results_na
                try:
                    result[hypervisor["_id"]]["weekly"] = {
                        "feeApr": hypervisor["returns"]["7"]["av_feeApr"],
                        "feeApy": hypervisor["returns"]["7"]["av_feeApy"],
                        "status": "database",
                    }
                except Exception:
                    result[hypervisor["_id"]]["weekly"] = results_na
                try:
                    result[hypervisor["_id"]]["monthly"] = {
                        "feeApr": hypervisor["returns"]["30"]["av_feeApr"],
                        "feeApy": hypervisor["returns"]["30"]["av_feeApy"],
                        "status": "database",
                    }
                except Exception:
                    result[hypervisor["_id"]]["monthly"] = results_na
                try:
                    result[hypervisor["_id"]]["allTime"] = {
                        "feeApr": hypervisor["returns"]["30"]["av_feeApr"],
                        "feeApy": hypervisor["returns"]["30"]["av_feeApy"],
                        "status": "database",
                    }
                except Exception:
                    result[hypervisor["_id"]]["allTime"] = results_na

            return result

    async def _subgraph(self):
        daily, weekly, monthly = await asyncio.gather(
            fee_returns_all(
                self.protocol, self.chain, 1, self.hypervisors, self.current_timestamp
            ),
            fee_returns_all(
                self.protocol, self.chain, 7, self.hypervisors, self.current_timestamp
            ),
            fee_returns_all(
                self.protocol, self.chain, 30, self.hypervisors, self.current_timestamp
            ),
        )

        results = {}
        for hypervisor_id in daily.keys():
            hypervisor_daily = daily.get(hypervisor_id)
            hypervisor_weekly = weekly.get(hypervisor_id)
            hypervisor_monthly = monthly.get(hypervisor_id)

            symbol = hypervisor_daily.pop("symbol")
            hypervisor_weekly.pop("symbol")
            hypervisor_monthly.pop("symbol")

            if hypervisor_weekly["feeApr"] == 0:
                hypervisor_weekly = hypervisor_daily

            if hypervisor_monthly["feeApr"] == 0:
                hypervisor_monthly = hypervisor_weekly

            results[hypervisor_id] = {"symbol": symbol}
            results[hypervisor_id]["daily"] = hypervisor_daily
            results[hypervisor_id]["weekly"] = hypervisor_weekly
            results[hypervisor_id]["monthly"] = hypervisor_monthly
            results[hypervisor_id]["allTime"] = hypervisor_monthly

        return results


class ImpermanentDivergence(ExecutionOrderWrapper):
    def __init__(
        self,
        protocol: Protocol,
        chain: Chain,
        days: int,
        current_timestamp: int | None = None,
        response: Response = None,
    ):
        self.days = days
        self.current_timestamp = current_timestamp
        super().__init__(protocol, chain, response)

    async def _database(self):
        # check days in database
        if self.days not in [1, 7, 30]:
            raise NotImplementedError("Requested period does not exist in database")
        returns_mngr = db_returns_manager(mongo_url=MONGO_DB_URL)
        return await returns_mngr.get_impermanentDivergence_data(
            chain=self.chain, protocol=self.protocol, period=self.days
        )

    async def _subgraph(self):
        return await impermanent_divergence_all(
            protocol=self.protocol,
            chain=self.chain,
            days=self.days,
            current_timestamp=self.current_timestamp,
        )


async def hypervisor_basic_stats(
    protocol: Protocol, chain: Chain, hypervisor_address: str, response: Response
):
    hypervisor_info = HypervisorInfo(protocol, chain)
    basic_stats = await hypervisor_info.basic_stats(hypervisor_address)

    if basic_stats:
        return basic_stats
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return "Invalid hypervisor address or not enough data"


async def recent_fees(protocol: Protocol, chain: Chain, hours: int = 24):
    top_level = TopLevelData(protocol, chain)
    recent_fees = await top_level.recent_fees(hours)

    return {"periodHours": hours, "fees": recent_fees}


async def hypervisors_average_return(
    protocol: Protocol, chain: Chain, response: Response = None
):
    if response:
        response.headers["X-Database"] = "true"
    average_returns_mngr = db_returns_manager(mongo_url=MONGO_DB_URL)
    return await average_returns_mngr.get_hypervisors_average(
        chain=chain, protocol=protocol
    )


async def hypervisor_average_return(
    protocol: Protocol, chain: Chain, hypervisor_address: str, response: Response = None
):
    if response:
        response.headers["X-Database"] = "true"
    average_returns_mngr = db_returns_manager(mongo_url=MONGO_DB_URL)
    return await average_returns_mngr.get_hypervisor_average(
        chain=chain, hypervisor_address=hypervisor_address, protocol=protocol
    )


async def uncollected_fees(
    protocol: Protocol,
    chain: Chain,
    hypervisor_address: str,
    current_timestamp: int | None = None,
):
    return await fees_all(
        protocol=protocol,
        chain=chain,
        hypervisors=[hypervisor_address],
        current_timestamp=current_timestamp,
    )


async def uncollected_fees_all(
    protocol: Protocol, chain: Chain, current_timestamp: int | None = None
):
    return await fees_all(
        protocol=protocol, chain=chain, current_timestamp=current_timestamp
    )


async def collected_fees(
    protocol: Protocol,
    chain: Chain,
    start_timestamp: int | None = None,
    end_timestamp: int | None = None,
    start_block: int | None = None,
    end_block: int | None = None,
    usd_total_only: bool = False,
) -> dict:
    """Collected fees

    Args:
        protocol (Protocol):
        chain (Chain):
        start_timestamp (int | None, optional): . Defaults to None.
        end_timestamp (int | None, optional): . Defaults to None.
        start_block (int | None, optional): . Defaults to None.
        end_block (int | None, optional): . Defaults to None.
        usd_total_only (bool, optional): return the sum of all period_grossFeesClaimed in usd. Defaults to False.

    Returns:
        dict:
    """
    if (not start_timestamp and not start_block) or (
        not end_timestamp and not end_block
    ):
        current_month_first_day: datetime = datetime.utcnow().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        last_month_first_day: datetime = (
            current_month_first_day - timedelta(days=current_month_first_day.day)
        ).replace(day=1)

        start_date = last_month_first_day
        end_date = (start_date + timedelta(days=33)).replace(
            day=1, hour=0, minute=0, second=0
        )
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())

    hype = HypervisorData(protocol=protocol, chain=chain)
    collected_fees = await hype._get_collected_fees(
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        start_block=start_block,
        end_block=end_block,
    )
    if usd_total_only and collected_fees:
        first_key = next(iter(collected_fees))
        initial_grossFeesClaimedUSD = 0
        end_grossFeesClaimedUSD = 0
        period_grossFeesClaimedUSD = 0
        for k, x in collected_fees.items():
            initial_grossFeesClaimedUSD += x["initial_grossFeesClaimedUSD"]
            end_grossFeesClaimedUSD += x["end_grossFeesClaimedUSD"]
            period_grossFeesClaimedUSD += x["period_grossFeesClaimedUSD"]

        return {
            "initial_block": collected_fees[first_key]["initial_block"],
            "initial_timestamp": collected_fees[first_key]["initial_timestamp"],
            "initial_datetime": datetime.fromtimestamp(
                collected_fees[first_key]["initial_timestamp"]
            ),
            "end_block": collected_fees[first_key]["end_block"],
            "end_timestamp": collected_fees[first_key]["end_timestamp"],
            "end_datetime": datetime.fromtimestamp(
                collected_fees[first_key]["end_timestamp"]
            ),
            "initial_grossFeesClaimedUSD": initial_grossFeesClaimedUSD,
            "end_grossFeesClaimedUSD": end_grossFeesClaimedUSD,
            "period_grossFeesClaimedUSD": period_grossFeesClaimedUSD,
        }
    else:
        return collected_fees
