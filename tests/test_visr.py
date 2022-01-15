
import json
import pytest
from v3data.gamma import GammaCalculations


@pytest.fixture
def visr_data_30days():
    with open("tests/data/visr_30days.json", "r") as f:
        data = json.load(f)
    return data

@pytest.fixture
def visr_data_6days():
    with open("tests/data/visr_6days.json", "r") as f:
        data = json.load(f)
    return data
    

def test_visr_calculations_basic_info_valid(visr_data_30days):
    calculations = GammaCalculations(days=30)
    calculations.data = visr_data_30days

    expected = {
        "totalDistributed": 448331.81597959,
        "totalDistributedUSD": 526995.4773599501,
        "totalStaked": 14450624.77771855,
        "totalSupply": 100000000.0
    }

    assert calculations.basic_info(get_data=False) == expected


def test_visr_calculations_visr_yield_valid(visr_data_30days):
    calculations = GammaCalculations(days=30)
    calculations.data = visr_data_30days

    expected = {
        "daily": {
            "yield": 0.00018433554014052334,
            "apr": 0.06728247215129102,
            "apy": 0.06959093499898117,
            "estimatedAnnualDistribution": 968155.5593894515,
            "estimatedAnnualDistributionUSD": 970171.4736479964
        },
        "weekly": {
            "yield": 0.0015005248827342221,
            "apr": 0.07824165459971301,
            "apy": 0.08137488138586457,
            "estimatedAnnualDistribution": 1131785.7941984935,
            "estimatedAnnualDistributionUSD": 1199654.9828339964
        },
        "monthly": {
            "yield": 0.008686742066208453,
            "apr": 0.1056886951388695,
            "apy": 0.11145881097696386,
            "estimatedAnnualDistribution": 1464760.1133901686,
            "estimatedAnnualDistributionUSD": 1319796.769148453
        }
    }

    assert calculations.visr_yield(get_data=False) == expected


def test_visr_calculations_distributions_valid(visr_data_6days):
    calculations = GammaCalculations(days=6)
    calculations.data = visr_data_6days

    expected = [
        {
            "timestamp": "1627794000",
            "date": "August 01, 2021",
            "distributed": 2652.4809846286344
        },
        {
            "timestamp": "1627707600",
            "date": "July 31, 2021",
            "distributed": 4142.0
        },
        {
            "timestamp": "1627621200",
            "date": "July 30, 2021",
            "distributed": 2924.0
        },
        {
            "timestamp": "1627534800",
            "date": "July 29, 2021",
            "distributed": 3535.0000000000005
        },
        {
            "timestamp": "1627448400",
            "date": "July 28, 2021",
            "distributed": 3734.0
        },
        {
            "timestamp": "1627362000",
            "date": "July 27, 2021",
            "distributed": 2996.0
        }
    ]

    assert calculations.distributions(get_data=False) == expected