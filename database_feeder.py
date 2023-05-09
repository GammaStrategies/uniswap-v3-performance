#
#   Script to update mongoDb with periodic data
#
import os
import sys
import getopt
import logging
import asyncio
from aiocron import crontab

from croniter import croniter
from datetime import datetime, timezone

from v3data import utils

from v3data.enums import Chain, Protocol
from v3data.config import (
    MONGO_DB_URL,
    GAMMA_SUBGRAPH_URLS,
    EXCLUDED_HYPERVISORS,
    DEPLOYMENTS,
)

from database.collection_endpoint import (
    db_returns_manager,
    db_static_manager,
    db_allData_manager,
    db_allRewards2_manager,
    db_allRewards2_external_manager,
    db_aggregateStats_manager,
)


logging.basicConfig(
    format="[%(asctime)s:%(levelname)s:%(name)s]:%(message)s",
    datefmt="%Y/%m/%d %I:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# using gamma subgraph keys to build chain,protocol list
CHAINS_PROTOCOLS = [
    (chain, protocol)
    for protocol in Protocol
    for chain in GAMMA_SUBGRAPH_URLS[protocol].keys()
]


# set cron vars
EXPR_FORMATS = {
    "returns": {
        "daily": "*/60 */2 * * *",  # (At every 60th minute past every 2nd hour. )
        "weekly": "*/60 */12 * * *",  # (At every 60th minute past every 12th hour. )  # can't do every 14 hours
        "biweekly": "0 6 */1 * * ",  # ( At 06:00 on every day-of-month.)
        "monthly": "0 12 */2 * *",  # ( At 12:00 on every 2nd day-of-month.)
    },
    "inSecuence": {  # allData + static hypervisor info
        "mins": "*/30 * * * *",
    },
    "aggregateStats": {
        "mins": "*/15 * * * *",
    },
    "allRewards2": {
        "mins": "*/20 * * * *",
    },
}
EXPR_ARGS = {
    "returns": {
        "daily": [[1]],
        "weekly": [[7]],
        "biweekly": [[14]],
        "monthly": [[30]],
    }
}


# feed jobs
async def feed_database_returns(
    periods: list, current_timestamp: int = None, max_retries: int = 1
):
    name = "returns"
    logger.info(f" Starting database feeding process for {name} data")
    # start time log
    _startime = datetime.utcnow()

    returns_manager = db_returns_manager(mongo_url=MONGO_DB_URL)
    returns_manager._max_retry = max_retries

    # all request at once
    requests = [
        returns_manager.feed_db(
            chain=chain,
            protocol=protocol,
            periods=periods,
            current_timestamp=current_timestamp,
        )
        for chain, protocol in CHAINS_PROTOCOLS
    ]
    await asyncio.gather(*requests)

    # end time log
    logger.info(f" took {get_timepassed_string(_startime)} to complete the {name} feed")


async def feed_database_static():
    name = "static"
    logger.info(f" Starting database feeding process for {name} data")
    logger.debug(f"     chains prot.: {CHAINS_PROTOCOLS}")
    logger.debug(f"     excluded_hyp: {EXCLUDED_HYPERVISORS}")

    # start time log
    _startime = datetime.utcnow()

    # static requests
    static_manager = db_static_manager(mongo_url=MONGO_DB_URL)
    requests = [
        static_manager.feed_db(chain=chain, protocol=protocol)
        for chain, protocol in CHAINS_PROTOCOLS
    ]

    # execute feed
    await asyncio.gather(*requests)

    # end time log
    logger.info(f" took {get_timepassed_string(_startime)} to complete the {name} feed")


async def feed_database_allData():
    name = "allData"
    logger.info(f" Starting database feeding process for {name} data")
    logger.debug(f"     chains prot.: {CHAINS_PROTOCOLS}")
    logger.debug(f"     excluded_hyp: {EXCLUDED_HYPERVISORS}")

    # start time log
    _startime = datetime.utcnow()

    _manager = db_allData_manager(mongo_url=MONGO_DB_URL)
    requests = [
        _manager.feed_db(
            chain=chain,
            protocol=protocol,
        )
        for chain, protocol in CHAINS_PROTOCOLS
    ]

    # execute feed
    await asyncio.gather(*requests)

    # end time log
    logger.info(f" took {get_timepassed_string(_startime)} to complete the {name} feed")


async def feed_all_allRewards2():
    await feed_database_allRewards2()
    await feed_database_allRewards2_externals()


async def feed_database_allRewards2():
    name = "allRewards2"
    logger.info(f" Starting database feeding process for {name} data")
    # start time log
    _startime = datetime.utcnow()

    _manager = db_allRewards2_manager(mongo_url=MONGO_DB_URL)
    requests = [
        _manager.feed_db(
            chain=chain,
            protocol=protocol,
        )
        for chain, protocol in CHAINS_PROTOCOLS
    ]

    # execute feed
    await asyncio.gather(*requests)

    # end time log
    logger.info(f" took {get_timepassed_string(_startime)} to complete the {name} feed")


async def feed_database_allRewards2_externals(current_timestamp: int | None = None):
    name = "allRewards2 external"
    logger.info(f" Starting database feeding process for {name} data")
    # start time log
    _startime = datetime.utcnow()

    _manager = db_allRewards2_external_manager(mongo_url=MONGO_DB_URL)
    requests = [
        _manager.feed_db(
            chain=chain,
            protocol=protocol,
            current_timestamp=current_timestamp,
        )
        for chain, protocol in CHAINS_PROTOCOLS
        if protocol in [Protocol.ZYBERSWAP, Protocol.THENA]
    ]

    # execute feed
    await asyncio.gather(*requests)

    # end time log
    logger.info(f" took {get_timepassed_string(_startime)} to complete the {name} feed")


async def feed_database_aggregateStats():
    name = "aggregateStats"
    logger.info(f" Starting database feeding process for {name} data")
    # start time log
    _startime = datetime.utcnow()

    _manager = db_aggregateStats_manager(mongo_url=MONGO_DB_URL)
    requests = [
        _manager.feed_db(
            chain=chain,
            protocol=protocol,
        )
        for chain, protocol in CHAINS_PROTOCOLS
    ]

    # execute feed
    await asyncio.gather(*requests)

    # end time log
    logger.info(f" took {get_timepassed_string(_startime)} to complete the {name} feed")


# Multiple feeds in one
async def feed_database_inSecuence():
    # start time log
    _startime = datetime.utcnow()

    await feed_database_static()
    await feed_database_allData()

    _endtime = datetime.utcnow()
    if (_endtime - _startime).total_seconds() > (60 * 2):
        # end time log
        logger.warning(
            " Consider increasing cron schedule ->  took {} to complete database feeder loop.".format(
                get_timepassed_string(_startime, _endtime)
            )
        )


async def feed_all():
    await feed_database_static()
    await feed_database_allData()
    await feed_all_allRewards2()
    await feed_database_aggregateStats()


# Manual script execution
async def feed_database_with_historic_data(from_datetime: datetime, periods=None):
    """Fill database with historic

    Args:
        from_datetime (datetime): like datetime(2022, 12, 1, 0, 0, tzinfo=timezone.utc)
        process_quickswap (bool): should quickswap protocol be included ?
        periods (list): list of periods as ["daily", "weekly", "monthly"]
    """
    # final log var
    processed_datetime_strings = list()

    last_time = datetime.utcnow()

    # define periods when empty
    if not periods:
        periods = list(EXPR_ARGS["returns"].keys())

    logger.info(
        f" Feeding database with historic data  periods:{periods} chains/protocols:{CHAINS_PROTOCOLS}"
    )

    for period in periods:
        cron_ex_format = EXPR_FORMATS["returns"][period]

        # create croniter
        c_iter = croniter(expr_format=cron_ex_format, start_time=from_datetime)
        current_timestamp = c_iter.get_next(start_time=from_datetime.timestamp())

        # set utils now
        last_timestamp = last_time.timestamp()
        while last_timestamp > current_timestamp:
            txt_timestamp = "{:%Y-%m-%d  %H:%M:%S}".format(
                datetime.utcfromtimestamp(current_timestamp)
            )
            processed_datetime_strings.append(txt_timestamp)
            logger.info(" Feeding {} database at  {}".format(period, txt_timestamp))

            # database feed
            await asyncio.gather(
                feed_database_returns(
                    periods=EXPR_ARGS["returns"][period][0],
                    current_timestamp=int(current_timestamp),
                    max_retries=0,
                ),
                feed_database_allRewards2_externals(
                    current_timestamp=int(current_timestamp)
                ),
            )

            # set next timestamp
            current_timestamp = c_iter.get_next(start_time=current_timestamp)

    logger.info(" Processed dates: {} ".format(processed_datetime_strings))


def convert_commandline_arguments(argv) -> dict:
    """converts command line arguments to a dictionary of those

    Arguments:
       argv {} --

    Returns:
       dict --
    """

    # GET COMMAND LINE ARGUMENTS
    prmtrs = dict()  # the parameters we will pass to simulation creation
    prmtrs["historic"] = False

    try:
        opts, args = getopt.getopt(argv, "hs:m:", ["historic", "start=", "manual="])
    except getopt.GetoptError as err:
        print("             <filename>.py <options>")
        print("Options:")
        print(" -s <start date> or --start=<start date>")
        print(" -m <option> or --manual=<option>")
        print("           <option> being: secuence")
        print(" ")
        print(" ")
        print(" ")
        print("to feed database with current data  (infinite loop):")
        print("             <filename>.py")
        print("to feed database with historic data: (no quickswap)")
        print("             <filename>.py -h")
        print("             <filename>.py -s <start date as %Y-%m-%d>")
        print("error message: {}".format(err.msg))
        print("opt message: {}".format(err.opt))
        sys.exit(2)

    # loop and retrieve each command
    for opt, arg in opts:
        if opt in ("-s", "start="):
            # todo: check if it is a date
            prmtrs["from_datetime"] = datetime.strptime((arg).strip(), "%Y-%m-%d")
            prmtrs["historic"] = True
        elif opt in ("-h", "historic"):
            prmtrs["historic"] = True
        elif opt in ("-m", "manual="):
            prmtrs["manual"] = arg
    return prmtrs


def get_timepassed_string(start_time: datetime, end_time: datetime = None) -> str:
    if not end_time:
        end_time = datetime.utcnow()
    _timelapse = end_time - start_time
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


# set functions here
EXPR_FUNCS = {
    "returns": feed_database_returns,
    "static": feed_database_static,
    "allData": feed_database_allData,
    "allRewards2": feed_all_allRewards2,
    "aggregateStats": feed_database_aggregateStats,
    "inSecuence": feed_database_inSecuence,
}

if __name__ == "__main__":
    # convert command line arguments to dict variables
    cml_parameters = convert_commandline_arguments(sys.argv[1:])

    if cml_parameters["historic"]:
        # historic feed

        from_datetime = cml_parameters.get(
            "from_datetime", datetime(2022, 12, 1, 0, 0, tzinfo=timezone.utc)
        )

        logger.info(" ")
        logger.info(
            " Feeding database with historic data from {:%Y-%m-%d} to now *********************   ********************* ".format(
                from_datetime
            )
        )
        logger.info(" ")

        # start time log
        _startime = datetime.utcnow()

        asyncio.run(feed_database_with_historic_data(from_datetime=from_datetime))

        # end time log
        logger.info(
            " took {} to complete the historic feed".format(
                get_timepassed_string(_startime)
            )
        )
    elif "manual" in cml_parameters:
        logger.info(" Starting one-time manual execution ")
        logger.info(f"     chains prot.: {CHAINS_PROTOCOLS}")
        logger.info(f"     excluded_hyp: {EXCLUDED_HYPERVISORS}")

        # start time log
        _startime = datetime.utcnow()

        asyncio.run(feed_all())

        # end time log
        logger.info(
            " took {} to complete the sequencer feed".format(
                get_timepassed_string(_startime)
            )
        )
    else:
        # actual feed
        logger.info(" Starting loop feed  ")

        # create event loop
        loop = asyncio.new_event_loop()

        # create cron jobs ( utc timezone )
        crons = {}
        for function, formats in EXPR_FORMATS.items():
            for key, cron_ex_format in EXPR_FORMATS[function].items():
                args = EXPR_ARGS.get(function, {}).get(key)
                crons[f"{function}_{key}"] = crontab(
                    cron_ex_format,
                    func=EXPR_FUNCS[function],
                    args=args if args else (),
                    loop=loop,
                    start=True,
                    tz=timezone.utc,
                )

        # run forever
        asyncio.set_event_loop(loop)
        loop.run_forever()
