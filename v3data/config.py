import os

V3_FACTORY_ADDRESS = "0x1F98431c8aD98523631AE4a59f267346ea31F984"

uniswap_subgraphs = {
    "mainnet": {
        "prod": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
        "alt": "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-alt",
        "test": "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-testing",
    },
    "polygon": {
        "prod": "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-polygon"
    },
    "arbitrum": {
        "prod": "https://api.thegraph.com/subgraphs/name/ianlapham/arbitrum-dev"
    },
    "optimism": {
        "prod": "https://api.thegraph.com/subgraphs/name/ianlapham/optimism-post-regenesis"
    },
    "celo": {
        "prod": "https://api.thegraph.com/subgraphs/name/jesse-sawa/uniswap-celo"
    }
}

visor_subgraphs = {
    "prod": "https://api.thegraph.com/subgraphs/name/visorfinance/visor",
    "test": "https://api.thegraph.com/subgraphs/name/l0c4t0r/visor",
    "lab": "https://api.thegraph.com/subgraphs/name/l0c4t0r/laboratory",
}

gamma_subgraphs = {
    "mainnet": {
        "prod": "https://api.thegraph.com/subgraphs/name/gammastrategies/gamma",
        "test": "https://api.thegraph.com/subgraphs/name/l0c4t0r/gamma",
        "lab": "https://api.thegraph.com/subgraphs/name/l0c4t0r/laboratory",
    },
    "polygon": {
        "prod": "https://api.thegraph.com/subgraphs/name/gammastrategies/polygon",
        "test": "https://api.thegraph.com/subgraphs/name/l0c4t0r/gamma-polygon",
    },
    "arbitrum": {
        "prod": "https://api.thegraph.com/subgraphs/name/gammastrategies/arbitrum",
        "test": "https://api.thegraph.com/subgraphs/name/l0c4t0r/gamma-arbitrum",
    },
    "optimism": {
        "prod": "https://api.thegraph.com/subgraphs/name/gammastrategies/optimism",
        "test": "https://api.thegraph.com/subgraphs/name/l0c4t0r/gamma-optimism",
    },
    "celo": {
        "prod": "https://api.thegraph.com/subgraphs/name/gammastrategies/celo",
        "test": "https://api.thegraph.com/subgraphs/name/l0c4t0r/gamma-celo",
    },
}

THEGRAPH_INDEX_NODE_URL = "https://api.thegraph.com/index-node/graphql"
ETH_BLOCKS_SUBGRAPH_URL = (
    "https://api.thegraph.com/subgraphs/name/blocklytics/ethereum-blocks"
)
UNI_V2_SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/ianlapham/uniswapv2"


UNI_V3_SUBGRAPH_URLS = {
    "mainnet": uniswap_subgraphs["mainnet"][
        os.environ.get("UNISWAP_SUBGRAPH_MAINNET", "prod")
    ],
    "polygon": uniswap_subgraphs["polygon"][
        os.environ.get("UNISWAP_SUBGRAPH_POLYGON", "prod")
    ],
    "arbitrum": uniswap_subgraphs["arbitrum"][
        os.environ.get("UNISWAP_SUBGRAPH_ARBITRUM", "prod")
    ],
    "optimism": uniswap_subgraphs["optimism"][
        os.environ.get("UNISWAP_SUBGRAPH_OPTIMISM", "prod")
    ],
    "celo": uniswap_subgraphs["celo"][
        os.environ.get("UNISWAP_SUBGRAPH_CELO", "prod")
    ],
}

VISOR_SUBGRAPH_URL = visor_subgraphs[os.environ.get("VISOR_SUBGRAPH", "prod")]

GAMMA_SUBGRAPH_URLS = {
    "mainnet": gamma_subgraphs["mainnet"][
        os.environ.get("GAMMA_SUBGRAPH_MAINNET", "prod")
    ],
    "polygon": gamma_subgraphs["polygon"][
        os.environ.get("GAMMA_SUBGRAPH_POLYGON", "prod")
    ],
    "arbitrum": gamma_subgraphs["arbitrum"][
        os.environ.get("GAMMA_SUBGRAPH_ARBITRUM", "prod")
    ],
    "optimism": gamma_subgraphs["optimism"][
        os.environ.get("GAMMA_SUBGRAPH_OPTIMISM", "prod")
    ],
    "celo": gamma_subgraphs["celo"][
        os.environ.get("GAMMA_SUBGRAPH_CELO", "prod")
    ],
}


XGAMMA_SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/l0c4t0r/xgamma"


TOKEN_LIST_URL = "https://tokens.coingecko.com/uniswap/all.json"

DEFAULT_BBAND_INTERVALS = 20
DEFAULT_TIMEZONE = os.environ.get("TIMEZONE", "UTC-5")

CHARTS_CACHE_TIMEOUT = os.environ.get("CHARTS_CACHE_TIMEOUT", 600)
APY_CACHE_TIMEOUT = os.environ.get("APY_CACHE_TIMEOUT", 600)
DASHBOARD_CACHE_TIMEOUT = os.environ.get("DASHBOARD_CACHE_TIMEOUT", 600)

EXCLUDED_HYPERVISORS = list(
    filter(None, os.environ.get("EXCLUDED_HYPES", "").split(","))
)
FALLBACK_DAYS = os.environ.get("FALLBACK_DAYS", 90)

legacy_stats = {
    "visr_distributed": 987998.1542393989,
    "visr_distributed_usd": 1246656.7073805775,
    "estimated_visr_annual_distribution": 1237782.0442017058,
    "estimated_visr_annual_distribution_usd": 1197097.0895269862,
}

ALCHEMY_URLS = {
    "polygon": f"https://polygon-mainnet.g.alchemy.com/v2/{os.environ.get('ALCHEMY_POLYGON_KEY', '')}",
    "optimism": f"https://opt-mainnet.g.alchemy.com/v2/{os.environ.get('ALCHEMY_OPTIMISM_KEY', '')}"
}
