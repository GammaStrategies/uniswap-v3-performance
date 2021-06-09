import datetime


def timestamp_to_date(timestamp):
    """Converts UNIX timestamp to ISO date"""
    return datetime.datetime.utcfromtimestamp(timestamp).isoformat()

def timestamp_ago(time_delta):
    """Returns timestamp of time_delta ago from now in UTC"""
    return int((datetime.datetime.utcnow() - time_delta).replace(tzinfo=datetime.timezone.utc).timestamp())

def sqrtPriceX96_to_priceDecimal(sqrtPriceX96, token0_decimal, token1_decimal):
    return ((sqrtPriceX96 ** 2) / 2 ** (96 * 2)) * 10 ** (token0_decimal - token1_decimal)
