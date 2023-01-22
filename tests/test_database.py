import sys
import os
import datetime as dt
import logging
import asyncio
import csv
from pathlib import Path

# force test environment
# os.environ["MONGO_DB_URL"] = "mongodb://localhost:27072"

logging.basicConfig(
    format="[%(asctime)s:%(levelname)s:%(name)s]:%(message)s",
    datefmt="%Y/%m/%d %I:%M:%S",
    level=logging.INFO,
)

# append parent directory pth
CURRENT_FOLDER = os.path.dirname(os.path.realpath(__file__))
PARENT_FOLDER = os.path.dirname(CURRENT_FOLDER)
sys.path.append(PARENT_FOLDER)


from v3data.constants import PROTOCOL_UNISWAP_V3, PROTOCOL_QUICKSWAP
from v3data.config import MONGO_DB_URL, GAMMA_SUBGRAPH_URLS

from database.collection_returns import db_returns_manager
from database.collection_static import db_static_manager
from v3data.common import hypervisor

logger = logging.getLogger(__name__)


async def test_put_data_to_Mongodb_v1():

    protocols = [PROTOCOL_UNISWAP_V3, PROTOCOL_QUICKSWAP]
    chains_protocols = [
        (chain, protocol)
        for protocol in protocols
        for chain in GAMMA_SUBGRAPH_URLS[protocol].keys()
    ]

    # return requests
    # returns_manager = db_returns_manager(mongo_url=MONGO_DB_URL)
    # requests = [returns_manager.feed_db(chain=chain, protocol=protocol) for chain,protocol in chains_protocols]

    # static requests
    static_manager = db_static_manager(mongo_url=MONGO_DB_URL)
    requests = [
        static_manager.feed_db(chain=chain, protocol=protocol)
        for chain, protocol in chains_protocols
    ]

    # execute queries
    await asyncio.gather(*requests)


async def test_get_data_from_Mongodb_v1():

    chains = ["mainnet", "optimism", "polygon", "arbitrum", "celo"]

    returns_manager = db_returns_manager(mongo_url=MONGO_DB_URL)
    result_requests = [
        returns_manager.get_data(
            query=db_returns_manager.query_hypervisors_average(chain=chain)
        )
        for chain in ["mainnet", "optimism", "polygon", "arbitrum", "celo"]
    ]
    result_responses = {
        chains[idx]: list(x)
        for idx, x in enumerate(await asyncio.gather(*result_requests))
    }


async def test_get_data_from_Mongodb_v2():

    protocols = [PROTOCOL_UNISWAP_V3, PROTOCOL_QUICKSWAP]
    chains_protocols = [
        (chain, protocol)
        for protocol in protocols
        for chain in GAMMA_SUBGRAPH_URLS[protocol].keys()
    ]
    for chain, protocol in chains_protocols:
        # start time log
        _startime = dt.datetime.utcnow()

        data_result = await hypervisor.hypervisors_average_return(protocol, chain)
        # end time log
        print(
            "[{} {}]  took {} to get hypervisors return data".format(
                chain, protocol, get_timepassed_string(_startime)
            )
        )


def get_timepassed_string(start_time: dt.datetime) -> str:
    _timelapse = dt.datetime.utcnow() - start_time
    _passed = _timelapse.total_seconds()
    if _passed < 60:
        _timelapse_unit = "seconds"
    elif _passed < 60 * 60:
        _timelapse_unit = "minutes"
        _passed /= 60
    elif _passed < 60 * 60 * 24:
        _timelapse_unit = "hours"
        _passed /= 60 * 60
    return "{:,.2f} {}".format(_passed, _timelapse_unit)


# TESTING
if __name__ == "__main__":
    # start time log
    _startime = dt.datetime.utcnow()


    asyncio.run(test_get_data_from_Mongodb_v2())

    # end time log
    print(" took {} to complete the script".format(get_timepassed_string(_startime)))
