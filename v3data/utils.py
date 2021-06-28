import datetime
import pytz


def timestamp_to_date(timestamp, format=None):
    """Converts UNIX timestamp to ISO date"""
    dt = datetime.datetime.utcfromtimestamp(timestamp)

    if not format:
        # Returns isoformat by default
        return dt.isoformat()
    else:
        return dt.strftime(format)


def timestamp_ago(time_delta):
    """Returns timestamp of time_delta ago from now in UTC"""
    return int((datetime.datetime.utcnow() - time_delta).replace(tzinfo=datetime.timezone.utc).timestamp())


def sqrtPriceX96_to_priceDecimal(sqrtPriceX96, token0_decimal, token1_decimal):
    return ((sqrtPriceX96 ** 2) / 2 ** (96 * 2)) * 10 ** (token0_decimal - token1_decimal)


def current_date_in_timezone(timezone):
    EST = pytz.timezone(timezone)
    return int(datetime.datetime.now(EST).replace(hour=0, minute=0, second=0).timestamp())


def tick_to_priceDecimal(tick, token0_decimal, token1_decimal):
    return 1.0001 ** tick * 10 ** (token0_decimal - token1_decimal)
