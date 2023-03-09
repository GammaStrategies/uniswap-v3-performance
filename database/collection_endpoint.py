import logging
import asyncio
import sys
from datetime import datetime

from v3data.hypervisor import HypervisorInfo, HypervisorData
from v3data.masterchef_v2 import MasterchefV2Info
from v3data.hype_fees.data import FeeGrowthSnapshotData
from v3data.hype_fees.fees_yield import FeesYield
from v3data.hype_fees.impermanent_divergence import impermanent_divergence_all
from v3data.toplevel import TopLevelData
from v3data.enums import Chain, Protocol

from database.common.collections_common import db_collections_common

logger = logging.getLogger(__name__)


class db_collection_manager(db_collections_common):
    db_collection_name = ""

    async def feed_db(self, chain: Chain, protocol: Protocol):
        try:
            await self.save_items_to_database(
                data=await self.create_data(chain=chain, protocol=protocol),
                collection_name=self.db_collection_name,
            )
        except:
            logger.warning(
                f" Unexpected error feeding {chain}'s {protocol} database  err:{sys.exc_info()[0]}"
            )

    async def _get_data(self, query: list[dict]):
        return await self.query_items_from_database(
            query=query, collection_name=self.db_collection_name
        )


class db_static_manager(db_collection_manager):
    db_collection_name = "static"

    async def create_data(self, chain: Chain, protocol: Protocol) -> dict:
        """Create a dictionary of hypervisor_static database models

        Args:
            chain (str): _description_
            protocol (str): _description_

        Returns:
            dict: <hypervisor_id>:<db_data_models.hypervisor_static>
        """
        # define result var
        result = dict()
        hypervisors_data = HypervisorData(protocol=protocol, chain=chain)
        # get all hypervisors & their pools data

        await hypervisors_data._get_all_data()

        for hypervisor in hypervisors_data.basics_data:
            # temporal vars
            address = hypervisor["id"]
            hypervisor_name = f'{hypervisor["pool"]["token0"]["symbol"]}-{hypervisor["pool"]["token1"]["symbol"]}-{hypervisor["pool"]["fee"]}'

            _tokens = [
                {
                    "address": hypervisor["pool"]["token0"]["id"],
                    "symbol": hypervisor["pool"]["token0"]["symbol"],
                    "position": 0,
                },
                {
                    "address": hypervisor["pool"]["token1"]["id"],
                    "symbol": hypervisor["pool"]["token1"]["symbol"],
                    "position": 1,
                },
            ]
            _pool = {
                "address": hypervisor["pool"]["id"],
                "fee": hypervisor["pool"]["fee"],
                "tokens": _tokens,
            }

            # add to result
            result[address] = {
                "id": f"{chain}_{address}",
                "chain": chain,
                "address": address,
                "symbol": hypervisor_name,
                "protocol": protocol,
                "created": hypervisor["created"],
                "pool": _pool,
            }

        return result


class db_returns_manager(db_collection_manager):
    """This is managing database with fee Return and Impermanent divergence data

    returns data is collected from <get_fees_yield> so it is using uncollected fees to return %
    impermanent data is collected from <get_impermanent_data>

    """

    db_collection_name = "returns"

    # format data to be used with mongo db
    async def create_data(
        self, chain: Chain, protocol: Protocol, period_days: int
    ) -> dict:
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

        # calculate return
        fees_data = FeeGrowthSnapshotData(period_days, protocol, chain)
        await fees_data.get_data()

        returns_data = {}
        for hypervisor_id, fees_data in fees_data.data.items():
            fees_yield = FeesYield(fees_data, protocol, chain)
            returns = fees_yield.calculate_returns()
            returns_data[hypervisor_id] = returns

        # calculate impermanent divergence
        imperm_data = await impermanent_divergence_all(
            protocol=protocol, chain=chain, days=period_days
        )

        # get block n timestamp
        block = fees_data.data[0].block
        timestamp = fees_data.data[0].timestamp

        # fee yield data process
        for k, v in returns_data.items():
            if k not in result.keys():
                # set the database unique id
                database_id = f"{chain}_{k}_{block}_{period_days}"

                result[k] = {
                    "id": database_id,
                    "chain": chain,
                    "period": period_days,
                    "address": k,
                    "symbol": v.symbol,
                    "block": block,
                    "timestamp": timestamp,
                    "fees": {
                        "feeApr": v.feeApr,
                        "feeApy": v.feeApy,
                        "status": v.status,
                    },
                }

        # impermanent data process
        for k, v in imperm_data.items():
            # only hypervisors with FeeYield data
            if k in result.keys():
                result[k]["impermanent"] = {
                    "vs_hodl_usd": v["vs_hodl_usd"],
                    "vs_hodl_deposited": v["vs_hodl_deposited"],
                    "vs_hodl_token0": v["vs_hodl_token0"],
                    "vs_hodl_token1": v["vs_hodl_token1"],
                }

        return result

    async def feed_db(
        self, chain: Chain, protocol: Protocol, periods: list[int] = [1, 7, 30]
    ):

        try:
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
        except:
            logger.warning(
                f" Unexpected error feeding {chain}'s {protocol} returns to db   err:{sys.exc_info()[0]}"
            )

    async def get_hypervisors_average(
        self, chain: Chain, period: int = 0, protocol: Protocol = ""
    ) -> dict:
        result = await self._get_data(
            query=self.query_hypervisors_average(
                chain=chain, period=period, protocol=protocol
            )
        )
        try:
            return result
        except:
            return {}

    async def get_hypervisors_returns_average(
        self, chain: Chain, period: int = 0, protocol: Protocol = ""
    ) -> dict:
        result = await self._get_data(
            query=self.query_hypervisors_returns_average(
                chain=chain, period=period, protocol=protocol
            )
        )
        try:
            return result
        except:
            return {}

    async def get_hypervisor_average(
        self,
        chain: Chain,
        hypervisor_address: str,
        period: int = 0,
        protocol: Protocol = "",
    ) -> dict:
        result = await self._get_data(
            query=self.query_hypervisors_average(
                chain=chain,
                hypervisor_address=hypervisor_address,
                period=period,
                protocol=protocol,
            )
        )
        try:
            return result
        except:
            return {}

    async def get_feeReturns(
        self,
        chain: Chain,
        protocol: Protocol,
        period: int,
        hypervisor_address: str = "",
    ) -> dict:

        # query database
        dbdata = await self._get_data(
            query=self.query_last_returns(
                chain=chain,
                protocol=protocol,
                period=period,
                hypervisor_address=hypervisor_address,
            )
        )
        # set database last update field as the maximum date found within the items returned
        try:
            db_lastUpdate = max([x["timestamp"] for x in dbdata])
        except:
            # TODO: log error
            db_lastUpdate = datetime.utcnow().timestamp()

        # init result
        result = dict()
        # convert result to dict
        for item in dbdata:
            address = item.pop("address")
            result[address] = item

        # add database last update datetime
        result["datetime"] = datetime.fromtimestamp(db_lastUpdate)

        return result

    async def get_returns(
        self, chain: Chain, protocol: Protocol, hypervisor_address: str = ""
    ) -> dict:

        # query database
        result = await self._get_data(
            query=self.query_last_returns(
                chain=chain,
                protocol=protocol,
                hypervisor_address=hypervisor_address,
            )
        )
        # set database last update field as the maximum date found within the items returned
        try:
            db_lastUpdate = max([x["timestamp"] for x in result])
        except:
            # TODO: log error
            db_lastUpdate = datetime.utcnow().timestamp()

        # convert result to dict
        result = {
            x["_id"]: {
                "daily": x["daily"],
                "weekly": x["weekly"],
                "monthly": x["monthly"],
                "allTime": x["allTime"],
            }
            for x in result
        }
        result["datetime"] = datetime.fromtimestamp(db_lastUpdate)

        return result

    # TODO: use a limited number of items back? ( $limit )
    # TODO: return dict item with hypervisor id's as keys and 1 item list only ... to match others
    @staticmethod
    def query_hypervisors_average(
        chain: Chain,
        period: int = 0,
        protocol: Protocol = "",
        hypervisor_address: str = "",
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
                                "av_imp_vs_hodl_token1": "$av_imp_vs_hodl_token1",
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

    @staticmethod
    def query_hypervisors_returns_average(
        chain: Chain,
        period: int = 0,
        protocol: Protocol = "",
        hypervisor_address: str = "",
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
        _returns_match = {
            "chain": chain,
            "$and": [{"fees.feeApr": {"$gt": 0}}, {"fees.feeApr": {"$lt": 8}}],
            "$and": [{"fees.feeApy": {"$gt": 0}}, {"fees.feeApy": {"$lt": 8}}],
        }

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

    @staticmethod
    def query_last_returns(
        chain: Chain,
        period: int = 0,
        protocol: Protocol = "",
        hypervisor_address: str = "",
    ) -> list[dict]:
        """return the last items found not zero lower than 800% apy apr :
                daily, weekly and monthly apr apy ( alltime is the monthly figure)

        Args:
            chain (str):
            period (int, optional): . Defaults to 0.
            protocol (str, optional): . Defaults to "".
            hypervisor_address (str, optional): . Defaults to "".

        Returns:
            list[dict]:
                        when period == default {
                                                "_id" : "0xeb7d263db66aab4d5ee903a949a5a54c287bec87",
                                                "daily" : {
                                                    "feeApr" : 0.0173442096430378,
                                                    "feeApy" : 0.017495074535651,
                                                    "hasOutlier" : "False",
                                                    "symbol" : "WMATIC-stMATIC-0"
                                                },
                                                "weekly" : {
                                                    "feeApr" : 0.00174322708835021,
                                                    "feeApy" : 0.00174474322190754,
                                                    "hasOutlier" : "False",
                                                    "symbol" : "WMATIC-stMATIC-0"
                                                },
                                                "monthly" : {
                                                    "feeApr" : 0.00134238749591191,
                                                    "feeApy" : 0.00134328642948756,
                                                    "hasOutlier" : "False",
                                                    "symbol" : "WMATIC-stMATIC-0"
                                                },
                                                "allTime" : {
                                                    "feeApr" : 0.00134238749591191,
                                                    "feeApy" : 0.00134328642948756,
                                                    "hasOutlier" : "False",
                                                    "symbol" : "WMATIC-stMATIC-0"
                                                }
                                            }

                        when period != 0 {
                                        "address" : "0xf874d4957861e193aec9937223062679c14f9aca",
                                        "timestamp" : 1675329215,
                                        "block" : 38817275,
                                        "feeApr" : 0.0560324909858921,
                                        "feeApy" : 0.0576274984164038,
                                        "hasOutlier" : "False",
                                        "symbol" : "WMATIC-WETH-500"
                                        }
        """

        # set return match vars
        _returns_match = {
            "chain": chain,
            "$and": [{"fees.feeApr": {"$gt": 0}}, {"fees.feeApr": {"$lt": 8}}],
            "$and": [{"fees.feeApy": {"$gt": 0}}, {"fees.feeApy": {"$lt": 8}}],
        }

        if period != 0:
            _returns_match["period"] = period
        if hypervisor_address != "":
            _returns_match["address"] = hypervisor_address

        # set return match vars
        _static_match = dict()
        if protocol != "":
            _static_match["hypervisor.protocol"] = protocol

        # will return a list of:
        # {
        #     "_id" : "0xeb7d263db66aab4d5ee903a949a5a54c287bec87",
        #     "daily" : {
        #         "feeApr" : 0.0173442096430378,
        #         "feeApy" : 0.017495074535651,
        #         "hasOutlier" : "False",
        #         "symbol" : "WMATIC-stMATIC-0"
        #     },
        #     "weekly" : {
        #         "feeApr" : 0.00174322708835021,
        #         "feeApy" : 0.00174474322190754,
        #         "hasOutlier" : "False",
        #         "symbol" : "WMATIC-stMATIC-0"
        #     },
        #     "monthly" : {
        #         "feeApr" : 0.00134238749591191,
        #         "feeApy" : 0.00134328642948756,
        #         "hasOutlier" : "False",
        #         "symbol" : "WMATIC-stMATIC-0"
        #     },
        #     "allTime" : {
        #         "feeApr" : 0.00134238749591191,
        #         "feeApy" : 0.00134328642948756,
        #         "hasOutlier" : "False",
        #         "symbol" : "WMATIC-stMATIC-0"
        #     }
        # }
        returns_all_periods = [
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
                    "status": "$fees.status",
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
                    "status": "$status",
                    "symbol": "$hypervisor.symbol",
                }
            },
            {
                "$group": {
                    "_id": {"address": "$address", "period": "$period"},
                    "items": {"$push": "$$ROOT"},
                }
            },
            {
                "$group": {
                    "_id": "$_id.address",
                    "periods": {
                        "$push": {
                            "k": {"$toString": "$_id.period"},
                            "v": {"$last": "$items"},
                        },
                    },
                }
            },
            {
                "$project": {
                    "_id": "$_id",
                    "returns": {"$arrayToObject": "$periods"},
                }
            },
            {
                "$addFields": {
                    "daily": {
                        "feeApr": "$returns.1.feeApr",
                        "feeApy": "$returns.1.feeApy",
                        "status": "$returns.1.status",
                        "symbol": "$returns.1.symbol",
                    },
                    "weekly": {
                        "feeApr": "$returns.7.feeApr",
                        "feeApy": "$returns.7.feeApy",
                        "status": "$returns.7.status",
                        "symbol": "$returns.7.symbol",
                    },
                    "monthly": {
                        "feeApr": "$returns.30.feeApr",
                        "feeApy": "$returns.30.feeApy",
                        "status": "$returns.30.status",
                        "symbol": "$returns.30.symbol",
                    },
                    "allTime": {
                        "feeApr": "$returns.30.feeApr",
                        "feeApy": "$returns.30.feeApy",
                        "status": "$returns.30.status",
                        "symbol": "$returns.30.symbol",
                    },
                }
            },
            {"$unset": ["returns"]},
        ]

        # will return a list of {
        #     "address" : "0xf874d4957861e193aec9937223062679c14f9aca",
        #     "timestamp" : 1675329215,
        #     "block" : 38817275,
        #     "feeApr" : 0.0560324909858921,
        #     "feeApy" : 0.0576274984164038,
        #     "hasOutlier" : "False",
        #     "symbol" : "WMATIC-WETH-500"
        # }
        returns_by_period = [
            {"$match": _returns_match},
            {
                "$project": {
                    "address": "$address",
                    "hypervisor_id": {"$concat": ["$chain", "_", "$address"]},
                    "timestamp": "$timestamp",
                    "block": "$block",
                    "feeApr": "$fees.feeApr",
                    "feeApy": "$fees.feeApy",
                    "status": "$fees.status",
                    "block": "$block",
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
            {"$sort": {"block": -1}},
            {
                "$project": {
                    "address": "$address",
                    "timestamp": "$timestamp",
                    "block": "$block",
                    "feeApr": "$feeApr",
                    "feeApy": "$feeApy",
                    "status": "$status",
                    "symbol": "$hypervisor.symbol",
                }
            },
            {
                "$group": {
                    "_id": "$address",
                    "items": {"$first": "$$ROOT"},
                }
            },
            {"$replaceRoot": {"newRoot": "$items"}},
            {"$unset": ["_id"]},
        ]

        if period != 0:
            return returns_by_period
        else:
            return returns_all_periods


class db_allData_manager(db_collection_manager):
    db_collection_name = "allData"

    async def create_data(self, chain: Chain, protocol: Protocol) -> dict:
        """Create a dictionary of hypervisor_allData database models

        Args:
            chain (str): _description_
            protocol (str): _description_

        Returns:
            dict: <hypervisor_id>:<db_data_models.hypervisor_static>
        """
        # define result var
        result = dict()
        hypervisor_info = HypervisorInfo(protocol=protocol, chain=chain)
        allData = await hypervisor_info.all_data()

        # types conversion
        for hyp_id, hypervisor in allData.items():
            hypervisor["totalSupply"] = str(hypervisor["totalSupply"])
            hypervisor["maxTotalSupply"] = str(hypervisor["maxTotalSupply"])
            # hypervisor["id"] = hyp_id

        # add id and datetime to data
        allData["id"] = f"{chain}_{protocol}"
        allData["datetime"] = datetime.utcnow()

        return allData

    async def feed_db(self, chain: Chain, protocol: Protocol):
        try:
            # save as 1 item ( not separated)
            await self.save_item_to_database(
                data=await self.create_data(chain=chain, protocol=protocol),
                collection_name=self.db_collection_name,
            )
        except:
            logger.warning(
                f" Unexpected error feeding  {chain}'s {protocol} allData to db   err:{sys.exc_info()[0]}"
            )

    async def get_data(self, chain: Chain, protocol: Protocol) -> dict:
        result = await self._get_data(
            query=self.query_all(chain=chain, protocol=protocol)
        )
        try:
            return result[0]
        except:
            return {}

    @staticmethod
    def query_all(chain: Chain, protocol: Protocol = "") -> list[dict]:
        """
        Args:
            chain (str): _description_
            protocol (str)

        Returns:
            list[dict]:

        """
        # set return match vars
        _match = {"id": f"{chain}_{protocol}"}

        # return query
        return [{"$match": _match}, {"$unset": ["_id", "id"]}]


class db_allRewards2_manager(db_collection_manager):
    db_collection_name = "allRewards2"

    async def create_data(self, chain: Chain, protocol: Protocol) -> dict:
        """

        Args:
            chain (str): _description_
            protocol (str): _description_

        Returns:
            dict:
        """
        # define result var
        data = dict()
        try:
            masterchef_info = MasterchefV2Info(protocol=protocol, chain=chain)
            data = await masterchef_info.output(get_data=True)
        except:
            # some pools do not have Masterchef info
            pass

        # add id and datetime to data
        data["datetime"] = datetime.utcnow()
        # get timestamp without decimals
        timestamp = int(datetime.timestamp(data["datetime"]))
        # set id
        data["id"] = f"{timestamp}_{chain}_{protocol}"
        # identify data
        data["chain"] = chain
        data["protocol"] = protocol

        return data

    async def feed_db(self, chain: Chain, protocol: Protocol):
        try:

            # save as 1 item ( not separated)
            await self.save_item_to_database(
                data=await self.create_data(chain=chain, protocol=protocol),
                collection_name=self.db_collection_name,
            )
        except:
            logger.warning(
                f" Unexpected error feeding  {chain}'s {protocol} allRewards2 to db   err:{sys.exc_info()[0]}"
            )

    async def get_data(self, chain: Chain, protocol: Protocol) -> dict:
        result = await self._get_data(
            query=self.query_all(chain=chain, protocol=protocol)
        )
        try:
            return result[0]
        except:
            return {}

    async def get_last_data(self, chain: Chain, protocol: Protocol) -> dict:
        """Retrieve last chain+protocol data available at database

        Args:
            chain (str):
            protocol (str):

        Returns:
            dict:
        """
        result = await self._get_data(
            query=self.query_last(chain=chain, protocol=protocol)
        )

        try:
            return result[0]
        except:
            return {}

    @staticmethod
    def query_all(chain: Chain, protocol: Protocol = "") -> list[dict]:
        """
        Args:
            chain (str): _description_
            protocol (str)

        Returns:
            list[dict]:

        """
        # set return match vars
        _match = {"id": f"{chain}_{protocol}"}

        # return query
        return [{"$match": _match}, {"$unset": ["_id", "id"]}]

    @staticmethod
    def query_last(chain: Chain, protocol: Protocol) -> list[str]:
        # set return match vars
        _match = {"chain": chain, "protocol": protocol}

        return [
            {"$match": _match},
            {"$sort": {"datetime": -1}},
            {"$limit": 3},
            {"$unset": ["_id", "id", "chain", "protocol"]},
        ]


class db_aggregateStats_manager(db_collection_manager):
    db_collection_name = "agregateStats"

    async def create_data(self, chain: Chain, protocol: Protocol) -> dict:
        """

        Args:
            chain (str): _description_
            protocol (str): _description_

        Returns:
            dict:
        """

        top_level = TopLevelData(protocol=protocol, chain=chain)
        top_level_data = await top_level.all_stats()

        dtime = datetime.utcnow()
        return {
            "id": f"{chain}_{protocol}_{dtime.timestamp()}",
            "chain": chain,
            "protocol": protocol,
            "datetime": dtime,
            "totalValueLockedUSD": top_level_data["tvl"],
            "pairCount": top_level_data["hypervisor_count"],
            "totalFeesClaimedUSD": top_level_data["fees_claimed"],
        }

    async def feed_db(self, chain: Chain, protocol: Protocol):
        try:
            # save as 1 item ( not separated)
            await self.save_item_to_database(
                data=await self.create_data(chain=chain, protocol=protocol),
                collection_name=self.db_collection_name,
            )
        except:
            logger.warning(
                f" Unexpected error feeding  {chain}'s {protocol} aggregateStats to db   err:{sys.exc_info()[0]}"
            )

    async def get_data(self, chain: Chain, protocol: Protocol) -> dict:
        result = await self._get_data(
            query=self.query_last(chain=chain, protocol=protocol)
        )
        try:
            return result[0]
        except:
            return {}

    @staticmethod
    def query_last(chain: Chain, protocol: Protocol = "") -> list[dict]:
        """Query last item ( highest datetime )
        Args:
            chain (str):
            protocol (str)

        Returns:
            list[dict]:

        """
        # set return match vars
        _match = {"chain": chain, "protocol": protocol}

        # return query
        return [
            {"$match": _match},
            {"$sort": {"datetime": -1}},
            {"$unset": ["_id", "id", "chain", "protocol"]},
        ]
