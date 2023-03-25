from v3data import GammaClient
from v3data.config import DEFAULT_TIMEZONE
from v3data.enums import Chain, Protocol
from v3data.utils import timestamp_to_date


class EthData:
    def __init__(
        self, protocol: Protocol, chain: Chain, days, timezone=DEFAULT_TIMEZONE
    ):
        self.gamma_client = GammaClient(protocol, chain)
        self.days = days
        self.timezone = timezone
        self.decimal_factor = 10**18
        self.data = {}

    async def _get_data(self):
        query = """
        query($token: String!, $days: Int!, $timezone: String!){
            protocolDistribution(
                id: $token
            ){
                distributed
                distributedUSD
            }
            distributionDayDatas(
                orderBy: date
                orderDirection: desc
                first: $days
                where: {
                    token: $token
                    distributed_gt: 0
                    timezone: $timezone
                }
            ){
                date
                distributed
                distributedUSD
            }
        }
        """
        variables = {"token": "ETH", "days": self.days, "timezone": self.timezone}
        response = await self.gamma_client.query(query, variables)
        self.data = response["data"]


class EthCalculations(EthData):
    def __init__(self, chain: Chain, days=30):
        super().__init__(chain, days=days)

    async def basic_info(self, get_data=True):
        if get_data:
            await self._get_data()

        data = self.data["ethToken"]

        return {
            "totalDistributed": int(data["totalDistributed"]) / self.decimal_factor,
            "totalDistributedUSD": float(data["totalDistributedUSD"]),
        }

    async def distributions(self, get_data=True):
        if get_data:
            await self._get_data()

        results = [
            {
                "timestamp": day["date"],
                "date": timestamp_to_date(int(day["date"]), "%m/%d/%Y"),
                "distributed": float(day["distributed"]) / self.decimal_factor,
            }
            for day in self.data["distributionDayDatas"]
        ]

        return results


class EthDistribution(EthCalculations):
    def __init__(self, chain: Chain, days=6, timezone=DEFAULT_TIMEZONE):
        super().__init__(chain, days=days)

    async def output(self):
        distributions = await self.distributions(get_data=True)

        fee_distributions = []
        for i, distribution in enumerate(distributions):
            fee_distributions.append(
                {
                    "title": distribution["date"],
                    "desc": f"{float(distribution['distributed']):.2f} ETH Distributed",
                    "id": i + 2,
                }
            )

        return {"feeDistribution": fee_distributions}
