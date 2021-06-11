import requests

from v3data.config import VISOR_SUBGRAPH_URL, UNI_V3_SUBGRAPH_URL


class SubgraphClient:
    def __init__(self, url):
        self._url = url

    def query(self, query: str, variables=None) -> dict:
        """Make graphql query to subgraph"""
        if variables:
            params = {'query': query, 'variables': variables}
        else:
            params = {'query': query}
        response = requests.post(self._url, json=params)
        return response.json()


class VisorClient(SubgraphClient):
    def __init__(self):
        super().__init__(VISOR_SUBGRAPH_URL)


class UniswapV3Client(SubgraphClient):
    def __init__(self):
        super().__init__(UNI_V3_SUBGRAPH_URL)
