import pytest
from v3data.visor import VisorVault


@pytest.fixture
def visor():
    visor_data = VisorVault("0x283ca7b5f1f27154a130e5b2d991726cafad76df")
    visor_data.data = {
        "hypervisorShares": [
            {
                "hypervisor": {
                    "id": "0x33682bfc1d94480a0e3de0a565180b182b71d485",
                    "pool": {
                        "token0": { "decimals": 18 },
                        "token1": { "decimals": 18 }
                    },
                    "totalSupply": "83363442388453224282",
                    "tvl0": "3642482372580536749329",
                    "tvl1": "68028480034187187941",
                    "tvlUSD": "221037.6586470762133346823579644606"
                },
                "shares": "110736588201756890"
            },
            {
                "hypervisor": {
                    "id": "0x716bd8a7f8a44b010969a1825ae5658e7a18630d",
                    "pool": {
                        "token0": { "decimals": 6 },
                        "token1": { "decimals": 18 }
                    },
                    "totalSupply": "463119870128461327530",
                    "tvl0": "1015040859637",
                    "tvl1": "158123004391085370660",
                    "tvlUSD": "1403964.591712667777493882525084481"
                },
                "shares": "664158777314592180"
            }
        ],
        "owner": {
            "id": "0xccff041faeb4afda1cf84b0c082d907387291453"
        },
        "visrStaked": "4469747988595138246832"
    }
    return visor_data

def test_info_valid(visor):
    expected = {
        "0x33682bfc1d94480a0e3de0a565180b182b71d485": {
            "balance0": 4.838524645432333,
            "balance1": 0.09036625124517011,
            "balanceUSD": 293.6173876868612,
            "shareOfSupply": 0.001328359110768861,
            "shares": 110736588201756890
        },
        "0x716bd8a7f8a44b010969a1825ae5658e7a18630d": {
            "balance0": 1455.6669660359544,
            "balance1": 0.2267637128861752,
            "balanceUSD": 2013.4212906179544,
            "shareOfSupply": 0.0014340969156222258,
            "shares": 664158777314592180
        },
        "owner": "0xccff041faeb4afda1cf84b0c082d907387291453",
        "visrStaked": 4469.747988595138
    }
    assert visor.info(get_data=False) == expected
