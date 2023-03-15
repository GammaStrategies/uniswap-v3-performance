from datetime import datetime, timedelta
from fastapi import Response, status

from v3data.enums import Chain, Protocol
from database.collection_endpoint import db_returns_manager, db_allRewards2_manager
from v3data.config import MONGO_DB_URL


class HypervisorAnalytics:
    def __init__(self, chain: Chain, hypervisor_address: str):
        self.chain = chain
        self.address = hypervisor_address

        self.returns_manager = db_returns_manager(mongo_url=MONGO_DB_URL)
        self.allrewards2_manager = db_allRewards2_manager(mongo_url=MONGO_DB_URL)

    async def get_data(
        self,
        period: int = 30,
    ):

        end_date = datetime.now()
        ini_date = end_date - timedelta(days=period)

        return await self.returns_manager._get_data(
            query=self.returns_manager.query_return_imperm_rewards2_flat(
                chain=self.chain,
                hypervisor_address=self.address,
                period=period,
                ini_date=ini_date,
                end_date=end_date,
            )
        )

        # allrewards2_data = await self.allrewards2_manager.get_hypervisor_rewards(
        #     chain=self.chain, address=self.address, ini_date=ini_date, end_date=end_date
        # )

        # # merge first found allrewards2 to returns and il data
        # returns_il_data["allRewards2"] = (
        #     allrewards2_data[0]["rewards2"] if allrewards2_data else {}
        # )

        # # return data
        # return returns_il_data


async def get_hype_data(
    chain: Chain, hypervisor_address: str, period: int, response: Response = None
):

    if response:
        # this is a database query only
        response.headers["X-Database"] = "true"
    atest = HypervisorAnalytics(chain=chain, hypervisor_address=hypervisor_address)
    return await atest.get_data(period=period)
