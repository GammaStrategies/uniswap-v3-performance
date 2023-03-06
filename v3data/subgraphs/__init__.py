import logging
from functools import wraps

from gql import Client as GqlClient
from gql.dsl import DSLFragment, DSLQuery, DSLSchema, dsl_gql
from gql.transport.aiohttp import AIOHTTPTransport, log as requests_logger

from v3data.enums import Chain, Protocol

requests_logger.setLevel(logging.WARNING)


class AsyncGqlClient(GqlClient):
    """Subclass of gql Client that defaults to AIOHTTPTransport"""
    def __init__(self, url: str, schema):
        self.url = url
        super().__init__(schema=schema, transport=AIOHTTPTransport(url=url))


class SubgraphClient:
    """Subgraph base client to manage query execution and shared fragments"""
    def __init__(
        self, protocol: Protocol, chain: Chain, url: str, schema_path: str
    ) -> None:
        with open(schema_path) as f:
            schema = f.read()
        self.client = AsyncGqlClient(url=url, schema=schema)
        self.data_schema = DSLSchema(self.client.schema)
        self._fragment_dependencies: list[DSLFragment] = []
        self._fragments_used: list[str] = []

    async def execute(self, query: DSLQuery) -> dict:
        gql = dsl_gql(*self._fragment_dependencies, query)
        async with self.client as session:
            result = await session.execute(gql)
            return result


def fragment(fragment_function):
    """
    Decorator for use with SubgraphClient methods keep track of fragment usage
    All fragment methods should be decorated with this
    """
    @wraps(fragment_function)
    def wrapper(*args):
        fragment = fragment_function(*args)
        instance = args[0]  # self
        if fragment.name not in instance._fragments_used:
            instance._fragments_used.append(fragment.name)
            instance._fragment_dependencies.append(fragment)
        return fragment

    return wrapper
