import pytest
import v3data.utils as utils


def test_year_month_to_timestamp_valid():
    assert utils.year_month_to_timestamp(2021, 6) == 1622505600

@pytest.mark.parametrize(
    "year, month", [
        (2021, 15),
        (-15, 2),
        (-1, 18)
    ]
)
def test_year_month_to_timestamp_invalid(year, month):
    with pytest.raises(ValueError):
        utils.year_month_to_timestamp(year, month)
