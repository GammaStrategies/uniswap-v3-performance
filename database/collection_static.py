import logging
import asyncio
from dataclasses import dataclass, field, asdict, InitVar
from v3data.config import MONGO_DB_URL
from v3data.hypervisor import HypervisorData
from database.common.db_data_models import (
    tool_mongodb_general,
    tool_database_id,
    pool,
    token,
)
from database.collections_common import db_collections_common


@dataclass
class hypervisor_static(tool_mongodb_general, tool_database_id):
    chain: str
    address: str
    symbol: str
    protocol: int
    created: int
    pool: pool

    def create_id(self) -> str:
        return f"{self.chain}_{self.address}"


class db_static_manager(db_collections_common):
    db_collection_name = "static"

    async def create_data(
        self, chain: str, protocol: str
    ) -> dict[str:hypervisor_static]:
        """Create a dictionary of hypervisor_static database models

        Args:
            chain (str): _description_
            protocol (str): _description_

        Returns:
            dict: <hypervisor_id>:<db_data_models.hypervisor_static>
        """
        # define result var
        result = dict()
        hypervisors_data = HypervisorData(protocol=protocol, chain=chain)
        # get all hypervisors & their pools data
        await hypervisors_data._get_all_data()
        for hypervisor in hypervisors_data.basics_data:
            # temporal vars
            address = hypervisor["id"]
            hypervisor_name = f'{hypervisor["pool"]["token0"]["symbol"]}-{hypervisor["pool"]["token1"]["symbol"]}-{hypervisor["pool"]["fee"]}'

            _tokens = [
                token(
                    address=hypervisor["pool"]["token0"]["id"],
                    symbol=hypervisor["pool"]["token0"]["symbol"],
                    chain=chain,
                    position=0,
                ),
                token(
                    address=hypervisor["pool"]["token1"]["id"],
                    symbol=hypervisor["pool"]["token1"]["symbol"],
                    chain=chain,
                    position=1,
                ),
            ]
            _pool = pool(
                address=hypervisor["pool"]["id"],
                chain=chain,
                fee=hypervisor["pool"]["fee"],
                tokens=_tokens,
            )

            # add to result
            result[address] = hypervisor_static(
                chain=chain,
                address=address,
                symbol=hypervisor_name,
                protocol=protocol,
                created=hypervisor["created"],
                pool=_pool,
            )

        return result

    async def feed_db(self, chain: str, protocol: str):

        await self.save_items_to_database(
            data=await self.create_data(chain=chain, protocol=protocol),
            collection_name=self.db_collection_name,
        )

    async def get_data(self, chain: str, protocol: str) -> dict[str:hypervisor_static]:
        pass
