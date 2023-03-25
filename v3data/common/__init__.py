import logging
from abc import ABC, abstractmethod

from fastapi import Response

from v3data.enums import Chain, Protocol, QueryType

from .subgraph_status import SubgraphStatusOutput, subgraph_status

logger = logging.getLogger(__name__)


class ExecutionOrderWrapper(ABC):
    def __init__(self, protocol: Protocol, chain: Chain, response: Response) -> None:
        self.protocol = protocol
        self.chain = chain
        self.response = response
        self.database_datetime: str = ""

    async def run(self, first: QueryType = QueryType.SUBGRAPH):
        first_func = self._subgraph
        first_headers = self._set_subgraph_headers

        second_func = self._database
        second_headers = self._set_database_headers

        if first == QueryType.DATABASE:
            first_func, second_func = second_func, first_func
            first_headers, second_headers = second_headers, first_headers
        try:
            results = await first_func()
            first_headers()
        except Exception:
            logger.exception(f"{first} run failed for {self.__class__.__name__}")
            results = await second_func()
            second_headers()

        return results

    @abstractmethod
    async def _database(self):
        pass

    def _set_database_headers(self) -> None:
        if not self.response:
            return
        self.response.headers["X-Database"] = "true"
        self.response.headers["X-Database-itemUpdated"] = f"{self.database_datetime}"

    @abstractmethod
    async def _subgraph(self):
        pass

    def _set_subgraph_headers(self) -> None:
        if not self.response:
            return
        self.response.headers["X-Database"] = "false"
