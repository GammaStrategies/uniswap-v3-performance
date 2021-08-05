import pytest
from v3data.users import VisorUser


@pytest.fixture
def user():
    user_data = VisorUser("0x33682bfc1d94480a0e3de0a565180b182b71d485")
    user_data.data = {
        "visorsOwned": [
            {
                "hypervisorShares": [
                    {
                        "hypervisor": {
                            "id": "0x33682bfc1d94480a0e3de0a565180b182b71d485",
                            "pool": {
                                "token0": { "decimals": 18 },
                                "token1": { "decimals": 18 }
                            },
                            "totalSupply": "83363442388453224282",
                            "tvl0": "3628232815096625131352",
                            "tvl1": "68113925747644545946",
                            "tvlUSD": "219955.8273500016637486216234189742"
                        },
                        "shares": "3773291065513214437"
                    },
                    {
                        "hypervisor": {
                            "id": "0x9a98bffabc0abf291d6811c034e239e916bbcec0",
                            "pool": {
                                "token0": { "decimals": 18 },
                                "token1": { "decimals": 6 }
                            },
                            "totalSupply": "1318530588409",
                            "tvl0": "70709788626136145516",
                            "tvl1": "1040387884408",
                            "tvlUSD": "1215077.807724075415589436443443255"
                        },
                        "shares": "22927529964"
                    }
                ],
                "id": "0xdb8be2c6dffa48cea696966743fb137d97aa55f6",
                "visrStaked": "12313895778848414458187"
            }
        ]
    }
    return user_data

def test_info_valid(user):
    expected = {
        '0xdb8be2c6dffa48cea696966743fb137d97aa55f6': {
            'visrStaked': 12313.895778848415,
            '0x33682bfc1d94480a0e3de0a565180b182b71d485': {
                'shares': 3773291065513214437,
                'shareOfSupply': 0.04526313882205826,
                'balance0': 164.2252055884658,
                'balance1': 3.083050076831004,
                'balanceUSD': 9955.891148063805
            },
            '0x9a98bffabc0abf291d6811c034e239e916bbcec0': {
                'shares': 22927529964,
                'shareOfSupply': 0.01738869781676087,
                'balance0': 1.229551147106916,
                'balance1': 18090.99053418985,
                'balanceUSD': 21128.620822366214
            }
        }
    }
    assert user.info(get_data=False) == expected
