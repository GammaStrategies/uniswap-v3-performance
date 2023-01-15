#
#   Script to update mongoDb with periodic data
#
import os
import logging
import asyncio
from aiocron import crontab

from v3data.constants import PROTOCOL_UNISWAP_V3, PROTOCOL_QUICKSWAP
from v3data.config import MONGO_DB_URL, GAMMA_SUBGRAPH_URLS

from database.collection_returns import db_returns_manager
from database.collection_static import db_static_manager


logging.basicConfig(
    format="[%(asctime)s:%(levelname)s:%(name)s]:%(message)s",
    datefmt="%Y/%m/%d %I:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# using gamma subgraph keys to build chain,protocol list
PROTOCOLS = [PROTOCOL_UNISWAP_V3, PROTOCOL_QUICKSWAP]
CHAINS_PROTOCOLS = [
    (chain, protocol)
    for protocol in PROTOCOLS
    for chain in GAMMA_SUBGRAPH_URLS[protocol].keys()
]


# every day
@crontab("0 0 * * *", start=True)
async def feed_database_daily_average_returns():
    logger.debug(" Starting daily database feeding process for average results data")
    periods = [1]
    returns_manager = db_returns_manager(mongo_url=MONGO_DB_URL)
    requests = [
        returns_manager.feed_db(
            chain=chain, protocol=PROTOCOL_UNISWAP_V3, periods=periods
        )
        for chain, procol in CHAINS_PROTOCOLS
    ]

    await asyncio.gather(*requests)


# every week
@crontab("2 0 * * mon", start=True)
async def feed_database_weekly_average_returns():
    logger.debug(" Starting weekly database feeding process for average results data")
    periods = [7]
    returns_manager = db_returns_manager(mongo_url=MONGO_DB_URL)
    requests = [
        returns_manager.feed_db(
            chain=chain, protocol=PROTOCOL_UNISWAP_V3, periods=periods
        )
        for chain in GAMMA_SUBGRAPH_URLS[PROTOCOL_UNISWAP_V3].keys()
    ]
    requests.extend(
        [
            returns_manager.feed_db(
                chain=chain, protocol=PROTOCOL_QUICKSWAP, periods=periods
            )
            for chain in GAMMA_SUBGRAPH_URLS[PROTOCOL_QUICKSWAP].keys()
        ]
    )

    await asyncio.gather(*requests)


# every month
@crontab("5 0 * * mon#1", start=True)
async def feed_database_monthly_average_returns():
    logger.debug(" Starting monthly database feeding process for average results data")
    periods = [30]
    returns_manager = db_returns_manager(mongo_url=MONGO_DB_URL)
    requests = [
        returns_manager.feed_db(
            chain=chain, protocol=PROTOCOL_UNISWAP_V3, periods=periods
        )
        for chain in GAMMA_SUBGRAPH_URLS[PROTOCOL_UNISWAP_V3].keys()
    ]
    requests.extend(
        [
            returns_manager.feed_db(
                chain=chain, protocol=PROTOCOL_QUICKSWAP, periods=periods
            )
            for chain in GAMMA_SUBGRAPH_URLS[PROTOCOL_QUICKSWAP].keys()
        ]
    )

    await asyncio.gather(*requests)


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
asyncio.get_event_loop().run_forever()
