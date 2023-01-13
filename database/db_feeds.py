import logging


from v3data.config import MONGO_DB_URL
from database.db_data_format import create_db_returns, create_db_static_hypervisor_info
from database.db_managers import MongoDbManager
from database.db_data_models import tool_mongodb_general, tool_database_id


# TODO: -> currently hardcoding mongo database name and collections untill we have more usecases for the database model
MONGO_DB_NAME = "gamma_db_v1"
MONGO_DB_COLLECTIONS = {"static": {"id": True}, "returns": {"id": True}}

logger = logging.getLogger(__name__)


# calculations
async def feed_db_with_returns(chain: str, protocol: str):

    for days in [1, 7, 30]:
        await save_items_to_database(
            mongo_srv_url=MONGO_DB_URL,
            db_name=MONGO_DB_NAME,
            collections=MONGO_DB_COLLECTIONS,
            data=await create_db_returns(
                chain=chain, protocol=protocol, period_days=days
            ),
            collection_name="returns",
        )

async def feed_db_with_static_hypInfo(chain: str, protocol: str):

    await save_items_to_database(
        mongo_srv_url=MONGO_DB_URL,
        db_name=MONGO_DB_NAME,
        collections=MONGO_DB_COLLECTIONS,
        data=await create_db_static_hypervisor_info(chain=chain, protocol=protocol),
        collection_name="static",
    )




# actual db saving
async def save_items_to_database(
    mongo_srv_url: str,
    db_name: str,
    collections: dict,
    data: list[tool_mongodb_general],
    collection_name: str,
):
    """ Save dictionary values to the database collection replacing any equal id defined

    Args:
        mongo_srv_url (str): full url of the mongo database, including user passwd
        db_name (str): mongo database name
        collections (dict): collection format as stated in MongoDbManager
        data (list): data list following tool_mongodb_general class to be saved to database in a dict format
        collection_name (str): collection name to save data to
    """

    # create database manager/connector
    try:
        db_manager = MongoDbManager(
            url=mongo_srv_url, db_name=db_name, collections=collections
        )
    except Exception as e:
        logger.exception(e)
        # do not continue 
        return

    # add item by item to database
    for key, item in data.items():
        # add to mongodb
        save_item_to_database(
            db_manager=db_manager, data=item, collection_name=collection_name
        )

def save_item_to_database(
    db_manager: MongoDbManager,
    data: tool_database_id,
    collection_name: str,
):
    try:
        # enforce type match
        if not issubclass(type(data), tool_mongodb_general) and not issubclass(
            type(data), tool_database_id
        ):
            logger.exception(
                " data passed to be saved to mongodb is in an incorrect format".format()
            )

        # add to mongodb
        db_manager.add_item(
            coll_name=collection_name, dbFilter={"id": data.id}, data=data.asdict()
        )
    except Exception as e:
        logger.exception(
            " Unable to save data to mongo's {} collection.  error-> {}".format(
                collection_name, e
            )
        )
