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


#
async def feed_database_average_returns(periods: list, process_quickswap=True):
    logger.debug(" Starting database feeding process for average results data")
    returns_manager = db_returns_manager(mongo_url=MONGO_DB_URL)
    requests = [
        returns_manager.feed_db(
            chain=chain, protocol=PROTOCOL_UNISWAP_V3, periods=periods
        )
        for chain in GAMMA_SUBGRAPH_URLS[PROTOCOL_UNISWAP_V3].keys()
    ]

    if process_quickswap:
        requests.extend(
            [
                returns_manager.feed_db(
                    chain=chain, protocol=PROTOCOL_QUICKSWAP, periods=periods
                )
                for chain in GAMMA_SUBGRAPH_URLS[PROTOCOL_QUICKSWAP].keys()
            ]
        )

    await asyncio.gather(*requests)


# create event loop
loop = asyncio.new_event_loop()

# set cron vars
expr_formats = {
    "daily": "0 0 * * *",
    "weekly": "2 0 * * mon",
    "monthly": "5 0 * * mon#1",
}
expr_periods = {
    "daily": [1],
    "weekly": [7],
    "monthly": [30],
}
crons = {}

# create cron jobs ( utc timezone )
for period, cron_ex_format in expr_formats.items():
    crons[period] = crontab(
        cron_ex_format,
        func=feed_database_average_returns,
        args=[expr_periods[period], True],
        loop=loop,
        start=True,
        tz=dt.timezone.utc,
    )

# run forever
asyncio.set_event_loop(loop)
asyncio.get_event_loop().run_forever()
