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

from v3data.constants import PROTOCOL_UNISWAP_V3, PROTOCOL_QUICKSWAP
from v3data.config import MONGO_DB_URL, GAMMA_SUBGRAPH_URLS, EXCLUDED_HYPERVISORS

from database.collection_endpoint import (
    db_returns_manager,
    db_static_manager,
    db_allData_manager,
    db_allRewards2_manager,
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
    for protocol in [PROTOCOL_UNISWAP_V3, PROTOCOL_QUICKSWAP]
    for chain in GAMMA_SUBGRAPH_URLS[protocol].keys()
]

# set cron vars
EXPR_FORMATS = {
    "average_returns": {
        "daily": "0 0 * * *",
        "weekly": "2 0 * * mon",
        "monthly": "5 0 * * mon#1",
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
    "average_returns": {
        "daily": [[1], True],
        "weekly": [[7], True],
        "monthly": [[30], True],
    }
}

# feed jobs
async def feed_database_average_returns(periods: list, process_quickswap=True):
    logger.info(" Starting database feeding process for average results data")
    returns_manager = db_returns_manager(mongo_url=MONGO_DB_URL)
    requests = [
        returns_manager.feed_db(chain=chain, protocol=protocol, periods=periods)
        for chain, protocol in CHAINS_PROTOCOLS
        if (not process_quickswap and not protocol == PROTOCOL_QUICKSWAP)
    ]

    await asyncio.gather(*requests)


async def feed_database_static():
    name = "static"
    logger.info(f" Starting database feeding process for {name} data")
    logger.info(f"     chains prot.: {CHAINS_PROTOCOLS}")
    logger.info(f"     excluded_hyp: {EXCLUDED_HYPERVISORS}")

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
    logger.info(f"     chains prot.: {CHAINS_PROTOCOLS}")
    logger.info(f"     excluded_hyp: {EXCLUDED_HYPERVISORS}")

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
    # await feed_database_allRewards2()

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
    await feed_database_allRewards2()
    await feed_database_aggregateStats()


# Manual script execution
async def feed_database_with_historic_data(
    from_datetime: datetime, process_quickswap=True, periods=[]
):
    """Fill database with historic

    Args:
        from_datetime (datetime): like datetime(2022, 12, 1, 0, 0, tzinfo=timezone.utc)
        process_quickswap (bool): should quickswap protocol be included ?
        periods (list): list of periods as ["daily", "weekly", "monthly"]
    """

    last_time = datetime.utcnow()

    # define periods when empty
    if len(periods) == 0:
        periods = EXPR_ARGS["average_returns"].keys()

    for period in periods:
        cron_ex_format = EXPR_FORMATS["average_returns"][period]

        # create croniter
        c_iter = croniter(expr_format=cron_ex_format, start_time=from_datetime)
        current_timestamp = c_iter.get_next(start_time=from_datetime.timestamp())

        # set utils now
        utils.STATIC_DATETIME_UTCNOW = datetime.utcfromtimestamp(current_timestamp)
        last_timestamp = last_time.timestamp()
        while last_timestamp > current_timestamp:
            logger.info(
                " Feeding {} database at  {:%Y-%m-%d  %H:%M:%S}  ".format(
                    period, datetime.utcfromtimestamp(current_timestamp)
                )
            )

            # database feed
            await feed_database_average_returns(
                periods=EXPR_PERIODS["average_returns"][period],
                process_quickswap=process_quickswap,
            )

            # set next timestamp
            current_timestamp = c_iter.get_next(start_time=current_timestamp)

            # set utils now
            utils.STATIC_DATETIME_UTCNOW = datetime.utcfromtimestamp(current_timestamp)

    # reset utils now
    utils.STATIC_DATETIME_UTCNOW = None


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
            prmtrs["from_datetime"] = datetime.strptime(arg, "%Y-%m-%d")
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
    "average_returns": feed_database_average_returns,
    "static": feed_database_static,
    "allData": feed_database_allData,
    "allRewards2": feed_database_allRewards2,
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

        logger.info(
            " Feeding database with historic data from {:%Y-%m-%d} to now".format(
                from_datetime
            )
        )

        # start time log
        _startime = datetime.utcnow()

        # TODO: add quickswap command line args
        asyncio.run(
            feed_database_with_historic_data(
                from_datetime=from_datetime, process_quickswap=False
            )
        )

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
        # maybe log cron jobs using https://github.com/bradymholt/cron-expression-descriptor ??

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
