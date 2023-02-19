import datetime
import logging

from v3data.constants import BLOCK_TIME_SECONDS
from v3data.config import CHAIN_NAME_CONVERSION

logger = logging.getLogger(__name__)


# historic used var
STATIC_DATETIME_UTCNOW = None


def __datetime_utcnow() -> datetime.datetime:
    if STATIC_DATETIME_UTCNOW:
        # return defined datetime
        return STATIC_DATETIME_UTCNOW

    # return current datetime
    return datetime.datetime.utcnow()


def timestamp_to_date(timestamp, format=None):
    """Converts UNIX timestamp to ISO date"""
    dt = datetime.datetime.utcfromtimestamp(timestamp)

    if not format:
        # Returns isoformat by default
        return dt.isoformat()
    else:
        return dt.strftime(format)


def parse_date(date_string, date_format="%Y-%m-%d"):
    if not date_string:
        return None

    try:
        date = datetime.datetime.strptime(date_string, date_format)
    except ValueError:
        return None

    return date


def date_to_timestamp(date):
    date_as_dt = datetime.datetime(year=date.year, month=date.month, day=date.day)
    return int(date_as_dt.replace(tzinfo=datetime.timezone.utc).timestamp())


def timestamp_ago(time_delta):
    """Returns timestamp of time_delta ago from now in UTC"""
    return int(
        (__datetime_utcnow() - time_delta)
        .replace(tzinfo=datetime.timezone.utc)
        .timestamp()
    )


def year_month_day_to_timestamp(year, month, day):
    if year < 0 or month < 0 or month > 12:
        raise ValueError("Invalid month")
    return int(
        datetime.datetime(year, month, day, tzinfo=datetime.timezone.utc).timestamp()
    )


def sqrtPriceX96_to_priceDecimal(sqrtPriceX96, token0_decimal, token1_decimal):
    return ((sqrtPriceX96**2) / 2 ** (96 * 2)) * 10 ** (
        token0_decimal - token1_decimal
    )


def tick_to_priceDecimal(tick, token0_decimal, token1_decimal):
    return 1.0001**tick * 10 ** (token0_decimal - token1_decimal)


def sub_in_256(x, y):
    difference = x - y
    if difference < 0:
        difference += 2**256

    return difference


def estimate_block_from_timestamp_diff(
    chain, current_block, current_timestamp, initial_timestamp
):
    ts_diff = current_timestamp - initial_timestamp
    block_diff = ts_diff // BLOCK_TIME_SECONDS[chain]

    initial_block = current_block - block_diff
    return initial_block


def filter_addresses_byChain(addresses: list[str], chain: str) -> list[str]:
    """Return only addresses belonging to the specified chain.
        addresses list must follow EIP-3770 (https://eips.ethereum.org/EIPS/eip-3770)
        and will be converted to local format using config CHAIN_NAME_CONVERSION var

    Args:
        addresses (list): EIP-3770 formatted addresses list
        chain (str):

    Returns:
        list: of addresses
    """
    result = list()
    for item in addresses:
        try:
            k, address = parse_address_eip(item)
            if CHAIN_NAME_CONVERSION[k.lower()] == chain.lower():
                result.append(address)
        except ValueError as err:
            logger.warning(err)
        except:
            logger.exception(f" Unexpected error parsing address item: {item}")

    return result


def parse_address_eip(address: str) -> tuple[str, str]:
    """convert EIP 3770 address format to chain,address values

    Args:
        address (str): in EIP 3770 address format

    Raises:
        ValueError:

    Returns:
        tuple[str,str]: <chain>, <address>
    """
    base = address.split(":")
    if len(base) == 2:
        return base[0], base[1]
    else:
        raise ValueError(f" Address does not follow standard  {address}")
