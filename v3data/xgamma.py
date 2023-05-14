"""Data related to XGAMMA Staking"""

from dataclasses import InitVar, dataclass, field

from gql.dsl import DSLQuery

from v3data.constants import XGAMMA_ADDRESS
from v3data.enums import Chain, Protocol
from v3data.schema import ValueWithDecimal
from v3data.subgraphs import SubgraphData
from v3data.subgraphs.gamma import GammaClient


@dataclass
class XGammaInfo:
    """Data class to store query data"""

    gamma_staked: ValueWithDecimal = field(init=False)
    xgamma_supply: ValueWithDecimal = field(init=False)
    gamma_per_xgamma: float = field(init=False)
    gamma_staked_raw: InitVar[int]
    xgamma_supply_raw: InitVar[int]

    def __post_init__(self, gamma_staked_raw: int, xgamma_supply_raw: int):
        self.gamma_staked = ValueWithDecimal(gamma_staked_raw, decimals=18)
        self.xgamma_supply = ValueWithDecimal(xgamma_supply_raw, decimals=18)
        self.gamma_per_xgamma = (
            self.gamma_staked.raw / self.xgamma_supply.raw
        )


class XGammaData(SubgraphData):
    """Class to get xGamma staking relateed data"""

    def __init__(self):
        super().__init__()
        self.data: XGammaInfo
        self.client = GammaClient(Protocol.UNISWAP, Chain.MAINNET)

    async def _query_data(self) -> dict:
        ds = self.client.data_schema

        query = DSLQuery(
            ds.Query.rewardHypervisor(id=XGAMMA_ADDRESS).select(
                ds.RewardHypervisor.totalGamma,
                ds.RewardHypervisor.totalSupply,
            ),
        )

        response = await self.client.execute(query)
        self.query_response = response

    def _transform_data(self) -> XGammaInfo:
        return XGammaInfo(
            gamma_staked_raw=self.query_response["rewardHypervisor"]["totalGamma"],
            xgamma_supply_raw=self.query_response["rewardHypervisor"]["totalSupply"],
        )
