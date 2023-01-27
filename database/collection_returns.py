import logging
import asyncio

from dataclasses import dataclass, field, asdict, InitVar

from v3data.hypes.impermanent_data import ImpermanentDivergence

from database.common.db_data_models import (
    tool_mongodb_general,
    tool_database_id,
    hypervisor_fees,
    hypervisor_impermanent,
)
from database.collections_common import db_collections_common


@dataclass
class hypervisor_return(tool_mongodb_general, tool_database_id):
    chain: str
    period: str
    address: str
    symbol: str
    block: int
    timestamp: int
    fees: hypervisor_fees = None
    impermanent: hypervisor_impermanent = None

    def create_id(self) -> str:
        return f"{self.chain}_{self.address}_{self.block}_{self.period}"


class db_returns_manager(db_collections_common):
    db_collection_name = "returns"

    # format data to be used with mongo db
    async def create_data(
        self, chain: str, protocol: str, period_days: int
    ) -> dict[str:hypervisor_return]:
        """Create a dictionary of hypervisor_return database models

        Args:
            chain (str): _description_
            protocol (str): _description_
            period_days (int): _description_

        Returns:
            dict:   <hypervisor_id>:<db_data_models.hypervisor_return>
        """
        # define result var
        result = dict()

        # define calculation class
        all_data = ImpermanentDivergence(
            period_days=period_days, protocol=protocol, chain=chain
        )
        # calculate return
        returns_data = await all_data.get_fees_yield(get_data=True)
        # calculate impermanent divergence
        imperm_data = await all_data.get_impermanent_data(get_data=False)

        # get block n timestamp
        block = all_data.data["current_block"]
        timestamp = all_data._block_ts_map[block]

        # fee yield data process
        for k, v in returns_data.items():
            if not k in result.keys():

                result[k] = hypervisor_return(
                    chain=chain,
                    period=period_days,
                    address=k,
                    symbol=v["symbol"],
                    block=block,
                    timestamp=timestamp,
                    fees=hypervisor_fees(
                        feeApr=v["feeApr"],
                        feeApy=v["feeApy"],
                        hasOutlier=v["hasOutlier"],
                    ),
                )

        # impermanent data process
        for k, v in imperm_data.items():
            # only hypervisors with FeeYield data
            if k in result.keys():
                result[k].impermanent = hypervisor_impermanent(
                    vs_hodl_usd=v["vs_hodl_usd"],
                    vs_hodl_deposited=v["vs_hodl_deposited"],
                    vs_hodl_token0=v["vs_hodl_token0"],
                    vs_hodl_token1=v["vs_hodl_token1"],
                )

        return result

    async def feed_db(self, chain: str, protocol: str, periods: list[int] = [1, 7, 30]):

        # TODO: replace hardcoded periods list
        requests = [
            self.save_items_to_database(
                data=await self.create_data(
                    chain=chain, protocol=protocol, period_days=days
                ),
                collection_name=self.db_collection_name,
            )
            for days in periods
        ]

        await asyncio.gather(*requests)

    async def get_data(self, query: list[dict]):
        return self.get_items_from_database(
            query=query, collection_name=self.db_collection_name
        )

    async def get_hypervisors_average(
        self, chain: str, period: int = 0, protocol: str = ""
    ) -> dict:
        return await self.get_data(
            query=self.query_hypervisors_average(
                chain=chain, period=period, protocol=protocol
            )
        )

    async def get_hypervisor_average(
        self, chain: str, hypervisor_address: str, period: int = 0, protocol: str = ""
    ) -> dict:
        return await self.get_data(
            query=self.query_hypervisors_average(
                chain=chain,
                hypervisor_address=hypervisor_address,
                period=period,
                protocol=protocol,
            )
        )

    # TODO: use a limited number of items back? ( $limit )
    @staticmethod
    def query_hypervisors_average(
        chain: str, period: int = 0, protocol: str = "", hypervisor_address: str = ""
    ) -> list[dict]:
        """get all average returns from collection

        Args:
            chain (str): _description_
            period (int, optional): _description_. Defaults to 0.
            protocol (str)
            hypervisor_address (str)

        Returns:
            list[dict]:
                { "_id" = hypervisor address, "hipervisor":{ ... }, "periods": { ... }  }

        """
        # set return match vars
        _returns_match = {"chain": chain}

        if period != 0:
            _returns_match["period"] = period
        if hypervisor_address != "":
            _returns_match["address"] = hypervisor_address

        # set return match vars
        _static_match = dict()
        if protocol != "":
            _static_match["hypervisor.protocol"] = protocol

        # return query
        return [
            {"$match": _returns_match},
            {
                "$project": {
                    "period": "$period",
                    "address": "$address",
                    "hypervisor_id": {"$concat": ["$chain", "_", "$address"]},
                    "timestamp": "$timestamp",
                    "block": "$block",
                    "feeApr": "$fees.feeApr",
                    "feeApy": "$fees.feeApy",
                    "imp_vs_hodl_usd": "$impermanent.vs_hodl_usd",
                    "imp_vs_hodl_deposited": "$impermanent.vs_hodl_deposited",
                    "imp_vs_hodl_token0": "$impermanent.vs_hodl_token0",
                    "imp_vs_hodl_token1": "$impermanent.vs_hodl_token1",
                }
            },
            {
                "$lookup": {
                    "from": "static",
                    "localField": "hypervisor_id",
                    "foreignField": "id",
                    "as": "hypervisor",
                }
            },
            {"$set": {"hypervisor": {"$arrayElemAt": ["$hypervisor", 0]}}},
            {"$match": _static_match},
            {"$sort": {"block": 1}},
            {
                "$project": {
                    "period": "$period",
                    "address": "$address",
                    "timestamp": "$timestamp",
                    "block": "$block",
                    "feeApr": "$feeApr",
                    "feeApy": "$feeApy",
                    "imp_vs_hodl_usd": "$imp_vs_hodl_usd",
                    "imp_vs_hodl_deposited": "$imp_vs_hodl_deposited",
                    "imp_vs_hodl_token0": "$imp_vs_hodl_token0",
                    "imp_vs_hodl_token1": "$imp_vs_hodl_token1",
                    "hypervisor": "$hypervisor",
                }
            },
            {
                "$group": {
                    "_id": {"address": "$address", "period": "$period"},
                    "min_timestamp": {"$min": "$timestamp"},
                    "max_timestamp": {"$max": "$timestamp"},
                    "min_block": {"$min": "$block"},
                    "max_block": {"$max": "$block"},
                    "av_feeApr": {"$avg": "$feeApr"},
                    "av_feeApy": {"$avg": "$feeApy"},
                    "av_imp_vs_hodl_usd": {"$avg": "$imp_vs_hodl_usd"},
                    "av_imp_vs_hodl_deposited": {"$avg": "$imp_vs_hodl_deposited"},
                    "av_imp_vs_hodl_token0": {"$avg": "$imp_vs_hodl_token0"},
                    "av_imp_vs_hodl_token1": {"$avg": "$imp_vs_hodl_token1"},
                    "hypervisor": {"$first": "$hypervisor"},
                }
            },
            {
                "$group": {
                    "_id": "$_id.address",
                    "periods": {
                        "$push": {
                            "k": {"$toString": "$_id.period"},
                            "v": {
                                "period": "$_id.period",
                                "items": "$items",
                                "min_timestamp": "$min_timestamp",
                                "max_timestamp": "$max_timestamp",
                                "min_block": "$min_block",
                                "max_block": "$max_block",
                                "av_feeApr": "$av_feeApr",
                                "av_feeApy": "$av_feeApy",
                                "av_imp_vs_hodl_usd": "$av_imp_vs_hodl_usd",
                                "av_imp_vs_hodl_deposited": "$av_imp_vs_hodl_deposited",
                                "av_imp_vs_hodl_token0": "$av_imp_vs_hodl_token0",
                                "av_imp_vs_hodl_token1": "$imp_vs_hodl_token1",
                            },
                        },
                    },
                    "hypervisor": {"$first": "$hypervisor"},
                }
            },
            {
                "$project": {
                    "_id": "$_id",
                    "hypervisor": {
                        "symbol": "$hypervisor.symbol",
                        "address": "$hypervisor.address",
                        "chain": "$hypervisor.chain",
                        "pool": "$hypervisor.pool",
                        "protocol": "$hypervisor.protocol",
                    },
                    "returns": {"$arrayToObject": "$periods"},
                }
            },
        ]
