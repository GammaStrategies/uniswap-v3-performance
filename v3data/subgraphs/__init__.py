import logging
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any

from gql import Client as GqlClient
from gql.dsl import DSLFragment, DSLQuery, DSLSchema, dsl_gql
from gql.transport.aiohttp import AIOHTTPTransport, log as requests_logger

from v3data.config import GQL_CLIENT_TIMEOUT

requests_logger.setLevel(logging.WARNING)


def fragment(fragment_function):
    """
    Decorator for use with SubgraphClient methods keep track of fragment usage
    All fragment methods should be decorated with this
    """

    @wraps(fragment_function)
    def wrapper(*args):
        frag = fragment_function(*args)
        instance = args[0]  # self
        if frag.name not in instance._fragments_used:
            instance._fragments_used.append(frag.name)
            instance._fragment_dependencies.append(frag)
        return frag

    return wrapper


class AsyncGqlClient(GqlClient):
    """Subclass of gql Client that defaults to AIOHTTPTransport"""

    def __init__(self, url: str, schema, execute_timeout: int) -> None:
        self.url = url
        super().__init__(
            schema=schema,
            transport=AIOHTTPTransport(url=url),
            execute_timeout=execute_timeout,
        )


class SubgraphClient:
    """Subgraph base client to manage query execution and shared fragments"""

    def __init__(self, url: str, schema_path: str) -> None:
        with open(schema_path, encoding="utf-8") as schema_file:
            schema = schema_file.read()
        self.client = AsyncGqlClient(
            url=url, schema=schema, execute_timeout=GQL_CLIENT_TIMEOUT
        )
        self.data_schema = DSLSchema(self.client.schema)
        self._fragment_dependencies: list[DSLFragment] = []
        self._fragments_used: list[str] = []

    async def execute(self, query: DSLQuery) -> dict:
        """Executes query and returns result"""
        gql = dsl_gql(*self._fragment_dependencies, query)
        async with self.client as session:
            result = await session.execute(gql)
            return result

    @fragment
    def meta_fields_fragment(self) -> DSLFragment:
        """Meta fragment is common across all subgraphs"""
        ds = self.data_schema
        frag = DSLFragment("MetaFields")
        frag.on(ds._Meta_)
        frag.select(ds._Meta_.block.select(ds._Block_.number, ds._Block_.timestamp))
        return frag


class SubgraphData(ABC):
    """Abstract base class for subgraph data."""
    def __init__(self):
        self.data: Any
        self.query_response: dict

    def load_query_response(self, query_response: dict) -> None:
        """Load data from external source to skip querying.

        Args:
            query_response: dict with data from subgraph query
        """
        self.query_response = query_response

    async def get_data(self, run_query: bool = True) -> None:
        """Get data, transforms it and stores it in self.data.

        Args:
            run_query: Defaults to True, set to False if data is already loaded
        """
        if run_query:
            await self._query_data()

        self.data = self._transform_data()

    @abstractmethod
    async def _query_data(self) -> dict:
        """Query subgraph and sets self.query_response."""
        # query = ""
        # response = await self.client.execute(query)
        # self.query_response = response

    @abstractmethod
    def _transform_data(self) -> Any:
        """Transformations for self.query_response into self.data"""
        self.data = self.query_response
