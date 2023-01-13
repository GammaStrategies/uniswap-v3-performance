import sys
import os
import datetime as dt
import logging
import asyncio
import csv
from pathlib import Path

# force test environment
#os.environ["MONGO_DB_URL"] = "mongodb://localhost:27027"


# append parent directory pth
CURRENT_FOLDER = os.path.dirname(os.path.realpath(__file__))
PARENT_FOLDER = os.path.dirname(CURRENT_FOLDER)
sys.path.append(PARENT_FOLDER)

from database import db_managers
from database import db_queries
from database.db_data_models import (
    tool_mongodb_general,
    tool_database_id,
    hypervisor_return,
    hypervisor_fees,
    hypervisor_impermanent,
    hypervisor_static,
    pool,
    token,
)
from v3data.constants import PROTOCOL_UNISWAP_V3, PROTOCOL_QUICKSWAP

from v3data import hypervisor
from v3data import hypes

from database.db_feeds import feed_db_with_returns, feed_db_with_static_hypInfo


logger = logging.getLogger(__name__)



async def test_put_data_to_Mongodb():

    for chain in ["mainnet", "optimism", "polygon", "arbitrum", "celo"]:

        protocol = PROTOCOL_UNISWAP_V3

        await asyncio.gather(
            feed_db_with_returns(chain=chain, protocol=protocol),
            feed_db_with_static_hypInfo(chain=chain, protocol=protocol),
        )

        if chain == "polygon":
            protocol = PROTOCOL_QUICKSWAP
            await asyncio.gather(
                feed_db_with_returns(chain=chain, protocol=protocol),
                feed_db_with_static_hypInfo(chain=chain, protocol=protocol),
            )

async def test_get_data_from_Mongo():

    for chain in ["mainnet", "optimism", "polygon", "arbitrum", "celo"]:
        for period in [1,7,24]: # TODO: periodless
            query = db_queries.db_returns_queries.hypervisors_average(chain, period)



asyncio.run(test_put_data_to_Mongodb())
