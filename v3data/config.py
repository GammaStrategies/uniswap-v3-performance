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
    "celo": {"prod": "https://api.thegraph.com/subgraphs/name/jesse-sawa/uniswap-celo"},
}

uniswap_feegrowth_subgraphs = {
    "mainnet": {
        "prod": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
        "alt": "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-alt",
        "test": "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-testing",
    },
    "polygon": {
        "prod": "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-polygon"
    },
    "arbitrum": {
        "prod": "https://api.thegraph.com/subgraphs/name/l0c4t0r/hype-pool-uniswap-v3-arbitrum"
    },
    "optimism": {
        "prod": "https://api.thegraph.com/subgraphs/name/ianlapham/optimism-post-regenesis"
    },
    "celo": {"prod": "https://api.thegraph.com/subgraphs/name/jesse-sawa/uniswap-celo"},
}

quickswap_subgraphs = {
    "polygon": {"prod": "https://api.thegraph.com/subgraphs/name/sameepsi/quickswap-v3"}
}

quickswap_feegrowth_subgraphs = {
    "polygon": {"prod": "https://api.thegraph.com/subgraphs/name/sameepsi/quickswap-v3"}
}

visor_subgraphs = {
    "prod": "https://api.thegraph.com/subgraphs/name/visorfinance/visor",
    "test": "https://api.thegraph.com/subgraphs/name/l0c4t0r/visor",
    "lab": "https://api.thegraph.com/subgraphs/name/l0c4t0r/laboratory",
}

gamma_subgraphs = {
    "uniswap_v3": {
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
            "test": "https://api.thegraph.com/subgraphs/name/l0c4t0r/visor-arbitrum",
        },
        "optimism": {
            "prod": "https://api.thegraph.com/subgraphs/name/gammastrategies/optimism",
            "test": "https://api.thegraph.com/subgraphs/name/l0c4t0r/gamma-optimism",
        },
        "celo": {
            "prod": "https://api.thegraph.com/subgraphs/name/gammastrategies/celo",
            "test": "https://api.thegraph.com/subgraphs/name/l0c4t0r/gamma-celo",
        },
    },
    "quickswap": {
        "polygon": {
            "prod": "https://api.thegraph.com/subgraphs/name/gammastrategies/algebra-polygon",
            "test": "https://api.thegraph.com/subgraphs/name/l0c4t0r/gamma-algebra-polygon",
        },
    },
}

THEGRAPH_INDEX_NODE_URL = "https://api.thegraph.com/index-node/graphql"
ETH_BLOCKS_SUBGRAPH_URL = (
    "https://api.thegraph.com/subgraphs/name/blocklytics/ethereum-blocks"
)
UNI_V2_SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/ianlapham/uniswapv2"

DEX_SUBGRAPH_URLS = {
    "uniswap_v3": {
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
    },
    "quickswap": {
        "polygon": quickswap_subgraphs["polygon"][
            os.environ.get("QUICKSWAP_SUBGRAPH_POLYGON", "prod")
        ],
    },
}

DEX_FEEGROWTH_SUBGRAPH_URLS = {
    "uniswap_v3": {
        "mainnet": uniswap_feegrowth_subgraphs["mainnet"][
            os.environ.get("UNISWAP_FG_SUBGRAPH_MAINNET", "prod")
        ],
        "polygon": uniswap_feegrowth_subgraphs["polygon"][
            os.environ.get("UNISWAP_FG_SUBGRAPH_POLYGON", "prod")
        ],
        "arbitrum": uniswap_feegrowth_subgraphs["arbitrum"][
            os.environ.get("UNISWAP_FG_SUBGRAPH_ARBITRUM", "prod")
        ],
        "optimism": uniswap_feegrowth_subgraphs["optimism"][
            os.environ.get("UNISWAP_FG_SUBGRAPH_OPTIMISM", "prod")
        ],
        "celo": uniswap_feegrowth_subgraphs["celo"][
            os.environ.get("UNISWAP_FG_SUBGRAPH_CELO", "prod")
        ],
    },
    "quickswap": {
        "polygon": quickswap_feegrowth_subgraphs["polygon"][
            os.environ.get("QUICKSWAP_FG_SUBGRAPH_POLYGON", "prod")
        ],
    },
}

VISOR_SUBGRAPH_URL = visor_subgraphs[os.environ.get("VISOR_SUBGRAPH", "prod")]

GAMMA_SUBGRAPH_URLS = {
    "uniswap_v3": {
        "mainnet": gamma_subgraphs["uniswap_v3"]["mainnet"][
            os.environ.get("GAMMA_SUBGRAPH_MAINNET", "prod")
        ],
        "polygon": gamma_subgraphs["uniswap_v3"]["polygon"][
            os.environ.get("GAMMA_SUBGRAPH_POLYGON", "prod")
        ],
        "arbitrum": gamma_subgraphs["uniswap_v3"]["arbitrum"][
            os.environ.get("GAMMA_SUBGRAPH_ARBITRUM", "prod")
        ],
        "optimism": gamma_subgraphs["uniswap_v3"]["optimism"][
            os.environ.get("GAMMA_SUBGRAPH_OPTIMISM", "prod")
        ],
        "celo": gamma_subgraphs["uniswap_v3"]["celo"][
            os.environ.get("GAMMA_SUBGRAPH_CELO", "prod")
        ],
    },
    "quickswap": {
        "polygon": gamma_subgraphs["quickswap"]["polygon"][
            os.environ.get("QUICKSWAP_SUBGRAPH_POLYGON", "prod")
        ],
    },
}


XGAMMA_SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/l0c4t0r/xgamma"


TOKEN_LIST_URL = "https://tokens.coingecko.com/uniswap/all.json"

DEFAULT_BBAND_INTERVALS = 20
DEFAULT_TIMEZONE = os.environ.get("TIMEZONE", "UTC-5")

CHARTS_CACHE_TIMEOUT = os.environ.get("CHARTS_CACHE_TIMEOUT", 600)
APY_CACHE_TIMEOUT = os.environ.get("APY_CACHE_TIMEOUT", 600)
DASHBOARD_CACHE_TIMEOUT = os.environ.get("DASHBOARD_CACHE_TIMEOUT", 600)
ALLDATA_CACHE_TIMEOUT = os.environ.get("ALLDATA_CACHE_TIMEOUT", 0)  # database call
DB_CACHE_TIMEOUT = os.environ.get("DB_CACHE_TIMEOUT", 0)  # database calls cache

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
    "mainnet": f"https://eth-mainnet.g.alchemy.com/v2/{os.environ.get('ALCHEMY_MAINNET_KEY', '')}",
    "polygon": f"https://polygon-mainnet.g.alchemy.com/v2/{os.environ.get('ALCHEMY_POLYGON_KEY', '')}",
    "optimism": f"https://opt-mainnet.g.alchemy.com/v2/{os.environ.get('ALCHEMY_OPTIMISM_KEY', '')}",
}

MONGO_DB_URL = os.environ.get("MONGO_DB_URL", "mongodb://localhost:27072")
MONGO_DB_TIMEOUTMS = os.environ.get("MONGO_DB_TIMEOUTMS", 2000)
MONGO_DB_COLLECTIONS = {
    "static": {"id": True},  #      no historic
    "returns": {"id": True},  #     historic
    "allData": {"id": True},  # id = <chain_protocol>       no historic
    "allRewards2": {"id": True},  # id = <chain_protocol>   no historic
    "agregateStats": {"id": True},  # id = <chain_protocol_timestamp>    historic
}
