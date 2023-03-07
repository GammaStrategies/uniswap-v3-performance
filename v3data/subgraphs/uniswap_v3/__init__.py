from v3data.enums import Chain, Protocol
from v3data.config import DEX_SUBGRAPH_URLS
from v3data.subgraphs import SubgraphClient


class UniswapClient(SubgraphClient):
    def __init__(self, protocol: Protocol, chain: Chain):
        super().__init__(
            protocol=protocol,
            chain=chain,
            url=DEX_SUBGRAPH_URLS[protocol][chain],
            schema_path="v3data/subgraphs/uniswap_v3/schema.graphql",
        )
