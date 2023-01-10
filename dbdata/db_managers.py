

from pymongo import MongoClient

class MongoDbManager():
    def __init__(self, url: str, db_name: str, collections:dict):
        """ Mongo database helper

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
         """        

        # define database var
        mongo_client = MongoClient(url)
        self.database = mongo_client[db_name]

        # Retrieve database collection names
        self.database_collections = self.database.list_collection_names(include_system_collections=False)

        # define collection configurations
        self.collections_config = collections

        # Setup collections and their indexes
        self.configure_collections()
        
    def configure_collections(self):
        """ define collection names and create indexes
        """
        for coll_name, fields in self.collections_config.items():
            for field,unique in fields.items():
                self.database[coll_name].create_index(field, unique=unique)
  
    def create_collection(self, coll_name:str, **indexes):
        """ Creates a collection if it does not exist.
         Arguments:
            indexes = [ <collection field name>:str = <unique>:bool  ]
         """

        if not coll_name in self.database_collections:
            for field,unique in indexes.items():
                self.database[coll_name].create_index(field, unique=unique)

            # refresh database collection names 
            self.database_collections = self.database.list_collection_names(include_system_collections=False)


    def add_item(self, coll_name:str, item_id:str, data:dict, upsert=True):
        """ Add or Update item

         Args:
            coll_name (str): collection name
            item_id (str): id to be saved as
            data (dict): data to save
            upsert (bool, optional): replace or add item. Defaults to True.

         Raises:
            ValueError: if coll_name is not defined at the class init <collections> field
        """        

        # check collection configuration exists
        if not coll_name in self.collections_config.keys():
            raise ValueError(f" No configuration found for {coll_name} database collection.")
        # create collection if it does not exist yet
        self.create_collection(coll_name=coll_name, **self.collections_config[coll_name])

        # add/ update to database (add or replace)
        self.database[coll_name].update_one({"_id": item_id},{"$set": data}, upsert=upsert)

    def get_item(self, coll_name:str, **kwargs):
        """ get items cursor from database

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
                                    sort={<field_01>:1, <field_02>:-1 }

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
                    return self.database[coll_name].find(kwargs["find"],batch_size=kwargs["batch_size"]).sort(kwargs["sort"])
                else:
                    return self.database[coll_name].find(kwargs["find"],batch_size=kwargs["batch_size"])
            else:
                if "sort" in kwargs:
                    return self.database[coll_name].find(kwargs["find"]).sort(kwargs["sort"])
                else:
                    return self.database[coll_name].find(kwargs["find"])
        
        # build AGGREGATE result
        elif "aggregate" in kwargs:
            if "allowDiskUse" in kwargs:
                return self.database[coll_name].aggregate(kwargs["aggregate"],allowDiskUse=kwargs["allowDiskUse"])
            else:
                return self.database[coll_name].aggregate(kwargs["aggregate"])


    # TODO: push_item ( add_item without id involved )
    # TODO: push_items ( add/update multiple items )
    # TODO: add_items ( add/update multiple items )





