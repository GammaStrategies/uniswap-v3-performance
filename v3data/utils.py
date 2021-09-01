import datetime


def timestamp_to_date(timestamp, format=None):
    """Converts UNIX timestamp to ISO date"""
    dt = datetime.datetime.utcfromtimestamp(timestamp)

    if not format:
        # Returns isoformat by default
        return dt.isoformat()
    else:
        return dt.strftime(format)


def date_to_timestamp(date):
    return int(date.replace(tzinfo=datetime.timezone.utc).timestamp())


def timestamp_ago(time_delta):
    """Returns timestamp of time_delta ago from now in UTC"""
    return int((datetime.datetime.utcnow() - time_delta).replace(tzinfo=datetime.timezone.utc).timestamp())


def year_month_day_to_timestamp(year, month, day):
    if year < 0 or month < 0 or month > 12:
        raise ValueError("Invalid month")
    return int(datetime.datetime(year, month, day, tzinfo=datetime.timezone.utc).timestamp())


def sqrtPriceX96_to_priceDecimal(sqrtPriceX96, token0_decimal, token1_decimal):
    return ((sqrtPriceX96 ** 2) / 2 ** (96 * 2)) * 10 ** (token0_decimal - token1_decimal)


def tick_to_priceDecimal(tick, token0_decimal, token1_decimal):
    return 1.0001 ** tick * 10 ** (token0_decimal - token1_decimal)
