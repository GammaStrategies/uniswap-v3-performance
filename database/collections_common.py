import logging
import asyncio
from dataclasses import dataclass, field, asdict, InitVar
from math import log

from database.common.db_managers import MongoDbManager


logger = logging.getLogger(__name__)


class db_collections_common:
    def __init__(
        self,
        mongo_url: str,
        db_name: str = "gamma_db_v1",
        db_collections: dict = {
            "static": {"id": True},
            "returns": {"id": True},
            "allData": {"id": True},  # id = network
            "allRewards2": {"id": True},  # id = network
        },
    ):
        # TODO: -> currently hardcoding optional mongo database name and collections untill we have more usecases for the database model

        self._db_mongo_url = mongo_url
        self._db_name = db_name
        self._db_collections = db_collections

    # actual db saving
    async def save_items_to_database(
        self,
        data: dict,
        collection_name: str,
    ):
        """Save dictionary values to the database collection replacing any equal id defined

        Args:
            data (list): data list following tool_mongodb_general class to be saved to database in a dict format
            collection_name (str): collection name to save data to
        """

        # create database manager/connector
        with MongoDbManager(
            url=self._db_mongo_url,
            db_name=self._db_name,
            collections=self._db_collections,
        ) as _db_manager:

            # add item by item to database
            for key, item in data.items():
                # add to mongodb
                self.__add_item_to_database(
                    db_manager=_db_manager, data=item, collection_name=collection_name
                )

    async def save_item_to_database(
        self,
        data: dict,
        collection_name: str,
    ):
        """Save dictionary values to the database collection replacing any equal id defined

        Args:
            data (list): data list following tool_mongodb_general class to be saved to database in a dict format
            collection_name (str): collection name to save data to
        """

        # create database manager/connector
        with MongoDbManager(
            url=self._db_mongo_url,
            db_name=self._db_name,
            collections=self._db_collections,
        ) as _db_manager:
            # add to mongodb
            self.__add_item_to_database(
                db_manager=_db_manager, data=data, collection_name=collection_name
            )

    def __add_item_to_database(
        self,
        db_manager: MongoDbManager,
        data: dict,
        collection_name: str,
    ):
        try:
            # add to mongodb
            db_manager.add_item(
                coll_name=collection_name, dbFilter={"id": data["id"]}, data=data
            )
        except Exception as e:
            logger.exception(
                " Unable to save data to mongo's {} collection.  error-> {}".format(
                    collection_name, e
                )
            )

    def create_db_manager(self) -> MongoDbManager:
        # create database manager/connector
        try:
            return MongoDbManager(
                url=self._db_mongo_url,
                db_name=self._db_name,
                collections=self._db_collections,
            )
        except Exception as e:
            logger.exception(e)
            # do not continue
        return None

    def get_items_from_database(
        self,
        query: list[dict],
        collection_name: str,
    ) -> list:
        # db_manager = self.create_db_manager()
        with MongoDbManager(
            url=self._db_mongo_url,
            db_name=self._db_name,
            collections=self._db_collections,
        ) as _db_manager:
            result = list(
                _db_manager.get_items(coll_name=collection_name, aggregate=query)
            )
        return result

    # TOOLING
    @staticmethod
    def bytes_needed(n):
        if n == 0:
            return 1
        if n < 0:
            return int(log(abs(n), 256)) + 2
        return int(log(n, 256)) + 1
