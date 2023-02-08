import logging
import asyncio
from dataclasses import dataclass, field, asdict, InitVar
from math import log

from database.common.db_managers import MongoDbManager
from v3data.config import MONGO_DB_COLLECTIONS

logger = logging.getLogger(__name__)


class db_collections_common:
    def __init__(
        self,
        mongo_url: str,
        db_name: str = "gamma_db_v1",
        db_collections: dict = MONGO_DB_COLLECTIONS,
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
        # add item by item to database
        for key, item in data.items():
            # add to mongodb
            await self.save_item_to_database(data=item, collection_name=collection_name)

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
        try:
            with MongoDbManager(
                url=self._db_mongo_url,
                db_name=self._db_name,
                collections=self._db_collections,
            ) as _db_manager:
                # add to mongodb
                _db_manager.add_item(
                    coll_name=collection_name, dbFilter={"id": data["id"]}, data=data
                )
        except Exception as e:
            logging.getLogger(__name__).exception(
                " Unable to save data to mongo's {} collection.  error-> {}".format(
                    collection_name, e
                )
            )

    async def replace_item_to_database(
        self,
        data: dict,
        collection_name: str,
    ):
        try:
            with MongoDbManager(
                url=self._db_mongo_url,
                db_name=self._db_name,
                collections=self._db_collections,
            ) as _db_manager:
                # add to mongodb
                _db_manager.replace_item(
                    coll_name=collection_name, dbFilter={"id": data["id"]}, data=data
                )
        except Exception as e:
            logging.getLogger(__name__).exception(
                " Unable to replace data in mongo's {} collection.  error-> {}".format(
                    collection_name, e
                )
            )

    def query_items_from_database(
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

    def get_items_from_database(self, collection_name: str, **kwargs) -> list:
        with MongoDbManager(
            url=self._db_mongo_url,
            db_name=self._db_name,
            collections=self._db_collections,
        ) as _db_manager:
            result = _db_manager.get_items(coll_name=collection_name, **kwargs)
            result = list(result)
        return result

    # TOOLING
    @staticmethod
    def bytes_needed(n):
        if n == 0:
            return 1
        if n < 0:
            return int(log(abs(n), 256)) + 2
        return int(log(n, 256)) + 1

    @staticmethod
    def convert_decimal_to_d128(item: dict) -> dict:
        """Converts a dictionary decimal values to BSON.decimal128, recursive...
            The function iterates a dict looking for types of Decimal128 and converts them to Decimal.

        Args:
            item (dict):

        Returns:
            dict: converted values dict
        """
        if item is None:
            return None

        for k, v in list(item.items()):
            if isinstance(v, dict):
                MongoDbManager.convert_decimal_to_d128(v)
            elif isinstance(v, list):
                for l in v:
                    MongoDbManager.convert_decimal_to_d128(l)
            elif isinstance(v, Decimal):
                item[k] = Decimal128(str(v))

        return item

    @staticmethod
    def convert_d128_to_decimal(item: dict) -> dict:
        """Converts a dictionary decimal128 values to decimal, recursive...
            The function iterates a dict looking for types of Decimal and converts them to Decimal128.

        Args:
            item (dict):

        Returns:
            dict: converted values dict
        """
        if item is None:
            return None

        for k, v in list(item.items()):
            if isinstance(v, dict):
                MongoDbManager.convert_d128_to_decimal(v)
            elif isinstance(v, list):
                for l in v:
                    MongoDbManager.convert_d128_to_decimal(l)
            elif isinstance(v, Decimal128):
                item[k] = v.to_decimal()

        return item
