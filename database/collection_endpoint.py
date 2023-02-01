import logging
import asyncio
from datetime import datetime

from dataclasses import dataclass, field, asdict, InitVar
from v3data.config import MONGO_DB_URL, DEFAULT_TIMEZONE
from v3data.hypervisor import HypervisorInfo, HypervisorData
from v3data.masterchef_v2 import MasterchefV2Info, UserRewardsV2
from v3data.hypes.impermanent_data import ImpermanentDivergence

from database.collections_common import db_collections_common


class db_static_manager(db_collections_common):
    db_collection_name = "static"

    async def create_data(self, chain: str, protocol: str) -> dict:
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

    async def feed_db(self, chain: str, protocol: str):

        await self.save_items_to_database(
            data=await self.create_data(chain=chain, protocol=protocol),
            collection_name=self.db_collection_name,
        )

    async def __get_data(self, chain: str, protocol: str) -> dict:
        pass


class db_returns_manager(db_collections_common):
    db_collection_name = "returns"

    # format data to be used with mongo db
    async def create_data(self, chain: str, protocol: str, period_days: int) -> dict:
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
                # set the database unique id
                database_id = f"{chain}_{k}_{block}_{period_days}"

                result[k] = {
                    "id": database_id,
                    "chain": chain,
                    "period": period_days,
                    "address": k,
                    "symbol": v["symbol"],
                    "block": block,
                    "timestamp": timestamp,
                    "fees": {
                        "feeApr": v["feeApr"],
                        "feeApy": v["feeApy"],
                        "hasOutlier": v["hasOutlier"],
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

    async def feed_db(self, chain: str, protocol: str, periods: list[int] = [1, 7, 30]):

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

    async def __get_data(self, query: list[dict]):
        return self.get_items_from_database(
            query=query, collection_name=self.db_collection_name
        )

    async def get_hypervisors_average(
        self, chain: str, period: int = 0, protocol: str = ""
    ) -> dict:
        return await self.__get_data(
            query=self.query_hypervisors_average(
                chain=chain, period=period, protocol=protocol
            )
        )

    async def get_hypervisor_average(
        self, chain: str, hypervisor_address: str, period: int = 0, protocol: str = ""
    ) -> dict:
        return await self.__get_data(
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


class db_allData_manager(db_collections_common):
    db_collection_name = "allData"

    async def create_data(self, chain: str, protocol: str) -> dict:
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

    async def feed_db(self, chain: str, protocol: str):

        # save as 1 item ( not separated)
        await self.save_item_to_database(
            data=await self.create_data(chain=chain, protocol=protocol),
            collection_name=self.db_collection_name,
        )

    async def __get_data(self, query: list[dict]) -> dict:
        return self.get_items_from_database(
            query=query, collection_name=self.db_collection_name
        )

    async def get_data(self, chain: str, protocol: str) -> dict:
        return self.__get_data(
            query=self.query_all(chain=chain, protocol=protocol),
            collection_name=self.db_collection_name,
        )

    @staticmethod
    def query_all(chain: str, protocol: str = "") -> list[dict]:
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


class db_allRewards2_manager(db_collections_common):
    db_collection_name = "allRewards2"

    async def create_data(self, chain: str, protocol: str) -> dict:
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
        data["id"] = f"{chain}_{protocol}"
        data["datetime"] = datetime.utcnow()

        return data

    async def feed_db(self, chain: str, protocol: str):

        # save as 1 item ( not separated)
        await self.save_item_to_database(
            data=await self.create_data(chain=chain, protocol=protocol),
            collection_name=self.db_collection_name,
        )

    async def __get_data(self, query: list[dict]) -> dict:
        return self.get_items_from_database(
            query=query, collection_name=self.db_collection_name
        )

    async def get_data(self, chain: str, protocol: str) -> dict:
        return self.__get_data(
            query=self.query_all(chain=chain, protocol=protocol),
            collection_name=self.db_collection_name,
        )

    @staticmethod
    def query_all(chain: str, protocol: str = "") -> list[dict]:
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
