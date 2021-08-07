import os

V3_FACTORY_ADDRESS = "0x1F98431c8aD98523631AE4a59f267346ea31F984"

uniswap_subgraphs = {
    'prod': "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
    'alt': "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-alt",
    'test': "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-testing"
}

visor_subgraphs = {
    'prod': "https://api.thegraph.com/subgraphs/name/visorfinance/visor",
    'test': "https://api.thegraph.com/subgraphs/name/l0c4t0r/visor",
}

THEGRAPH_INDEX_NODE_URL = "https://api.thegraph.com/index-node/graphql"
ETH_BLOCKS_SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/blocklytics/ethereum-blocks"
UNI_V2_SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/ianlapham/uniswapv2"
UNI_V3_SUBGRAPH_URL = uniswap_subgraphs[os.environ.get('UNISWAP_SUBGRAPH', 'prod')]
VISOR_SUBGRAPH_URL = visor_subgraphs[os.environ.get('VISOR_SUBGRAPH', 'prod')]


TOKEN_LIST_URL = "https://tokens.coingecko.com/uniswap/all.json"

DEFAULT_BBAND_INTERVALS = 20
DEFAULT_TIMEZONE = os.environ.get('TIMEZONE', 'UTC-5')

CHARTS_CACHE_TIMEOUT = os.environ.get('CHARTS_CACHE_TIMEOUT', 600)

PRIVATE_BETA_TVL = 400000
