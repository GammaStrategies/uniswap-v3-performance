import os

dex_subgraphs = {
    "uniswap_v3": {
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
        },
    },
    "quickswap": {
        "polygon": {
            "prod": "https://api.thegraph.com/subgraphs/name/sameepsi/quickswap-v3"
        }
    },
    "zyberswap": {
        "arbitrum": {
            "prod": "https://api.thegraph.com/subgraphs/name/iliaazhel/zyberswap-info"
        }
    },
}


dex_feegrowth_subgraphs = {
    "uniswap_v3": {
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
        },
    },
    "quickswap": {
        "polygon": {
            "prod": "https://api.thegraph.com/subgraphs/name/sameepsi/quickswap-v3"
        }
    },
    "zyberswap": {
        "arbitrum": {
            "prod": "https://api.thegraph.com/subgraphs/name/iliaazhel/zyberswap-info"
        }
    },
}

hype_pool_subgraphs = {
    "uniswap_v3": {
        "mainnet": {
            "prod": "https://api.thegraph.com/subgraphs/name/l0c4t0r/hype-pool-uniswap-mainnet",
        },
        "polygon": {
            "prod": "https://api.thegraph.com/subgraphs/name/l0c4t0r/hype-pool-uniswap-polygon"
        },
        "arbitrum": {
            "prod": "https://api.thegraph.com/subgraphs/name/l0c4t0r/hype-pool-uniswap-arbitrum"
        },
        "optimism": {
            "prod": "https://api.thegraph.com/subgraphs/name/l0c4t0r/hype-pool-uniswap-optimism"
        },
        "celo": {
            "prod": "https://api.thegraph.com/subgraphs/name/l0c4t0r/hype-pool-uniswap-celo"
        },
    },
    "quickswap": {
        "polygon": {
            "prod": "https://api.thegraph.com/subgraphs/name/l0c4t0r/hype-pool-quickswap-polygon"
        }
    },
    "zyberswap": {
        "arbitrum": {
            "prod": "https://api.thegraph.com/subgraphs/name/l0c4t0r/hype-pool-zyberswap-arbitrum"
        }
    },
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
    "zyberswap": {
        "arbitrum": {
            "prod": "https://api.thegraph.com/subgraphs/name/gammastrategies/zyberswap-arbitrum",
        }
    },
}

THEGRAPH_INDEX_NODE_URL = "https://api.thegraph.com/index-node/graphql"
ETH_BLOCKS_SUBGRAPH_URL = (
    "https://api.thegraph.com/subgraphs/name/blocklytics/ethereum-blocks"
)
UNI_V2_SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/ianlapham/uniswapv2"

DEX_SUBGRAPH_URLS = {
    "uniswap_v3": {
        "mainnet": dex_subgraphs["uniswap_v3"]["mainnet"][
            os.environ.get("UNISWAP_SUBGRAPH_MAINNET", "prod")
        ],
        "polygon": dex_subgraphs["uniswap_v3"]["polygon"][
            os.environ.get("UNISWAP_SUBGRAPH_POLYGON", "prod")
        ],
        "arbitrum": dex_subgraphs["uniswap_v3"]["arbitrum"][
            os.environ.get("UNISWAP_SUBGRAPH_ARBITRUM", "prod")
        ],
        "optimism": dex_subgraphs["uniswap_v3"]["optimism"][
            os.environ.get("UNISWAP_SUBGRAPH_OPTIMISM", "prod")
        ],
        "celo": dex_subgraphs["uniswap_v3"]["celo"][
            os.environ.get("UNISWAP_SUBGRAPH_CELO", "prod")
        ],
    },
    "quickswap": {
        "polygon": dex_subgraphs["quickswap"]["polygon"][
            os.environ.get("QUICKSWAP_SUBGRAPH_POLYGON", "prod")
        ],
    },
    "zyberswap": {
        "arbitrum": dex_subgraphs["zyberswap"]["arbitrum"][
            os.environ.get("ZYBERSWAP_SUBGRAPH_ARBITRUM", "prod")
        ],
    },
}

DEX_FEEGROWTH_SUBGRAPH_URLS = {
    "uniswap_v3": {
        "mainnet": dex_feegrowth_subgraphs["uniswap_v3"]["mainnet"][
            os.environ.get("UNISWAP_FG_SUBGRAPH_MAINNET", "prod")
        ],
        "polygon": dex_feegrowth_subgraphs["uniswap_v3"]["polygon"][
            os.environ.get("UNISWAP_FG_SUBGRAPH_POLYGON", "prod")
        ],
        "arbitrum": dex_feegrowth_subgraphs["uniswap_v3"]["arbitrum"][
            os.environ.get("UNISWAP_FG_SUBGRAPH_ARBITRUM", "prod")
        ],
        "optimism": dex_feegrowth_subgraphs["uniswap_v3"]["optimism"][
            os.environ.get("UNISWAP_FG_SUBGRAPH_OPTIMISM", "prod")
        ],
        "celo": dex_feegrowth_subgraphs["uniswap_v3"]["celo"][
            os.environ.get("UNISWAP_FG_SUBGRAPH_CELO", "prod")
        ],
    },
    "quickswap": {
        "polygon": dex_feegrowth_subgraphs["quickswap"]["polygon"][
            os.environ.get("QUICKSWAP_FG_SUBGRAPH_POLYGON", "prod")
        ],
    },
    "zyberswap": {
        "arbitrum": dex_feegrowth_subgraphs["zyberswap"]["arbitrum"][
            os.environ.get("QUICKSWAP_FG_SUBGRAPH_POLYGON", "prod")
        ],
    },
}

DEX_HYPEPOOL_SUBGRAPH_URLS = {
    "uniswap_v3": {
        "mainnet": hype_pool_subgraphs["uniswap_v3"]["mainnet"][
            os.environ.get("UNISWAP_HP_SUBGRAPH_MAINNET", "prod")
        ],
        "polygon": hype_pool_subgraphs["uniswap_v3"]["polygon"][
            os.environ.get("UNISWAP_HP_SUBGRAPH_POLYGON", "prod")
        ],
        "arbitrum": hype_pool_subgraphs["uniswap_v3"]["arbitrum"][
            os.environ.get("UNISWAP_HP_SUBGRAPH_ARBITRUM", "prod")
        ],
        "optimism": hype_pool_subgraphs["uniswap_v3"]["optimism"][
            os.environ.get("UNISWAP_HP_SUBGRAPH_OPTIMISM", "prod")
        ],
        "celo": hype_pool_subgraphs["uniswap_v3"]["celo"][
            os.environ.get("UNISWAP_HP_SUBGRAPH_CELO", "prod")
        ],
    },
    "quickswap": {
        "polygon": hype_pool_subgraphs["quickswap"]["polygon"][
            os.environ.get("QUICKSWAP_HP_SUBGRAPH_POLYGON", "prod")
        ],
    },
    "zyberswap": {
        "arbitrum": hype_pool_subgraphs["zyberswap"]["arbitrum"][
            os.environ.get("ZYBERSWAP_HP_SUBGRAPH_ARBITRUM", "prod")
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
            os.environ.get("GAMMA_QUICKSWAP_POLYGON_SUBGRAPH", "prod")
        ],
    },
    "zyberswap": {
        "arbitrum": gamma_subgraphs["zyberswap"]["arbitrum"][
            os.environ.get("GAMMA_ZYBERSWAP_ARBITRUM_SUBGRAPH", "prod")
        ],
    },
}


XGAMMA_SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/l0c4t0r/xgamma"


TOKEN_LIST_URL = "https://tokens.coingecko.com/uniswap/all.json"

DEFAULT_BBAND_INTERVALS = 20
DEFAULT_TIMEZONE = os.environ.get("TIMEZONE", "UTC-5")

CHARTS_CACHE_TIMEOUT = int(os.environ.get("CHARTS_CACHE_TIMEOUT", 600))
APY_CACHE_TIMEOUT = int(os.environ.get("APY_CACHE_TIMEOUT", 600))
DASHBOARD_CACHE_TIMEOUT = int(os.environ.get("DASHBOARD_CACHE_TIMEOUT", 600))
ALLDATA_CACHE_TIMEOUT = int(os.environ.get("ALLDATA_CACHE_TIMEOUT", 600))
DB_CACHE_TIMEOUT = int(os.environ.get("DB_CACHE_TIMEOUT", 160))  # database calls cache

EXCLUDED_HYPERVISORS = list(
    filter(None, os.environ.get("EXCLUDED_HYPES", "").split(","))
)
FALLBACK_DAYS = int(os.environ.get("FALLBACK_DAYS", 90))

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
MONGO_DB_TIMEOUTMS = int(os.environ.get("MONGO_DB_TIMEOUTMS", 2000))
MONGO_DB_COLLECTIONS = {
    "static": {"id": True},  # no historic
    "returns": {"id": True},  # historic
    "allData": {"id": True},  # id = <chain_protocol>       no historic
    "allRewards2": {"id": True},  # id = <chain_protocol>   no historic
    "agregateStats": {"id": True},  # id = <chain_protocol_timestamp>    historic
}

# local chain name <-> standard chain short name convention as in
# https://chainid.network/chains.json  or https://chainid.network/chains_mini.json
CHAIN_NAME_CONVERSION = {
    "eth": "mainnet",
    "matic": "polygon",
    "oeth": "optimism",
    "arb1": "arbitrum",
    "celo": "celo",
}

# Max fees per rebalance to remove outliers
GROSS_FEES_MAX = 10**6
