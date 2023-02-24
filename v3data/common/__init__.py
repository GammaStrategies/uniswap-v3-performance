from abc import ABC, abstractmethod
from enum import Enum
from fastapi import Response
from v3data import IndexNodeClient


async def subgraph_status(protocol: str, chain: str):
    client = IndexNodeClient(protocol, chain)
    return await client.status()


class QueryType(Enum):
    DATABASE = "DATABASE"
    SUBGRAPH = "SUBGRAPH"


class ExecutionOrderWrapper(ABC):
    def __init__(self, protocol: str, chain: str, response: Response) -> None:
        self.protocol = protocol
        self.chain = chain
        self.response = response

    async def run(self, first: QueryType = QueryType.DATABASE):
        first_func = self._database
        second_func = self._subgraph
        if first == QueryType.SUBGRAPH:
            first_func, second_func = second_func, first_func
        try:
            results = await first_func()
        except Exception:
            results = await second_func()

        return results

    @abstractmethod
    async def _database(self):
        pass

    @abstractmethod
    async def _subgraph(self):
        pass
