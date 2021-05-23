from datetime import datetime


def timestamp_to_date(timestamp):
    """Converts UNIX timestamp to ISO date"""
    return datetime.utcfromtimestamp(timestamp).isoformat()


def sqrtPriceX96_to_priceDecimal(sqrtPriceX96, token0_decimal, token1_decimal):
    return ((sqrtPriceX96 ** 2) / 2 ** (96 * 2)) * 10 ** (token0_decimal - token1_decimal)
