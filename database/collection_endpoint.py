import logging
import asyncio
import sys
from datetime import datetime, timezone
from v3data.hypervisor import HypervisorInfo, HypervisorData
from v3data.masterchef_v2 import MasterchefV2Info
from v3data.hype_fees.data import FeeGrowthSnapshotData
from v3data.hype_fees.fees_yield import FeesYield
from v3data.hype_fees.impermanent_divergence import impermanent_divergence_all
from v3data.toplevel import TopLevelData
from v3data.enums import Chain, Protocol

from v3data.config import GQL_CLIENT_TIMEOUT, MASTERCHEF_ADDRESSES

from database.common.collections_common import db_collections_common

logger = logging.getLogger(__name__)


class db_collection_manager(db_collections_common):
    def __init__(
        self,
        mongo_url: str,
        db_name: str,
        db_collections: dict,
    ):
        self.db_collection_name = ""
        # self.db_name = "gamma_db_v1"

        super().__init__(
            mongo_url=mongo_url, db_name=db_name, db_collections=db_collections
        )

    async def feed_db(self, chain: Chain, protocol: Protocol):
        try:
            await self.save_items_to_database(
                data=await self.create_data(chain=chain, protocol=protocol),
                collection_name=self.db_collection_name,
            )
        except Exception:
            logger.warning(
                f" Unexpected error feeding {chain}'s {protocol} database  err:{sys.exc_info()[0]}"
            )

    async def _get_data(self, query: list[dict]):
        return await self.query_items_from_database(
            query=query, collection_name=self.db_collection_name
        )


# gamma_v1 database related classes


class db_static_manager(db_collection_manager):
    def __init__(self, mongo_url: str):
        # Create a dictionary of collections
        self.db_collections = {"static": {"id": True}}  # no historical data}
        # Set the database name
        self.db_name = "gamma_db_v1"

        super().__init__(
            mongo_url=mongo_url,
            db_name=self.db_name,
            db_collections=self.db_collections,
        )

        # Set the collection to static, which is the name of the collection in the database
        self.db_collection_name = "static"

    async def create_data(self, chain: Chain, protocol: Protocol) -> dict:
        """Create a dictionary of hypervisor_static database models

        Args:
            chain (str): _description_
            protocol (str): _description_

        Returns:
            dict: <hypervisor_id>:<db_data_models.hypervisor_static>
        """
        # define result var
        result = {}
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

    async def get_hypervisors_address_list(
        self, chain: Chain, protocol: Protocol = None
    ) -> list:
        _find = {"chain": chain}
        if protocol:
            _find["protocol"] = protocol

        try:
            return await self.get_distinct_items_from_database(
                field="address",
                collection_name=self.db_collection_name,
                condition=_find,
            )
        except Exception:
            return []

    async def get_hypervisors(self, chain: Chain, protocol: Protocol = None) -> list:
        _find = {"chain": chain}
        if protocol:
            _find["protocol"] = protocol

        try:
            return await self.get_items_from_database(
                collection_name=self.db_collection_name,
                find=_find,
            )
        except Exception:
            return []


class db_returns_manager(db_collection_manager):
    """This is managing database with fee Return and Impermanent divergence data

    returns data is collected from <get_fees_yield> so it is using uncollected fees to return %
    impermanent data is collected from <get_impermanent_data>

    """

    def __init__(self, mongo_url: str):
        # Create a dictionary of collections
        self.db_collections = {
            "returns": {"id": True},
            "static": {"id": True},
            "allRewards2": {"id": True},
        }
        # Set the database name
        self.db_name = "gamma_db_v1"

        super().__init__(
            mongo_url=mongo_url,
            db_name=self.db_name,
            db_collections=self.db_collections,
        )

        # Set the collection to returns, which is the name of the collection in the database
        self.db_collection_name = "returns"
        self._max_retry = 1

    # format data to be used with mongo db
    async def create_data(
        self,
        chain: Chain,
        protocol: Protocol,
        period_days: int,
        current_timestamp: int = None,
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
        result = {}

        # calculate return
        fees_data = FeeGrowthSnapshotData(protocol, chain)
        await fees_data.init_time(days_ago=period_days, end_timestamp=current_timestamp)
        await fees_data.get_data()

        returns_data = {}
        for hypervisor_id, fees_data_item in fees_data.data.items():
            fees_yield = FeesYield(fees_data_item, protocol, chain)
            returns = fees_yield.calculate_returns()
            returns_data[hypervisor_id] = returns

        # calculate impermanent divergence
        imperm_data = await impermanent_divergence_all(
            protocol=protocol,
            chain=chain,
            days=period_days,
            current_timestamp=fees_data.time_range.end.timestamp,
        )

        # get block n timestamp
        block = fees_data.time_range.end.block
        timestamp = fees_data.time_range.end.timestamp

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
                    "block": block,
                    "timestamp": timestamp,
                    "fees": {
                        "feeApr": v.apr,
                        "feeApy": v.apy,
                        "status": v.status,
                    },
                }

        # impermanent data process
        for k, v in imperm_data.items():
            # only hypervisors with FeeYield data
            if k in result:
                # add symbol
                result[k]["symbol"] = v["symbol"]
                # add impermanent
                result[k]["impermanent"] = {
                    # "ini_block": v["ini_block"],
                    # "end_block": v["end_block"],
                    # "ini_timestamp": v["ini_timestamp"],
                    # "end_timestamp": v["end_timestamp"],
                    "lping": v["lping"],
                    "hodl_deposited": v["hodl_deposited"],
                    "hodl_fifty": v["hodl_fifty"],
                    "hodl_token0": v["hodl_token0"],
                    "hodl_token1": v["hodl_token1"],
                }

        return result

    async def feed_db(
        self,
        chain: Chain,
        protocol: Protocol,
        periods: list[int] = None,
        retried: int = 0,
        current_timestamp: int = None,
    ):
        """
        Args:
            chain (Chain):
            protocol (Protocol):
            periods (list[int], optional): . Defaults to [1, 7, 14, 30].
            retried (int, optional): current number of retries . Defaults to 0.
        """
        # set default periods
        if not periods:
            periods = [1, 7, 14, 30]

        # create data
        try:
            requests = [
                self.save_items_to_database(
                    data=await self.create_data(
                        chain=chain,
                        protocol=protocol,
                        period_days=days,
                        current_timestamp=current_timestamp,
                    ),
                    collection_name=self.db_collection_name,
                )
                for days in periods
            ]

            await asyncio.gather(*requests)

        except Exception as err:
            # retry when possible
            if retried < self._max_retry:
                # wait jic
                await asyncio.sleep(2)
                logger.info(
                    f" Retrying the feeding of {chain}'s {protocol} returns to db for the {retried+1} time."
                )
                # retry
                await self.feed_db(
                    chain=chain,
                    protocol=protocol,
                    periods=periods,
                    retried=retried + 1,
                    current_timestamp=current_timestamp,
                )
            elif err:
                # {'message': 'Failed to decode `block.number` value: `subgraph QmXUphAvAEiGcTzdopmaEt8YDxZ2uEmLJcCQGcfaDvRhp2 only has data starting at block number 63562887 and data for block number 50084142 is therefore not available`'}
                logger.debug(
                    f" Can't feed database {chain}'s {protocol} returns to db  err:{err.args[0]}. Retries: {retried}."
                )
            else:
                logger.exception(
                    f" Unexpected error feeding {chain}'s {protocol} returns to db  err:{sys.exc_info()[0]}. Retries: {retried}."
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
        except Exception:
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
        except Exception:
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
        except Exception:
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
            db_lastUpdate = max(x["timestamp"] for x in dbdata)
        except Exception:
            # TODO: log error
            db_lastUpdate = datetime.now(timezone.utc).timestamp()

        # init result
        result = {}
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
            db_lastUpdate = max(x["timestamp"] for x in result)
        except Exception:
            # TODO: log error
            db_lastUpdate = datetime.now(timezone.utc).timestamp()

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

    async def get_impermanentDivergence_data(
        self,
        chain: Chain,
        protocol: Protocol,
        period: int,
    ) -> dict:
        # query database
        dbdata = await self._get_data(
            query=self.query_impermanentDivergence(
                chain=chain,
                protocol=protocol,
                period=period,
            )
        )
        # set database last update field as the maximum date found within the items returned
        try:
            db_lastUpdate = max([x["timestamp"] for x in dbdata])
        except Exception:
            # TODO: log error
            db_lastUpdate = datetime.utcnow().timestamp()

        # init result
        result = dict()
        # convert result to dict
        for item in dbdata:
            address = item.pop("address")
            result[address] = {
                "id": address,
                "symbol": item["symbol"],
                "lping": item["lping"],
                "hodl_deposited": item["hodl_deposited"],
                "hodl_fifty": item["hodl_fifty"],
                "hodl_token0": item["hodl_token0"],
                "hodl_token1": item["hodl_token1"],
            }

        # add database last update datetime
        result["datetime"] = datetime.fromtimestamp(db_lastUpdate)

        return result

    async def get_analytics_data(
        self,
        chain: Chain,
        hypervisor_address: str,
        period: int,
        ini_date: datetime,
        end_date: datetime,
    ) -> list:
        return await self._get_data(
            query=self.query_return_imperm_rewards2_flat(
                chain=chain,
                hypervisor_address=hypervisor_address,
                period=period,
                ini_date=ini_date,
                end_date=end_date,
            )
        )

    async def get_analytics_data_variation(
        self,
        chain: Chain,
        hypervisor_address: str,
        period: int,
        ini_date: datetime,
        end_date: datetime,
    ) -> list:
        result = []
        last_row = None
        for idx, row in enumerate(
            await self._get_analytics_data(
                chain=chain,
                hypervisor_address=hypervisor_address,
                period=period,
                ini_date=ini_date,
                end_date=end_date,
            )
        ):
            if idx == 0:
                result.append({k: 0 for k, v in row.items()})
            else:
                result.append({k: v - last_row[k] for k, v in row.items()})
            last_row = row
        return result

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
        _static_match = {}
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
            "$and": [{"fees.feeApy": {"$gt": 0}}, {"fees.feeApy": {"$lt": 8}}],
        }

        if period != 0:
            _returns_match["period"] = period
        if hypervisor_address != "":
            _returns_match["address"] = hypervisor_address

        # set return match vars
        _static_match = {}
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
            "$and": [{"fees.feeApr": {"$gt": 0}}, {"fees.feeApr": {"$lt": 9}}],
            "$and": [{"fees.feeApy": {"$gt": 0}}, {"fees.feeApy": {"$lt": 9}}],
            "$and": [{"fees.feeApr": {"$gt": 0}}, {"fees.feeApr": {"$lt": 9}}],
            "$and": [{"fees.feeApy": {"$gt": 0}}, {"fees.feeApy": {"$lt": 9}}],
        }

        if period != 0:
            _returns_match["period"] = period
        if hypervisor_address != "":
            _returns_match["address"] = hypervisor_address

        # set return match vars
        _static_match = {}
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

        return returns_by_period if period != 0 else returns_all_periods

    @staticmethod
    def query_return_impermanent(
        chain: Chain,
        period: int = 0,
        protocol: Protocol = None,
        hypervisor_address: str = None,
        ini_date: datetime = None,
        end_date: datetime = None,
    ) -> list[dict]:
        # build first main match part of the query
        _match = {"chain": chain, "period": period}
        if hypervisor_address:
            _match["address"] = hypervisor_address
        if ini_date and end_date:
            _match["$and"] = [
                {"timestamp": {"$gte": int(ini_date.timestamp())}},
                {"timestamp": {"$lte": int(end_date.timestamp())}},
            ]
        elif ini_date:
            _match["timestamp"] = {"$gte": int(ini_date.timestamp())}
        elif end_date:
            _match["timestamp"] = {"$lte": int(end_date.timestamp())}

        _query = [{"$match": _match}]
        # build protocol part as needed
        if protocol:
            _query.extend(
                (
                    {
                        "$lookup": {
                            "from": "static",
                            "localField": "hypervisor_id",
                            "foreignField": "id",
                            "as": "hypervisor",
                        }
                    },
                    {"$set": {"hypervisor": {"$arrayElemAt": ["$hypervisor", 0]}}},
                    {"$match": {"hypervisor.protocol": protocol}},
                )
            )

        _query.extend(
            (
                {"$sort": {"timestamp": -1}},
                {"$unset": ["_id", "hypervisor_id", "hypervisor", "id"]},
            )
        )

        # debug_query = f"{_query}"

        # return result
        return _query

    @staticmethod
    def query_return_imperm_rewards2_flat(
        chain: Chain,
        period: int,
        hypervisor_address: str,
        ini_date: datetime = None,
        end_date: datetime = None,
    ) -> list[dict]:
        """
            matches the first lte return timestamp rewards2 measure and adds it

        Args:
            chain (Chain):
            period (int):
            hypervisor_address (str):
            ini_date (datetime, optional): . Defaults to None.
            end_date (datetime, optional): . Defaults to None.

        Returns:
            list[dict]: query
        """

        # build first main match part of the query
        _match = {"chain": chain, "period": period, "address": hypervisor_address}

        if ini_date and end_date:
            _match["$and"] = [
                {"timestamp": {"$gte": int(ini_date.timestamp())}},
                {"timestamp": {"$lte": int(end_date.timestamp())}},
            ]
        elif ini_date:
            _match["timestamp"] = {"$gte": int(ini_date.timestamp())}
        elif end_date:
            _match["timestamp"] = {"$lte": int(end_date.timestamp())}

        # construct the allRewards2 match part of the query ( filter masterchefs addresses)
        _allrewards2_match = {}
        valid_masterchefs = [
            {"obj_as_arr.k": address.lower()}
            for dex, address_list in MASTERCHEF_ADDRESSES.get(chain, {}).items()
            for address in address_list
        ]
        if valid_masterchefs:
            _allrewards2_match = {
                "$and": [
                    {"$or": valid_masterchefs},
                    {f"obj_as_arr.v.pools.{hypervisor_address}": {"$exists": 1}},
                ]
            }
        else:
            _allrewards2_match = {
                f"obj_as_arr.v.pools.{hypervisor_address}": {"$exists": 1}
            }

        # allrewards2 subquery: pick the sum of each rewarder apr
        year_allRewards2_subquery = {
            "$ifNull": [
                {"$sum": f"$allRewards2.obj_as_arr.v.pools.{hypervisor_address}.apr"},
                0,
            ]
        }

        # return result
        _query = [
            {"$match": _match},
            {
                "$lookup": {
                    "from": "allRewards2",
                    "let": {
                        "returns_chain": "$chain",
                        "returns_datetime": {
                            "$toDate": {"$multiply": ["$timestamp", 1000]}
                        },
                    },
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$chain", "$$returns_chain"]},
                                        {
                                            "$lte": [
                                                "$datetime",
                                                "$$returns_datetime",
                                            ]
                                        },
                                    ],
                                }
                            }
                        },
                        {"$sort": {"datetime": -1}},
                        {"$limit": 1},
                        {"$addFields": {"obj_as_arr": {"$objectToArray": "$$ROOT"}}},
                        {"$unwind": "$obj_as_arr"},
                        {"$match": _allrewards2_match},
                    ],
                    "as": "allRewards2",
                }
            },
            {"$sort": {"timestamp": 1}},
            {
                "$project": {
                    "chain": "$chain",
                    "address": "$address",
                    "symbol": "$symbol",
                    "block": "$block",
                    "timestamp": "$timestamp",
                    "period": "$period",
                    "year_feeApr": "$fees.feeApr",
                    "year_feeApy": "$fees.feeApy",
                    "year_allRewards2": year_allRewards2_subquery,
                    "period_feeApr": {
                        "$multiply": ["$period", {"$divide": ["$fees.feeApr", 365]}]
                    },
                    "period_rewardsApr": {
                        "$multiply": [
                            "$period",
                            {
                                "$divide": [
                                    year_allRewards2_subquery,
                                    365,
                                ]
                            },
                        ]
                    },
                    "period_lping": "$impermanent.lping",
                    "period_hodl_deposited": "$impermanent.hodl_deposited",
                    "period_hodl_fifty": "$impermanent.hodl_fifty",
                    "period_hodl_token0": "$impermanent.hodl_token0",
                    "period_hodl_token1": "$impermanent.hodl_token1",
                }
            },
            {
                "$addFields": {
                    "period_netApr": {"$sum": ["$period_lping", "$period_rewardsApr"]},
                    "period_impermanentResult": {
                        "$subtract": ["$period_lping", "$period_feeApr"]
                    },
                }
            },
            {
                "$addFields": {
                    "gamma_vs_hodl": {
                        "$subtract": [
                            {
                                "$divide": [
                                    {"$sum": ["$period_netApr", 1]},
                                    {"$sum": ["$period_hodl_deposited", 1]},
                                ]
                            },
                            1,
                        ]
                    },
                }
                ##### FILTER: exclude big differences btwen gamma and deposited ####
            },
            {
                "$addFields": {
                    "exclude": {
                        "$abs": {
                            "$subtract": ["$gamma_vs_hodl", "$period_hodl_deposited"]
                        }
                    }
                }
            },
            {"$match": {"exclude": {"$lte": 0.2}}},
            {"$unset": ["_id", "exclude"]},
        ]

        # debug_query = f"{_query}"
        return _query

    @staticmethod
    def query_impermanentDivergence(
        chain: Chain, protocol: Protocol, period: int
    ) -> list[dict]:
        # set return match vars
        _returns_match = {"chain": chain, "period": period}
        # set protocol match vars
        _static_match = {"hypervisor.protocol": protocol}
        # set query
        return [
            {"$match": _returns_match},
            {
                "$project": {
                    "period": "$period",
                    "address": "$address",
                    "hypervisor_id": {"$concat": ["$chain", "_", "$address"]},
                    "timestamp": "$timestamp",
                    "block": "$block",
                    "lping": "$impermanent.lping",
                    "hodl_deposited": "$impermanent.hodl_deposited",
                    "hodl_fifty": "$impermanent.hodl_fifty",
                    "hodl_token0": "$impermanent.hodl_token0",
                    "hodl_token1": "$impermanent.hodl_token1",
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
                    "period": "$period",
                    "address": "$address",
                    "timestamp": "$timestamp",
                    "block": "$block",
                    "lping": "$lping",
                    "hodl_deposited": "$hodl_deposited",
                    "hodl_fifty": "$hodl_fifty",
                    "hodl_token0": "$hodl_token0",
                    "hodl_token1": "$hodl_token1",
                    "symbol": "$hypervisor.symbol",
                }
            },
            {
                "$group": {
                    "_id": {"address": "$address", "period": "$period"},
                    "item": {"$first": "$$ROOT"},
                }
            },
            {"$replaceRoot": {"newRoot": "$item"}},
            {"$unset": ["_id"]},
        ]


class db_allData_manager(db_collection_manager):
    def __init__(self, mongo_url: str):
        # Create a dictionary of collections
        self.db_collections = {"allData": {"id": True}}
        # Set the database name
        self.db_name = "gamma_db_v1"

        super().__init__(
            mongo_url=mongo_url,
            db_name=self.db_name,
            db_collections=self.db_collections,
        )
        self.db_collection_name = "allData"

    async def create_data(self, chain: Chain, protocol: Protocol) -> dict:
        """Create a dictionary of hypervisor_allData database models

        Args:
            chain (str): _description_
            protocol (str): _description_

        Returns:
            dict: <hypervisor_id>:<db_data_models.hypervisor_static>
        """
        # define result var
        result = {}
        hypervisor_info = HypervisorInfo(protocol=protocol, chain=chain)
        allData = await hypervisor_info.all_data()

        # types conversion
        for hyp_id, hypervisor in allData.items():
            hypervisor["totalSupply"] = str(hypervisor["totalSupply"])
            hypervisor["maxTotalSupply"] = str(hypervisor["maxTotalSupply"])
            # hypervisor["id"] = hyp_id

        # add id and datetime to data
        allData["id"] = f"{chain}_{protocol}"
        allData["datetime"] = datetime.now(timezone.utc)

        return allData

    async def feed_db(self, chain: Chain, protocol: Protocol):
        try:
            # save as 1 item ( not separated)
            await self.save_item_to_database(
                data=await self.create_data(chain=chain, protocol=protocol),
                collection_name=self.db_collection_name,
            )
        except Exception:
            logger.warning(
                f" Unexpected error feeding  {chain}'s {protocol} allData to db   err:{sys.exc_info()[0]}"
            )

    async def get_data(self, chain: Chain, protocol: Protocol) -> dict:
        result = await self._get_data(
            query=self.query_all(chain=chain, protocol=protocol)
        )
        try:
            return result[0]
        except Exception:
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
    def __init__(self, mongo_url: str):
        # Create a dictionary of collections
        self.db_collections = {"allRewards2": {"id": True}}
        # Set the database name
        self.db_name = "gamma_db_v1"

        super().__init__(
            mongo_url=mongo_url,
            db_name=self.db_name,
            db_collections=self.db_collections,
        )

        # Set the collection, which is the name of the collection in the database
        self.db_collection_name = "allRewards2"

    async def create_data(self, chain: Chain, protocol: Protocol) -> dict:
        """

        Args:
            chain (str): _description_
            protocol (str): _description_

        Returns:
            dict:
        """
        # define result var
        data = {}
        try:
            masterchef_info = MasterchefV2Info(protocol=protocol, chain=chain)
            data = await masterchef_info.output(get_data=True)
        except Exception as e:
            # some pools do not have Masterchef info
            raise ValueError(
                f" {chain}'s {protocol} has no Masterchef v2 implemented "
            ) from e

        # add id and datetime to data
        data["datetime"] = datetime.now(timezone.utc)
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
        except ValueError:
            pass
        except Exception:
            logger.warning(
                f" Unexpected error feeding  {chain}'s {protocol} allRewards2 to db   err:{sys.exc_info()[0]}"
            )

    async def get_data(self, chain: Chain, protocol: Protocol) -> dict:
        result = await self._get_data(
            query=self.query_all(chain=chain, protocol=protocol)
        )
        try:
            return result[0]
        except Exception:
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
        except Exception:
            return {}

    async def get_hypervisor_rewards(
        self,
        chain: Chain,
        address: str,
        ini_date: datetime = None,
        end_date: datetime = None,
    ) -> list[dict]:
        try:
            return await self._get_data(
                query=self.query_hype_rewards(
                    chain=chain,
                    hypervisor_address=address,
                    ini_date=ini_date,
                    end_date=end_date,
                )
            )
        except Exception:
            return list({})

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
    def query_last(chain: Chain, protocol: Protocol) -> list[dict]:
        # set return match vars
        _match = {"chain": chain, "protocol": protocol}

        return [
            {"$match": _match},
            {"$sort": {"datetime": -1}},
            {"$limit": 3},
            {"$unset": ["_id", "id", "chain", "protocol"]},
        ]

    @staticmethod
    def query_hype_rewards(
        chain: Chain,
        hypervisor_address: str,
        ini_date: datetime = None,
        end_date: datetime = None,
    ) -> list[dict]:
        """Get hypervisor's rewards2
            sorted by datetime newest first

        Args:
            chain (Chain):
            hypervisor_address (str):
            ini_date (datetime, optional): . Defaults to None.
            end_date (datetime, optional): . Defaults to None.

        Returns:
            list[str]:
        """
        _match = {"chain": chain}
        if ini_date and end_date:
            _match["$and"] = [
                {"datetime": {"$gte": ini_date}},
                {"datetime": {"$lte": end_date}},
            ]
        elif ini_date:
            _match["datetime"] = {"$gte": ini_date}
        elif end_date:
            _match["datetime"] = {"$lte": end_date}

        return [
            {"$match": _match},
            {"$sort": {"datetime": -1}},
            {"$addFields": {"obj_as_arr": {"$objectToArray": "$$ROOT"}}},
            {"$unwind": "$obj_as_arr"},
            {"$match": {f"obj_as_arr.v.pools.{hypervisor_address}": {"$exists": 1}}},
            {
                "$project": {
                    "_id": 0,
                    "chain": "$chain",
                    "datetime": "$datetime",
                    "protocol": "$protocol",
                    "rewards2": f"$obj_as_arr.v.pools.{hypervisor_address}",
                }
            },
        ]


class db_allRewards2_external_manager(db_allRewards2_manager):
    async def feed_db(
        self, chain: Chain, protocol: Protocol, current_timestamp: int = None
    ):
        try:
            # save as 1 item ( not separated)
            if data := await self.create_data(
                chain=chain, protocol=protocol, current_timestamp=current_timestamp
            ):
                await self.save_item_to_database(
                    data=data,
                    collection_name=self.db_collection_name,
                )
        except ValueError:
            pass
        except Exception as e:
            logger.warning(
                f" Unexpected error feeding  {chain}'s {protocol} allRewards2 to db   err:{e}"
            )

    async def create_data(
        self, chain: Chain, protocol: Protocol, current_timestamp: int = None
    ) -> dict:
        """Create the data ready to be saved to database

        Args:
            chain (str):
            protocol (str):

        Returns:
            dict:
        """

        try:
            # create local database helper
            db_name = f"{convert_chain_name(chain)}_gamma"
            local_db_helper = database_local(
                mongo_url=self._db_mongo_url, db_name=db_name
            )
            # get data from local database rewards_status ( web3 database)
            rewards_status = await local_db_helper.query_items_from_database(
                query=self.query_rewards(timestamp_end=current_timestamp),
                collection_name="rewards_status",
            )

            block = rewards_status[0]["block"]
            timestamp = rewards_status[0]["timestamp"]

            # define result var
            data = {
                "id": f"{timestamp}_{chain}_{protocol}",
                "chain": chain,
                "datetime": datetime.fromtimestamp(timestamp, timezone.utc),
                "protocol": protocol,
                "block": block,
            }

            # format rewards status so that equals allRewards2 database format

            # create pools content

            for reward in rewards_status:
                # create masterchef level in data if not exists
                if not reward["rewarder_registry"] in data:
                    data[reward["rewarder_registry"]] = {"pools": {}}

                # create hypervisor level in data/registry if not exists
                if (
                    not reward["hypervisor_address"]
                    in data[reward["rewarder_registry"]]["pools"]
                ):
                    data[reward["rewarder_registry"]]["pools"][
                        reward["hypervisor_address"]
                    ] = {
                        "stakeTokenSymbol": reward["rewardToken_symbol"],
                        "stakedAmount": 0,
                        "stakedAmountUSD": 0,
                        "apr": 0,
                        "lastRewardTimestamp": 0,
                        "rewarders": {},
                    }

                # add hypervisor data
                data[reward["rewarder_registry"]]["pools"][
                    reward["hypervisor_address"]
                ]["stakedAmount"] += int(reward["total_hypervisorToken_qtty"]) / (
                    10**18
                )
                data[reward["rewarder_registry"]]["pools"][
                    reward["hypervisor_address"]
                ]["stakedAmountUSD"] = (
                    data[reward["rewarder_registry"]]["pools"][
                        reward["hypervisor_address"]
                    ]["stakedAmount"]
                    * reward["hypervisor_share_price_usd"]
                )

                #
                # create rewarder level in data/registry/hypervisor if not exists
                # should not exist ... but just in case
                if (
                    not reward["rewarder_address"]
                    in data[reward["rewarder_registry"]]["pools"][
                        reward["hypervisor_address"]
                    ]["rewarders"]
                ):
                    data[reward["rewarder_registry"]]["pools"][
                        reward["hypervisor_address"]
                    ]["rewarders"][reward["rewarder_address"]] = {
                        "rewardToken": reward["rewardToken"],
                        "rewardTokenDecimals": reward["rewardToken_decimals"],
                        "rewardTokenSymbol": reward["rewardToken_symbol"],
                        "rewardPerSecond": int(reward["rewards_perSecond"])
                        / (10 ** reward["rewardToken_decimals"]),
                        "allocPoint": 0,
                        "apr": reward["apr"],
                    }
                    # add apr to hypervisor level
                    data[reward["rewarder_registry"]]["pools"][
                        reward["hypervisor_address"]
                    ]["apr"] += reward["apr"]

                elif (
                    data[reward["rewarder_registry"]]["pools"][
                        reward["hypervisor_address"]
                    ]["rewarders"][reward["rewarder_address"]]["rewardToken"]
                    != reward["rewardToken"]
                ):
                    # add apr to root pool but log error
                    data[reward["rewarder_registry"]]["pools"][
                        reward["hypervisor_address"]
                    ]["apr"] += reward["apr"]
                    logger.error(
                        f" {chain}'s {protocol} has same rewarder address with different reward token "
                    )
                else:
                    logger.error(
                        f" {chain}'s {protocol} has same rewarder address with same reward token "
                    )
        except IndexError as e:
            raise IndexError(
                " {}'s {} has no rewards data in database {}".format(
                    chain,
                    protocol,
                    f"for {current_timestamp} timestamp" if current_timestamp else "",
                )
            ) from e
        except Exception as e:
            raise ValueError(
                f" {chain}'s {protocol} has no external rewards implemented "
            ) from e

        # return
        return data

    @staticmethod
    def query_rewards(timestamp_end: int | None = None) -> list[dict]:
        result = [
            {"$sort": {"block": -1}},
            {
                "$group": {
                    "_id": "$hypervisor_address",
                    "reward_data": {"$first": "$$ROOT"},
                }
            },
            {"$replaceRoot": {"newRoot": "$reward_data"}},
            {"$unset": ["_id"]},
        ]

        if timestamp_end:
            result.insert(0, {"$match": {"timestamp": {"$lte": timestamp_end}}})

        return result


class db_aggregateStats_manager(db_collection_manager):
    def __init__(self, mongo_url: str):
        # Create a dictionary of collections
        self.db_collections = {"agregateStats": {"id": True}}
        # Set the database name
        self.db_name = "gamma_db_v1"

        super().__init__(
            mongo_url=mongo_url,
            db_name=self.db_name,
            db_collections=self.db_collections,
        )

        # Set the collection, which is the name of the collection in the database
        self.db_collection_name = "agregateStats"

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

        dtime = datetime.now(timezone.utc)
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
        except Exception:
            logger.warning(
                f" Unexpected error feeding  {chain}'s {protocol} aggregateStats to db   err:{sys.exc_info()[0]}"
            )

    async def get_data(self, chain: Chain, protocol: Protocol) -> dict:
        result = await self._get_data(
            query=self.query_last(chain=chain, protocol=protocol)
        )
        try:
            return result[0]
        except Exception:
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


# web3 database related classes


class database_global(db_collections_common):
    """global database helper
    "blocks":
        item-> {id: <network>_<block_number>
                network:
                block:
                timestamp:
                }
    "usd_prices":
        item-> {id: <network>_<block_number>_<address>
                network:
                block:
                address:
                price:
                }
    """

    def __init__(
        self, mongo_url: str, db_name: str = "global", db_collections: dict = None
    ):
        if db_collections is None:
            db_collections = {"blocks": {"id": True}, "usd_prices": {"id": True}}
        super().__init__(
            mongo_url=mongo_url, db_name=db_name, db_collections=db_collections
        )

    async def set_price_usd(
        self, network: str, block: int, token_address: str, price_usd: float
    ):
        data = {
            "id": f"{network}_{block}_{token_address}",
            "network": network,
            "block": int(block),
            "address": token_address,
            "price": float(price_usd),
        }

        await self.save_item_to_database(data=data, collection_name="usd_prices")

    async def set_block(self, network: str, block: int, timestamp: datetime.timestamp):
        data = {
            "id": f"{network}_{block}",
            "network": network,
            "block": block,
            "timestamp": timestamp,
        }
        await self.save_item_to_database(data=data, collection_name="blocks")

    async def get_unique_prices_addressBlock(self, network: str) -> list:
        """get addresses and blocks already present in database
            with price greater than zero.

        Args:
            network (str):

        Returns:
            list:
        """
        return await self.get_items_from_database(
            collection_name="usd_prices", find={"network": network, "price": {"$gt": 0}}
        )

    async def get_price_usd(
        self,
        network: str,
        block: int,
        address: str,
    ) -> list[dict]:
        """get usd price from block

        Args:
            network (str): ethereum, optimism, polygon....
            block (int): number
            address (str): token address

        Returns:
            list[dict]: list of price dict obj
        """
        return await self.get_items_from_database(
            collection_name="usd_prices",
            find={"network": network, "block": block, "address": address},
        )

    async def get_price_usd_closestBlock(
        self,
        network: str,
        block: int,
        address: str,
    ) -> dict:
        """get usd price from closest block to <block>

        Args:
            network (str):
            block (int): number
            address (str): token address

        Returns:
            dict:
        """
        return await self.query_items_from_database(
            query=self.query_blocks_closest(network=network, block=block),
            collection_name="usd_prices",
        )

    async def get_timestamp(
        self,
        network: str,
        block: int,
    ) -> dict:
        return await self.get_items_from_database(
            collection_name="blocks",
            find={"network": network, "block": block},
        )

    async def get_closest_timestamp(self, network: str, block: int) -> dict:
        return await self.query_items_from_database(
            query=self.query_blocks_closest(network=network, block=block),
            collection_name="blocks",
        )

    async def get_block(
        self,
        network: str,
        timestamp: int,
    ) -> dict:
        return await self.get_items_from_database(
            collection_name="blocks", find={"network": network, "timestamp": timestamp}
        )

    async def get_closest_block(self, network: str, timestamp: int) -> dict:
        return await self.query_items_from_database(
            query=self.query_blocks_closest(network=network, timestamp=timestamp),
            collection_name="blocks",
        )

    async def get_all_block_timestamp(self, network: str) -> list:
        """get all blocks and timestamps from database
            sorted by block
        Args:
            network (str):

        Returns:
            list: of sorted blocks timestamps
        """
        return await self.get_items_from_database(
            collection_name="blocks", find={"network": network}, sort=[("block", 1)]
        )

    @staticmethod
    def query_prices_addressBlocks(network: str) -> list[dict]:
        """get addresses and blocks of usd prices present at database and greater than zero

        Args:
            network (str):

        Returns:
            list[dict]:
        """
        return [
            {"$match": {"network": network, "price": {"$gt": 0}}},
        ]

    @staticmethod
    def query_blocks_closest(
        network: str, block: int = 0, timestamp: int = 0
    ) -> list[dict]:
        """find closest block/timestamp item in database

        Args:
            network (str):
            block (int, optional): . Defaults to 0.
            timestamp (int, optional): . Defaults to 0.

        Raises:
            NotImplementedError: when no block or timestamp are provided

        Returns:
            list[dict]:
        """
        if block != 0:
            _search = [block, "$block"]
        elif timestamp != 0:
            _search = [timestamp, "$timestamp"]
        else:
            raise NotImplementedError(
                " provide either block or timestamp. If both are provided, block will be used "
            )
        return [
            {"$match": {"network": network}},
            # Project a diff field that's the absolute difference along with the original doc.
            {
                "$project": {
                    "diff": {"$abs": {"$subtract": _search}},
                    "doc": "$$ROOT",
                }
            },
            # Order the docs by diff
            {"$sort": {"diff": 1}},
            # Take the first one
            {"$limit": 1},
        ]


class database_local(db_collections_common):
    """local database helper
    "static":
        item-> {id: <hypervisor_address>_
                "address": "",  # hypervisor id
                "created": None,  # datetime
                "fee": 0,  # 500
                "network": "",  # polygon
                "name": "",  # xWMATIC-USDC05
                "pool_id": "",  # pool id
                "tokens": [  db_objec_model.token... ],

    "operations":
        item-> {id: <logIndex>_<transactionHash>
                {
                    "_id" : ObjectId("63e0f19e2309ec2395434e4b"),
                    "transactionHash" : "0x8bf414df76a612ce2110cabec4fcaefd9cfc6aaeddd29d7850ac6fa2786adbb4",
                    "blockHash" : "0x286390969e2ddfa3aed6ed885c793bc78bb1974ec7f019116bed6b3edd5fa294",
                    "blockNumber" : 12590365,
                    "address" : "0x9a98bffabc0abf291d6811c034e239e916bbcec0",
                    "timestamp" : 1623108400,
                    "decimals_token0" : 18,
                    "decimals_token1" : 6,
                    "decimals_contract" : 18,
                    "tick" : -197716,
                    "totalAmount0" : "3246736264521404428",
                    "totalAmount1" : "6762363410",
                    "qtty_token0" : "3741331192922089",
                    "qtty_token1" : "0",
                    "topic" : "rebalance",
                    "logIndex" : 118,
                    "id" : "118_0x8bf414df76a612ce2110cabec4fcaefd9cfc6aaeddd29d7850ac6fa2786adbb4"
                }
                ...
                }

    "status":
        item-> {id: <hypervisor address>_<block_number>
                network:
                block:
                address:
                qtty_token0: 0,  # token qtty   (this is tvl = deployed_qtty + owed fees + parked_qtty )
                qtty_token1: 0,  #
                deployed_token0: 0,  # tokens deployed into pool
                deployed_token1: 0,  #
                parked_token0: 0,  # tokens sitting in hype contract ( sleeping )
                parked_token1: 0,  #
                supply: 0,  # total Suply

                }

    "user_status":
        item-> {id: <wallet_address>_<block_number>
                network:
                block:
                address:  <wallet_address>
                ...

                }
    """

    def __init__(self, mongo_url: str, db_name: str, db_collections: dict = None):
        if db_collections is None:
            db_collections = {
                "static": {"id": True},
                "operations": {
                    "id": True,
                    "address": False,
                    "blockNumber": False,
                },
                "status": {
                    "id": True,
                    "address": False,
                    "block": False,
                    "timestamp": False,
                },
                "user_status": {
                    "id": True,
                    "address": False,
                    "hypervisor_address": False,
                    "block": False,
                    "timestamp": False,
                },
            }

        super().__init__(
            mongo_url=mongo_url, db_name=db_name, db_collections=db_collections
        )

    # static

    async def set_static(self, data: dict):
        data["id"] = data["address"]
        await self.save_item_to_database(data=data, collection_name="static")

    async def get_unique_tokens(self) -> list:
        """Get a unique token list from static database

        Returns:
            list:
        """
        return await self.get_items_from_database(
            collection_name="static", aggregate=self.query_unique_token_addresses()
        )

    async def get_mostUsed_tokens1(self, limit: int = 10) -> list:
        """Return the addresses of the top used tokens1, present in static database

        Args:
            limit (int, optional): . Defaults to 5.

        Returns:
            list: of {"token":<address>}
        """
        return await self.get_items_from_database(
            collection_name="static",
            aggregate=self.query_status_mostUsed_token1(limit=limit),
        )

    # operation

    async def set_operation(self, data: dict):
        await self.replace_item_to_database(data=data, collection_name="operations")

    async def get_all_operations(self, hypervisor_address: str) -> list:
        """find all hypervisor operations from db
            sort by lowest block and lowest logIndex first

        Args:
            hypervisor_address (str): address

        Returns:
            list: hypervisor status list
        """
        find = {"address": hypervisor_address}
        sort = [("blockNumber", 1), ("logIndex", 1)]
        return await self.get_items_from_database(
            collection_name="operations", find=find, sort=sort
        )

    async def get_hype_operations_btwn_timestamps(
        self,
        hypervisor_address: str,
        timestamp_ini: int,
        timestamp_end: int,
    ) -> list:
        return await self.query_items_from_database(
            collection_name="operations",
            query=self.query_operations_btwn_timestamps(
                hypervisor_address=hypervisor_address,
                timestamp_ini=timestamp_ini,
                timestamp_end=timestamp_end,
            ),
        )

    async def get_unique_operations_addressBlock(self, topics: list = None) -> list:
        """Retrieve a list of unique blocks + hypervisor addresses present in operations collection

        Returns:
            list: of  {
                    "address" : "0x407e99b20d61f245426031df872966953909e9d3",
                    "block" : 12736656
                    }
        """
        query = []
        if topics:
            query.append({"$match": {"topics": {"$in": topics}}})

        query.extend(
            (
                {
                    "$group": {
                        "_id": {"address": "$address", "block": "$blockNumber"},
                    }
                },
                {
                    "$project": {
                        "address": "$_id.address",
                        "block": "$_id.block",
                    }
                },
                {"$unset": ["_id"]},
            )
        )

        debug_query = f"{query}"

        return await self.get_items_from_database(
            collection_name="operations", aggregate=query
        )

    async def get_user_operations(
        self, user_address: str, timestamp_ini: int | None, timestamp_end: int | None
    ) -> list:
        find = {
            "$or": [
                {"src": user_address},
                {"dst": user_address},
                {"from": user_address},
                {"to": user_address},
            ]
        }

        if timestamp_ini and timestamp_end:
            find["$and"] = [
                {"timestamp": {"$lte": timestamp_end}},
                {"timestamp": {"$gte": timestamp_ini}},
            ]
        elif timestamp_ini:
            find["timestamp"] = {"$gte": timestamp_ini}
        elif timestamp_end:
            find["timestamp"] = {"$lte": timestamp_end}

        sort = [("block", 1)]
        return await self.get_items_from_database(
            collection_name="status", find=find, sort=sort
        )

    # status

    async def set_status(self, data: dict):
        # define database id
        data["id"] = f"{data['address']}_{data['block']}"
        await self.save_item_to_database(data=data, collection_name="status")

    async def get_all_status(self, hypervisor_address: str) -> list:
        """find all hypervisor status from db
            sort by lowest block first

        Args:
            hypervisor_address (str): address

        Returns:
            list: hypervisor status list
        """
        find = {"address": hypervisor_address}
        sort = [("block", 1)]
        return await self.get_items_from_database(
            collection_name="status", find=find, sort=sort
        )

    async def get_hype_status_btwn_blocks(
        self,
        hypervisor_address: str,
        block_ini: int,
        block_end: int,
    ) -> list:
        return await self.query_items_from_database(
            collection_name="status",
            query=self.query_status_btwn_blocks(
                hypervisor_address=hypervisor_address,
                block_ini=block_ini,
                block_end=block_end,
            ),
        )

    async def get_hype_status_blocks(
        self, hypervisor_address: str, blocks: list
    ) -> list:
        find = {"address": hypervisor_address, "block": {"$in": blocks}}
        sort = [("block", 1)]
        return await self.get_items_from_database(
            collection_name="status", find=find, sort=sort
        )

    async def get_unique_status_addressBlock(self) -> list:
        """Retrieve a list of unique blocks + hypervisor addresses present in status collection

        Returns:
            list: of {
                    "address" : "0x407e99b20d61f245426031df872966953909e9d3",
                    "block" : 12736656
                    }
        """
        query = [
            {
                "$group": {
                    "_id": {"address": "$address", "block": "$block"},
                }
            },
            {
                "$project": {
                    "address": "$_id.address",
                    "block": "$_id.block",
                }
            },
            {"$unset": ["_id"]},
        ]
        return await self.get_items_from_database(
            collection_name="status", aggregate=query
        )

    async def get_status_feeReturn_data(
        self,
        hypervisor_address: str,
        timestamp_ini: int,
        timestamp_end: int,
    ) -> list:
        return await self.query_items_from_database(
            collection_name="status",
            query=self.query_status_feeReturn_data(
                hypervisor_address=hypervisor_address,
                timestamp_ini=timestamp_ini,
                timestamp_end=timestamp_end,
            ),
        )

    async def get_status_feeReturn_data_alternative(
        self,
        hypervisor_address: str,
        timestamp_ini: int,
        timestamp_end: int,
    ) -> list:
        return await self.query_items_from_database(
            collection_name="status",
            query=self.query_status_feeReturn_data_alternative(
                hypervisor_address=hypervisor_address,
                timestamp_ini=timestamp_ini,
                timestamp_end=timestamp_end,
            ),
        )

    # user status

    async def set_user_status(self, data: dict):
        """

        Args:
            data (dict):
        """
        # define database id
        data[
            "id"
        ] = f"{data['address']}_{data['block']}_{data['logIndex']}_{data['hypervisor_address']}"

        # convert decimal to bson compatible and save
        await self.replace_item_to_database(data=data, collection_name="user_status")

    async def get_user_status(
        self, address: str, block_ini: int = 0, block_end: int = 0
    ) -> list:
        _main_match = {
            "address": address,
            "topic": {"$in": ["report", "withdraw", "deposit", "transfer"]},
        }
        if block_ini and block_end:
            _main_match["$and"] = [
                {"block": {"$lte": block_end}},
                {"block": {"$gte": block_ini}},
            ]
        elif block_ini:
            _main_match["block"] = {"$gte": block_ini}
        elif block_end:
            _main_match["block"] = {"$lte": block_end}

        query = [
            {"$match": _main_match},
            {"$sort": {"block": 1}},
            {
                "$group": {
                    "_id": "$hypervisor_address",
                    "hypervisor_address": {"$first": "$hypervisor_address"},
                    "history": {
                        "$push": {
                            "hypervisor_address": "$hypervisor_address",
                            "block": "$block",
                            "timestamp": "$timestamp",
                            "topic": "$topic",
                            "investment_qtty_token0": "$investment_qtty_token0",
                            "investment_qtty_token1": "$investment_qtty_token1",
                            "total_investment_qtty_in_usd": "$total_investment_qtty_in_usd",
                            "total_investment_qtty_in_token0": "$total_investment_qtty_in_token0",
                            "total_investment_qtty_in_token1": "$total_investment_qtty_in_token1",
                            "underlying_token0": "$underlying_token0",
                            "underlying_token1": "$underlying_token1",
                            "fees_collected_token0": "$fees_collected_token0",
                            "fees_collected_token1": "$fees_collected_token1",
                            "fees_owed_token0": "$fees_owed_token0",
                            "fees_owed_token1": "$fees_owed_token1",
                            "fees_uncollected_token0": "$fees_uncollected_token0",
                            "fees_uncollected_token1": "$fees_uncollected_token1",
                            "usd_price_token0": "$usd_price_token0",
                            "usd_price_token1": "$usd_price_token1",
                            "divestment_base_qtty_token0": "$divestment_base_qtty_token0",
                            "divestment_base_qtty_token1": "$divestment_base_qtty_token1",
                            "divestment_fee_qtty_token0": "$divestment_fee_qtty_token0",
                            "divestment_fee_qtty_token1": "$divestment_fee_qtty_token1",
                        }
                    },
                }
            },
            {"$unset": ["_id"]},
        ]

        debug_query = f"{query}"
        return [
            self.convert_decimal_to_float(item=self.convert_d128_to_decimal(item=item))
            for item in await self.query_items_from_database(
                query=query, collection_name="user_status"
            )
        ]

    # all

    async def get_items(self, collection_name: str, **kwargs) -> list:
        """Any

        Returns:
            list: of results
        """
        return await self.get_items_from_database(
            collection_name=collection_name, **kwargs
        )

    async def get_max_field(self, collection: str, field: str) -> list:
        """get the maximum field present in db
        Args:
            collection (str): _description_
            field (str): _description_

        Returns:
            list: of { "max": <value>}
        """
        return await self.get_items_from_database(
            collection_name=collection,
            aggregate=self.query_max(field=field),
        )

    # queries

    @staticmethod
    def query_unique_addressBlocks() -> list[dict]:
        """retriev

        Args:
            field (str): ca

        Returns:
            list[dict]: _description_
        """
        # return query
        return [
            {
                "$group": {
                    "_id": {"address": "$address", "block": "$blockNumber"},
                }
            },
            {
                "$project": {
                    "address": "$_id.address",
                    "block": "$_id.block",
                }
            },
            {"$unset": ["_id"]},
        ]

    @staticmethod
    def query_unique_token_addresses() -> list[dict]:
        """Unique token list using status database

        Returns:
            list[dict]:
        """
        return [
            {
                "$group": {
                    "_id": "$pool.address",
                    "items": {"$push": "$$ROOT"},
                }
            },
            {"$project": {"_id": "$_id", "last": {"$last": "$items"}}},
            {
                "$project": {
                    "_id": "$_id",
                    "token": ["$last.pool.token0.address", "$last.pool.token1.address"],
                }
            },
            {"$unwind": "$token"},
            {"$group": {"_id": "$token"}},
        ]

    @staticmethod
    def query_operations_btwn_timestamps(
        hypervisor_address: str,
        timestamp_ini: int,
        timestamp_end: int,
    ) -> list[dict]:
        """get operations between timestamps

        Args:
            timestamp_ini (datetime.timestamp): initial timestamp
            timestamp_end (datetime.timestamp): end timestamp

        Returns:
            list[dict]:
        """
        return [
            {
                "$match": {
                    "address": hypervisor_address,
                    "timestamp": {"$gte": timestamp_ini, "$lte": timestamp_end},
                }
            },
            {"$sort": {"blockNumber": -1, "logIndex": 1}},
        ]

    @staticmethod
    def query_status_btwn_blocks(
        hypervisor_address: str,
        block_ini: datetime.timestamp,
        block_end: datetime.timestamp,
    ) -> list[dict]:
        """get status between blocks"""
        return [
            {
                "$match": {
                    "address": hypervisor_address,
                    "block": {"$gte": block_ini, "$lte": block_end},
                }
            },
            {"$sort": {"block": -1}},
        ]

    @staticmethod
    def query_status_mostUsed_token1(limit: int = 5) -> list[dict]:
        """return the top most used token1 address of static database
            ( may be used in status too)

        Returns:
            list[dict]: _description_
        """
        return [
            {
                "$group": {
                    "_id": {"token1": "$pool.token1.address"},
                    "symbol": {"$last": "$pool.token1.symbol"},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "token": "$_id.token1",
                    "symbol": "$symbol",
                }
            },
            {"$unset": ["_id"]},
        ]

    @staticmethod
    def query_max(field: str) -> list[dict]:
        return [
            {
                "$group": {
                    "_id": "id",
                    "max": {"$max": f"${field}"},
                }
            },
            {"$unset": ["_id"]},
        ]

    @staticmethod
    def query_status_feeReturn_data(
        hypervisor_address: str,
        timestamp_ini: int,
        timestamp_end: int,
    ) -> list[dict]:
        """Get data to construct feeAPY APR using equal totalSupply values between blocks to identify APY period.
            This is a prone to error method as totalSupply may sporadically coincide in diff periods ...

        Args:
            hypervisor_address (str):
            timestamp_ini (int):
            timestamp_end (int):

        Returns:
            list[dict]:
                            "period_days" : 0.01653935185185185,
                            "ini_block" : NumberInt(14937408),
                            "end_block" : NumberInt(14937491),
                            "ini_timestamp" : NumberInt(1654849152),
                            "end_timestamp" : NumberInt(1654850581),
                            "ini_supply" : NumberDecimal("91.89181431665138243"),
                            "end_supply" : NumberDecimal("91.89181431665138243"),
                            "ini_tvl0" : NumberDecimal("47083.654951511146650678"),
                            "ini_tvl1" : NumberDecimal("69.395815272326034611"),
                            "ini_fees_uncollected0" : NumberDecimal("6.523979236566497"),
                            "ini_fees_uncollected1" : NumberDecimal("0.01195312935918579"),
                            "ini_fees_owed0" : NumberDecimal("0.0000"),
                            "ini_fees_owed1" : NumberDecimal("0.0000"),
                            "end_tvl0" : NumberDecimal("47083.654951511146650678"),
                            "end_tvl1" : NumberDecimal("69.395815272326034611"),
                            "end_fees_uncollected0" : NumberDecimal("6.523979236566497"),
                            "end_fees_uncollected1" : NumberDecimal("0.01195312935918579"),
                            "end_fees_owed0" : NumberDecimal("0.0000"),
                            "end_fees_owed1" : NumberDecimal("0.0000"),
                            "error_ini" : NumberInt(0),
                            "error_end" : NumberInt(0)
        """
        return [
            {
                "$match": {
                    "address": hypervisor_address,
                    "$and": [
                        {"timestamp": {"$lte": timestamp_end}},
                        {"timestamp": {"$gte": timestamp_ini}},
                    ],
                }
            },
            {"$sort": {"block": 1}},
            {
                "$group": {
                    "_id": "$totalSupply",
                    "items": {"$push": "$$ROOT"},
                    "max_block": {"$max": "$block"},
                    "min_block": {"$min": "$block"},
                    "max_timestamp": {"$max": "$timestamp"},
                    "min_timestamp": {"$min": "$timestamp"},
                }
            },
            {
                "$addFields": {
                    "period_days": {
                        "$divide": [
                            {"$subtract": ["$max_timestamp", "$min_timestamp"]},
                            60 * 60 * 24,
                        ]
                    }
                }
            },
            {"$sort": {"min_block": 1}},
            {
                "$project": {
                    "max_block": "$max_block",
                    "min_block": "$min_block",
                    "max_timestamp": "$max_timestamp",
                    "min_timestamp": "$min_timestamp",
                    "period_days": "$period_days",
                    "ini_snapshot": {"$arrayElemAt": ["$items", 0]},
                    "end_snapshot": {"$arrayElemAt": ["$items", -1]},
                }
            },
            {
                "$project": {
                    "max_block": "$max_block",
                    "min_block": "$min_block",
                    "max_timestamp": "$max_timestamp",
                    "min_timestamp": "$min_timestamp",
                    "period_days": "$period_days",
                    "ini_snapshot": "$ini_snapshot",
                    "end_snapshot": "$end_snapshot",
                    "error_ini": {"$subtract": ["$ini_snapshot.block", "$min_block"]},
                    "error_end": {"$subtract": ["$end_snapshot.block", "$max_block"]},
                }
            },
            {
                "$project": {
                    "period_days": "$period_days",
                    "ini_block": "$ini_snapshot.block",
                    "end_block": "$end_snapshot.block",
                    "ini_timestamp": "$ini_snapshot.timestamp",
                    "end_timestamp": "$end_snapshot.timestamp",
                    "ini_supply": {
                        "$divide": [
                            {"$toDecimal": "$ini_snapshot.totalSupply"},
                            {"$pow": [10, "$ini_snapshot.decimals"]},
                        ]
                    },
                    "end_supply": {
                        "$divide": [
                            {"$toDecimal": "$end_snapshot.totalSupply"},
                            {"$pow": [10, "$end_snapshot.decimals"]},
                        ]
                    },
                    "ini_tvl0": {
                        "$divide": [
                            {"$toDecimal": "$ini_snapshot.totalAmounts.total0"},
                            {"$pow": [10, "$ini_snapshot.pool.token0.decimals"]},
                        ]
                    },
                    "ini_tvl1": {
                        "$divide": [
                            {"$toDecimal": "$ini_snapshot.totalAmounts.total1"},
                            {"$pow": [10, "$ini_snapshot.pool.token1.decimals"]},
                        ]
                    },
                    "ini_fees_uncollected0": {
                        "$divide": [
                            {
                                "$toDecimal": "$ini_snapshot.fees_uncollected.qtty_token0"
                            },
                            {"$pow": [10, "$ini_snapshot.pool.token0.decimals"]},
                        ]
                    },
                    "ini_fees_uncollected1": {
                        "$divide": [
                            {
                                "$toDecimal": "$ini_snapshot.fees_uncollected.qtty_token1"
                            },
                            {"$pow": [10, "$ini_snapshot.pool.token1.decimals"]},
                        ]
                    },
                    "ini_fees_owed0": {
                        "$divide": [
                            {"$toDecimal": "$ini_snapshot.tvl.fees_owed_token0"},
                            {"$pow": [10, "$ini_snapshot.pool.token0.decimals"]},
                        ]
                    },
                    "ini_fees_owed1": {
                        "$divide": [
                            {"$toDecimal": "$ini_snapshot.tvl.fees_owed_token1"},
                            {"$pow": [10, "$ini_snapshot.pool.token1.decimals"]},
                        ]
                    },
                    "end_tvl0": {
                        "$divide": [
                            {"$toDecimal": "$end_snapshot.totalAmounts.total0"},
                            {"$pow": [10, "$end_snapshot.pool.token0.decimals"]},
                        ]
                    },
                    "end_tvl1": {
                        "$divide": [
                            {"$toDecimal": "$end_snapshot.totalAmounts.total1"},
                            {"$pow": [10, "$end_snapshot.pool.token1.decimals"]},
                        ]
                    },
                    "end_fees_uncollected0": {
                        "$divide": [
                            {
                                "$toDecimal": "$end_snapshot.fees_uncollected.qtty_token0"
                            },
                            {"$pow": [10, "$end_snapshot.pool.token0.decimals"]},
                        ]
                    },
                    "end_fees_uncollected1": {
                        "$divide": [
                            {
                                "$toDecimal": "$end_snapshot.fees_uncollected.qtty_token1"
                            },
                            {"$pow": [10, "$end_snapshot.pool.token1.decimals"]},
                        ]
                    },
                    "end_fees_owed0": {
                        "$divide": [
                            {"$toDecimal": "$end_snapshot.tvl.fees_owed_token0"},
                            {"$pow": [10, "$end_snapshot.pool.token0.decimals"]},
                        ]
                    },
                    "end_fees_owed1": {
                        "$divide": [
                            {"$toDecimal": "$end_snapshot.tvl.fees_owed_token1"},
                            {"$pow": [10, "$end_snapshot.pool.token1.decimals"]},
                        ]
                    },
                    "error_ini": "$error_ini",
                    "error_end": "$error_end",
                }
            },
            {"$unset": ["_id"]},
        ]

    @staticmethod
    def query_status_feeReturn_data_alternative(
        hypervisor_address: str, timestamp_ini: int, timestamp_end: int
    ) -> list[dict]:
        """

            old descript: return a list of status ordered by block matching deposit,withdraw,rebalance and zeroBurn operation blocks and those same blocks -1
            Each status has a order field indicating if this is the initial period status with a "first" value
            or this is the end of the perios status with the "last" value

        Args:
            hypervisor_address (str):
            timestamp_ini (int):
            timestamp_end (int):

        Returns:
            list[dict]:   Each status has an <order> field indicating if this is the initial period status with a "first" value
            or this is the end of the perios status with the "last" value
        """

        return [
            {
                "$match": {
                    "address": hypervisor_address,
                    "$and": [
                        {"timestamp": {"$lte": timestamp_end}},
                        {"timestamp": {"$gte": timestamp_ini}},
                    ],
                }
            },
            {"$sort": {"block": 1}},
            {
                "$group": {
                    "_id": "$totalSupply",
                    "items": {"$push": "$$ROOT"},
                    "max_block": {"$max": "$block"},
                    "min_block": {"$min": "$block"},
                    "max_timestamp": {"$max": "$timestamp"},
                    "min_timestamp": {"$min": "$timestamp"},
                }
            },
            {
                "$addFields": {
                    "period_days": {
                        "$divide": [
                            {"$subtract": ["$max_timestamp", "$min_timestamp"]},
                            60 * 60 * 24,
                        ]
                    }
                }
            },
            {"$sort": {"min_block": 1}},
            {"$unwind": "$items"},
            {"$replaceRoot": {"newRoot": "$items"}},
            {"$unset": ["_id", "id"]},
        ]

    @staticmethod
    def query_all_users(
        user_address: str, timestamp_ini: int = None, timestamp_end: int = None
    ) -> list[dict]:
        _match = {
            "$or": [
                {"src": user_address},
                {"dst": user_address},
                {"from": user_address},
                {"to": user_address},
            ]
        }

        if timestamp_ini and timestamp_end:
            _match["$and"] = [
                {"timestamp": {"$lte": timestamp_end}},
                {"timestamp": {"$gte": timestamp_ini}},
            ]
        elif timestamp_ini:
            _match["timestamp"] = {"$gte": timestamp_ini}
        elif timestamp_end:
            _match["timestamp"] = {"$lte": timestamp_end}

        return [{"$match": _match}, {"$sort": {"timestamp": 1}}]


def convert_chain_name(chain: Chain) -> str:
    if chain == Chain.MAINNET:
        return "ethereum"
    elif chain == Chain.BSC:
        return "binance"
    else:
        return chain.value
