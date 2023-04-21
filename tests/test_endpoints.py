import sys
import os
from datetime import datetime, timedelta
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

import v3data.common.analytics

from v3data.charts.base_range import BaseLimit
from v3data.toplevel import TopLevelData
from v3data.accounts import AccountInfo
from v3data.common import hypervisor
from v3data.enums import Chain, Protocol
from v3data.hype_fees.fees_yield import fee_returns_all

logger = logging.getLogger(__name__)


async def base_range_chart_all(protocol: Protocol, chain: Chain, days: int = 20):
    hours = days * 24
    baseLimitData = BaseLimit(protocol=protocol, hours=hours, chart=True, chain=chain)
    chart_data = await baseLimitData.all_rebalance_ranges()
    return chart_data


async def recent_fees(protocol: Protocol, chain: Chain, hours: int = 24):
    top_level = TopLevelData(protocol, chain)
    recent_fees = await top_level.recent_fees(hours)

    return {"periodHours": hours, "fees": recent_fees}


async def account():
    address = "0x8A0Dcd7cf2f6242Ff03ad126c980d60f7fFCbeC7"
    chain = Chain.POLYGON
    protocol = Protocol.UNISWAP
    account_info = AccountInfo(protocol, chain, address)
    popo = await account_info.output()


def get_timepassed_string(start_time: datetime) -> str:
    _timelapse = datetime.utcnow() - start_time
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


async def test_temporal():
    hypervisor_address = "0xadc7b4096c3059ec578585df36e6e1286d345367"
    result = await v3data.common.analytics.get_hype_data(
        chain=Chain.POLYGON, hypervisor_address=hypervisor_address, period=1
    )

    fees_yield = await fee_returns_all(
        protocol=Protocol.QUICKSWAP,
        chain=Chain.POLYGON,
        days=1,
        hypervisors=None,
        current_timestamp=None,
    )


async def test_hype_collectedFees(
    protocol: Protocol,
    chain: Chain,
    start_timestamp: int | None = None,
    end_timestamp: int | None = None,
    start_block: int | None = None,
    end_block: int | None = None,
):
    collected_fees = await v3data.common.hypervisor.collected_fees(
        protocol=protocol,
        chain=chain,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        start_block=start_block,
        end_block=end_block,
        usd_total_only=True,
    )

    return collected_fees


async def test_hype_collectedFees_multiMonth(
    protocol: Protocol,
    chain: Chain,
    year: int = 2023,
    start_month: int = 1,
    end_month: int = 4,
):
    for month in range(start_month, end_month + 1):
        start_date = datetime(year=year, month=month, day=1)
        end_date = (start_date + timedelta(days=33)).replace(
            day=1, hour=0, minute=0, second=0
        )
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())

        month_hype_collected_fees = await test_hype_collectedFees(
            protocol=protocol,
            chain=chain,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
        )

        debug = f"{month_hype_collected_fees}"


# TESTING
if __name__ == "__main__":
    # start time log
    _startime = datetime.utcnow()

    # base range chart all
    # data = asyncio.run(
    #    base_range_chart_all(protocol=Protocol.UNISWAP, chain=Chain.MAINNET, days=20)
    # )

    # recent fees
    data = asyncio.run(
        test_hype_collectedFees(
            protocol=Protocol.THENA,
            chain=Chain.BSC,
            start_timestamp=1680355404,
            end_timestamp=1682083431,
        )
    )

    # end time log
    print(" took {} to complete the script".format(get_timepassed_string(_startime)))
