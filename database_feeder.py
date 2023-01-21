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

# set cron vars
EXPR_FORMATS = {
    "daily": "0 0 * * *",
    "weekly": "2 0 * * mon",
    "monthly": "5 0 * * mon#1",
}
EXPR_PERIODS = {
    "daily": [1],
    "weekly": [7],
    "monthly": [30],
}


# cron job func
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


async def feed_database_with_historic_data(
    from_datetime: datetime, process_quickswap=False
):
    """Fill database with historic

    Args:
        from_datetime (datetime): like datetime(2022, 12, 1, 0, 0, tzinfo=dt.timezone.utc)
    """

    last_time = datetime.utcnow()

    for period, cron_ex_format in EXPR_FORMATS.items():
        # create croniter
        c_iter = croniter(expr_format=cron_ex_format, start_time=from_datetime)
        current_timestamp = c_iter.get_next(start_time=from_datetime.timestamp())

        # set utils now
        utils.static_datetime_utcnow = datetime.utcfromtimestamp(current_timestamp)
        last_timestamp = last_time.timestamp()
        while last_timestamp > current_timestamp:
            print(" ")
            print(
                " Feeding {} database at  {:%Y-%m-%d  %H:%M:%S}  ".format(
                    period, datetime.utcfromtimestamp(current_timestamp)
                )
            )
            print(" ")

            # database feed
            await feed_database_average_returns(
                periods=EXPR_PERIODS[period], process_quickswap=process_quickswap
            )

            # set next timestamp
            current_timestamp = c_iter.get_next(start_time=current_timestamp)

            # set utils now
            utils.static_datetime_utcnow = datetime.utcfromtimestamp(current_timestamp)


if __name__ == "__main__":

    # create event loop
    loop = asyncio.new_event_loop()

    # create cron jobs ( utc timezone )
    crons = {}
    for period, cron_ex_format in EXPR_FORMATS.items():
        crons[period] = crontab(
            cron_ex_format,
            func=feed_database_average_returns,
            args=[EXPR_PERIODS[period], True],
            loop=loop,
            start=True,
            tz=dt.timezone.utc,
        )

    # run forever
    asyncio.set_event_loop(loop)
    asyncio.get_event_loop().run_forever()
