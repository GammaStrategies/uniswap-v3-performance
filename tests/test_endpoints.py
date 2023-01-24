import sys
import os
import datetime as dt
import logging
import asyncio


logging.basicConfig(
    format="[%(asctime)s:%(levelname)s:%(name)s]:%(message)s",
    datefmt="%Y/%m/%d %I:%M:%S",
    level=logging.INFO,
)

# append parent directory pth
CURRENT_FOLDER = os.path.dirname(os.path.realpath(__file__))
PARENT_FOLDER = os.path.dirname(CURRENT_FOLDER)
sys.path.append(PARENT_FOLDER)

import v3data
from v3data.constants import PROTOCOL_UNISWAP_V3, PROTOCOL_QUICKSWAP
from v3data.config import MONGO_DB_URL, GAMMA_SUBGRAPH_URLS

from v3data.bollingerbands import BollingerBand
from v3data.charts.base_range import BaseLimit
from v3data.charts.benchmark import Benchmark

from v3data.toplevel import TopLevelData


from database.collection_returns import db_returns_manager
from database.collection_static import db_static_manager
from v3data.common import hypervisor


logger = logging.getLogger(__name__)


async def base_range_chart_all(protocol: str, chain: str, days: int = 20):
    hours = days * 24
    baseLimitData = BaseLimit(protocol=protocol, hours=hours, chart=True, chain=chain)
    chart_data = await baseLimitData.all_rebalance_ranges()
    return chart_data


async def recent_fees(protocol: str, chain: str, hours: int = 24):
    top_level = TopLevelData(protocol, chain)
    recent_fees = await top_level.recent_fees(hours)

    return {"periodHours": hours, "fees": recent_fees}


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

    # base range chart all
    # data = asyncio.run(
    #    base_range_chart_all(protocol=PROTOCOL_UNISWAP_V3, chain="mainnet", days=20)
    # )

    # recent fees
    data = asyncio.run(
        recent_fees(protocol=PROTOCOL_UNISWAP_V3, chain="mainnet", hours=24 * 2)
    )

    # end time log
    print(" took {} to complete the script".format(get_timepassed_string(_startime)))
