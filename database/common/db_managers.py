import logging
from pymongo import MongoClient
from pymongo import errors as MongoErrors

from v3data.config import MONGO_DB_TIMEOUTMS

logger = logging.getLogger(__name__)


class MongoDbManager:
    def __init__(
        self,
        url: str,
        db_name: str,
        collections: dict,
        serverSelectionTimeoutMS: int = MONGO_DB_TIMEOUTMS,
    ):
        """Mongo database helper

        Args:
           url (str): full mongodb url
           db_name (str): database name
           collections (dict): { <collection name>: {<field>:<uniqueness>, ...} ...}
                           example: {
                               "static":
                                       {"id":True,
                                       },
                               "returns":
                                       {"id":True
                                       },
                               }
            serverSelectionTimeoutMS (int): maximum number of milliseconds to timeout connection
        """

        # connect to mongo database
        try:
            self.mongo_client = MongoClient(
                url, serverSelectionTimeoutMS=serverSelectionTimeoutMS
            )
        except MongoErrors.ServerSelectionTimeoutError:
            raise Exception(
                f" Connection timed out using {serverSelectionTimeoutMS} ms. Try increasing this value if u know server is responding"
            )
        except MongoErrors.ConnectionFailure:
            raise Exception("Failed to connect to {}".format(url))
        self.database = self.mongo_client[db_name]

        # Retrieve database collection names
        self.database_collections = self.database.list_collection_names()

        # define collection configurations
        self.collections_config = collections

        # Setup collections and their indexes
        self.configure_collections()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        # xception handling here
        self.mongo_client.close()

    def configure_collections(self):
        """define collection names and create indexes"""
        for coll_name, fields in self.collections_config.items():
            for field, unique in fields.items():
                self.database[coll_name].create_index(field, unique=unique)

    def create_collection(self, coll_name: str, **indexes):
        """Creates a collection if it does not exist.
        Arguments:
           indexes = [ <collection field name>:str = <unique>:bool  ]
        """

        if not coll_name in self.database_collections:
            for field, unique in indexes.items():
                self.database[coll_name].create_index(field, unique=unique)

            # refresh database collection names
            self.database_collections = self.database.list_collection_names()

    def add_item(self, coll_name: str, dbFilter: dict, data: dict, upsert=True):
        """Add or Update item

        Args:
           coll_name (str): collection name
           dbFilter (dict): filter to use as to replacement filter, like { address:<>, chain:<>}
           data (dict): data to save
           upsert (bool, optional): replace or add item. Defaults to True.

        Raises:
           ValueError: if coll_name is not defined at the class init <collections> field
        """

        # check collection configuration exists
        if not coll_name in self.collections_config.keys():
            raise ValueError(
                f" No configuration found for {coll_name} database collection."
            )
        # create collection if it does not exist yet
        self.create_collection(
            coll_name=coll_name, **self.collections_config[coll_name]
        )

        # add/ update to database (add or replace)
        self.database[coll_name].update_one(
            filter=dbFilter, update={"$set": data}, upsert=True
        )

    def replace_item(self, coll_name: str, dbFilter: dict, data: dict, upsert=True):
        """Add or Update item

        Args:
           coll_name (str): collection name
           dbFilter (dict): filter to use as to replacement filter, like { address:<>, chain:<>}
           data (dict): data to save
           upsert (bool, optional): replace or add item. Defaults to True.

        Raises:
           ValueError: if coll_name is not defined at the class init <collections> field
        """

        # check collection configuration exists
        if not coll_name in self.collections_config.keys():
            raise ValueError(
                f" No configuration found for {coll_name} database collection."
            )
        # create collection if it does not exist yet
        self.create_collection(
            coll_name=coll_name, **self.collections_config[coll_name]
        )

        # add/ update to database (add or replace)
        self.database[coll_name].replace_one(
            filter=dbFilter, replacement=data, upsert=True
        )

    def get_items(self, coll_name: str, **kwargs):
        """get items cursor from database

        Args:
           coll_name (str): _description_
           **kwargs:  examples->   --FIND-----------------------
                                   find={  "product_id":<product id>,
                                                 "time": {
                                                   "$lte": <date>,
                                                   "$gte": <date>
                                                     }
                                       }
                                   batch_size=100
                                   sort=[(<field_01>,1), (<field_02>,-1) ]
                                   limit=10

                                   --AGGREGATE-------------------
                                   aggregate=[{  "$match": {
                                                           "time": {"$gte" : date_from, "$lte" : date_stop }
                                                           }
                                               },
                                               { "$group": {
                                                           "_id": "stuff",
                                                           "high": {"$max" : "$price"},
                                                           "low": {"$min": "$price"}
                                                       }
                                               }]
                                   allowDiskUse=<bool>
        """

        # build FIND result
        if "find" in kwargs:
            if "batch_size" in kwargs:
                if "sort" in kwargs:
                    if "limit" in kwargs:
                        return (
                            self.database[coll_name]
                            .find(kwargs["find"], batch_size=kwargs["batch_size"])
                            .sort(kwargs["sort"])
                            .limit(kwargs["limit"])
                        )
                    else:
                        if "limit" in kwargs:
                            return (
                                self.database[coll_name]
                                .find(kwargs["find"], batch_size=kwargs["batch_size"])
                                .sort(kwargs["sort"])
                                .limit(kwargs["limit"])
                            )
                        else:
                            return (
                                self.database[coll_name]
                                .find(kwargs["find"], batch_size=kwargs["batch_size"])
                                .sort(kwargs["sort"])
                            )
                else:
                    return self.database[coll_name].find(
                        kwargs["find"], batch_size=kwargs["batch_size"]
                    )
            else:
                if "sort" in kwargs:
                    if "limit" in kwargs:
                        return (
                            self.database[coll_name]
                            .find(kwargs["find"])
                            .sort(kwargs["sort"])
                            .limit(kwargs["limit"])
                        )
                    else:
                        return (
                            self.database[coll_name]
                            .find(kwargs["find"])
                            .sort(kwargs["sort"])
                        )
                else:
                    if "limit" in kwargs:
                        return (
                            self.database[coll_name]
                            .find(kwargs["find"])
                            .limit(kwargs["limit"])
                        )
                    else:
                        return self.database[coll_name].find(kwargs["find"])

        # build AGGREGATE result
        elif "aggregate" in kwargs:
            if "allowDiskUse" in kwargs:
                return self.database[coll_name].aggregate(
                    kwargs["aggregate"], allowDiskUse=kwargs["allowDiskUse"]
                )
            else:
                return self.database[coll_name].aggregate(kwargs["aggregate"])

    def get_distinct(self, coll_name: str, field: str, condition: dict = {}):
        """get distinct items of a database field

        Args:
            coll_name (str): collection name
            field (str): field to get distinct values from
            condition (dict): like {"dept" : "B"}
        """
        if len(condition.keys()) == 0:
            return self.database[coll_name].distinct(field)
        else:
            return self.database[coll_name].distinct(field, condition)

    # TODO: push_item ( add_item without id involved )
    # TODO: push_items ( add/update multiple items )
    # TODO: add_items ( add/update multiple items )
