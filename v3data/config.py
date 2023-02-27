import os

from v3data.enums import Chain, Protocol

dex_subgraphs = {
    Protocol.UNISWAP: {
        Chain.MAINNET: {
            "prod": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
            "alt": "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-alt",
            "test": "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-testing",
        },
        Chain.POLYGON: {
            "prod": "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-polygon"
        },
        Chain.ARBITRUM: {
            "prod": "https://api.thegraph.com/subgraphs/name/ianlapham/arbitrum-dev"
        },
        Chain.OPTIMISM: {
            "prod": "https://api.thegraph.com/subgraphs/name/ianlapham/optimism-post-regenesis"
        },
        Chain.CELO: {
            "prod": "https://api.thegraph.com/subgraphs/name/jesse-sawa/uniswap-celo"
        },
    },
    Protocol.QUICKSWAP: {
        Chain.POLYGON: {
            "prod": "https://api.thegraph.com/subgraphs/name/sameepsi/quickswap-v3"
        }
    },
    Protocol.ZYBERSWAP: {
        Chain.ARBITRUM: {
            "prod": "https://api.thegraph.com/subgraphs/name/iliaazhel/zyberswap-info"
        }
    },
}


dex_feegrowth_subgraphs = {
    Protocol.UNISWAP: {
        Chain.MAINNET: {
            "prod": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
            "alt": "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-alt",
            "test": "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-testing",
        },
        Chain.POLYGON: {
            "prod": "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-polygon"
        },
        Chain.ARBITRUM: {
            "prod": "https://api.thegraph.com/subgraphs/name/ianlapham/arbitrum-dev"
        },
        Chain.OPTIMISM: {
            "prod": "https://api.thegraph.com/subgraphs/name/ianlapham/optimism-post-regenesis"
        },
        Chain.CELO: {
            "prod": "https://api.thegraph.com/subgraphs/name/jesse-sawa/uniswap-celo"
        },
    },
    Protocol.QUICKSWAP: {
        Chain.POLYGON: {
            "prod": "https://api.thegraph.com/subgraphs/name/sameepsi/quickswap-v3"
        }
    },
    Protocol.ZYBERSWAP: {
        Chain.ARBITRUM: {
            "prod": "https://api.thegraph.com/subgraphs/name/iliaazhel/zyberswap-info"
        }
    },
}

hype_pool_subgraphs = {
    Protocol.UNISWAP: {
        Chain.MAINNET: {
            "prod": "https://api.thegraph.com/subgraphs/name/l0c4t0r/hype-pool-uniswap-mainnet",
        },
        Chain.POLYGON: {
            "prod": "https://api.thegraph.com/subgraphs/name/l0c4t0r/hype-pool-uniswap-polygon"
        },
        Chain.ARBITRUM: {
            "prod": "https://api.thegraph.com/subgraphs/name/l0c4t0r/hype-pool-uniswap-arbitrum"
        },
        Chain.OPTIMISM: {
            "prod": "https://api.thegraph.com/subgraphs/name/l0c4t0r/hype-pool-uniswap-optimism"
        },
        Chain.CELO: {
            "prod": "https://api.thegraph.com/subgraphs/name/l0c4t0r/hype-pool-uniswap-celo"
        },
    },
    Protocol.QUICKSWAP: {
        Chain.POLYGON: {
            "prod": "https://api.thegraph.com/subgraphs/name/l0c4t0r/hype-pool-quickswap-polygon"
        }
    },
    Protocol.ZYBERSWAP: {
        Chain.ARBITRUM: {
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
    Protocol.UNISWAP: {
        Chain.MAINNET: {
            "prod": "https://api.thegraph.com/subgraphs/name/gammastrategies/gamma",
            "test": "https://api.thegraph.com/subgraphs/name/l0c4t0r/gamma",
            "lab": "https://api.thegraph.com/subgraphs/name/l0c4t0r/laboratory",
        },
        Chain.POLYGON: {
            "prod": "https://api.thegraph.com/subgraphs/name/gammastrategies/polygon",
            "test": "https://api.thegraph.com/subgraphs/name/l0c4t0r/gamma-polygon",
        },
        Chain.ARBITRUM: {
            "prod": "https://api.thegraph.com/subgraphs/name/gammastrategies/arbitrum",
            "test": "https://api.thegraph.com/subgraphs/name/l0c4t0r/visor-arbitrum",
        },
        Chain.OPTIMISM: {
            "prod": "https://api.thegraph.com/subgraphs/name/gammastrategies/optimism",
            "test": "https://api.thegraph.com/subgraphs/name/l0c4t0r/gamma-optimism",
        },
        Chain.CELO: {
            "prod": "https://api.thegraph.com/subgraphs/name/gammastrategies/celo",
            "test": "https://api.thegraph.com/subgraphs/name/l0c4t0r/gamma-celo",
        },
    },
    Protocol.QUICKSWAP: {
        Chain.POLYGON: {
            "prod": "https://api.thegraph.com/subgraphs/name/gammastrategies/algebra-polygon",
            "test": "https://api.thegraph.com/subgraphs/name/l0c4t0r/gamma-algebra-polygon",
        },
    },
    Protocol.ZYBERSWAP: {
        Chain.ARBITRUM: {
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
    Protocol.UNISWAP: {
        Chain.MAINNET: dex_subgraphs[Protocol.UNISWAP][Chain.MAINNET][
            os.environ.get("UNISWAP_SUBGRAPH_MAINNET", "prod")
        ],
        Chain.POLYGON: dex_subgraphs[Protocol.UNISWAP][Chain.POLYGON][
            os.environ.get("UNISWAP_SUBGRAPH_POLYGON", "prod")
        ],
        Chain.ARBITRUM: dex_subgraphs[Protocol.UNISWAP][Chain.ARBITRUM][
            os.environ.get("UNISWAP_SUBGRAPH_ARBITRUM", "prod")
        ],
        Chain.OPTIMISM: dex_subgraphs[Protocol.UNISWAP][Chain.OPTIMISM][
            os.environ.get("UNISWAP_SUBGRAPH_OPTIMISM", "prod")
        ],
        Chain.CELO: dex_subgraphs[Protocol.UNISWAP][Chain.CELO][
            os.environ.get("UNISWAP_SUBGRAPH_CELO", "prod")
        ],
    },
    Protocol.QUICKSWAP: {
        Chain.POLYGON: dex_subgraphs[Protocol.QUICKSWAP][Chain.POLYGON][
            os.environ.get("QUICKSWAP_SUBGRAPH_POLYGON", "prod")
        ],
    },
    Protocol.ZYBERSWAP: {
        Chain.ARBITRUM: dex_subgraphs[Protocol.ZYBERSWAP][Chain.ARBITRUM][
            os.environ.get("ZYBERSWAP_SUBGRAPH_ARBITRUM", "prod")
        ],
    },
}

DEX_FEEGROWTH_SUBGRAPH_URLS = {
    Protocol.UNISWAP: {
        Chain.MAINNET: dex_feegrowth_subgraphs[Protocol.UNISWAP][Chain.MAINNET][
            os.environ.get("UNISWAP_FG_SUBGRAPH_MAINNET", "prod")
        ],
        Chain.POLYGON: dex_feegrowth_subgraphs[Protocol.UNISWAP][Chain.POLYGON][
            os.environ.get("UNISWAP_FG_SUBGRAPH_POLYGON", "prod")
        ],
        Chain.ARBITRUM: dex_feegrowth_subgraphs[Protocol.UNISWAP][Chain.ARBITRUM][
            os.environ.get("UNISWAP_FG_SUBGRAPH_ARBITRUM", "prod")
        ],
        Chain.OPTIMISM: dex_feegrowth_subgraphs[Protocol.UNISWAP][Chain.OPTIMISM][
            os.environ.get("UNISWAP_FG_SUBGRAPH_OPTIMISM", "prod")
        ],
        Chain.CELO: dex_feegrowth_subgraphs[Protocol.UNISWAP][Chain.CELO][
            os.environ.get("UNISWAP_FG_SUBGRAPH_CELO", "prod")
        ],
    },
    Protocol.QUICKSWAP: {
        Chain.POLYGON: dex_feegrowth_subgraphs[Protocol.QUICKSWAP][Chain.POLYGON][
            os.environ.get("QUICKSWAP_FG_SUBGRAPH_POLYGON", "prod")
        ],
    },
    Protocol.ZYBERSWAP: {
        Chain.ARBITRUM: dex_feegrowth_subgraphs[Protocol.ZYBERSWAP][Chain.ARBITRUM][
            os.environ.get("QUICKSWAP_FG_SUBGRAPH_POLYGON", "prod")
        ],
    },
}

DEX_HYPEPOOL_SUBGRAPH_URLS = {
    Protocol.UNISWAP: {
        Chain.MAINNET: hype_pool_subgraphs[Protocol.UNISWAP][Chain.MAINNET][
            os.environ.get("UNISWAP_HP_SUBGRAPH_MAINNET", "prod")
        ],
        Chain.POLYGON: hype_pool_subgraphs[Protocol.UNISWAP][Chain.POLYGON][
            os.environ.get("UNISWAP_HP_SUBGRAPH_POLYGON", "prod")
        ],
        Chain.ARBITRUM: hype_pool_subgraphs[Protocol.UNISWAP][Chain.ARBITRUM][
            os.environ.get("UNISWAP_HP_SUBGRAPH_ARBITRUM", "prod")
        ],
        Chain.OPTIMISM: hype_pool_subgraphs[Protocol.UNISWAP][Chain.OPTIMISM][
            os.environ.get("UNISWAP_HP_SUBGRAPH_OPTIMISM", "prod")
        ],
        Chain.CELO: hype_pool_subgraphs[Protocol.UNISWAP][Chain.CELO][
            os.environ.get("UNISWAP_HP_SUBGRAPH_CELO", "prod")
        ],
    },
    Protocol.QUICKSWAP: {
        Chain.POLYGON: hype_pool_subgraphs[Protocol.QUICKSWAP][Chain.POLYGON][
            os.environ.get("QUICKSWAP_HP_SUBGRAPH_POLYGON", "prod")
        ],
    },
    Protocol.ZYBERSWAP: {
        Chain.ARBITRUM: hype_pool_subgraphs[Protocol.ZYBERSWAP][Chain.ARBITRUM][
            os.environ.get("ZYBERSWAP_HP_SUBGRAPH_ARBITRUM", "prod")
        ],
    },
}

VISOR_SUBGRAPH_URL = visor_subgraphs[os.environ.get("VISOR_SUBGRAPH", "prod")]

GAMMA_SUBGRAPH_URLS = {
    Protocol.UNISWAP: {
        Chain.MAINNET: gamma_subgraphs[Protocol.UNISWAP][Chain.MAINNET][
            os.environ.get("GAMMA_SUBGRAPH_MAINNET", "prod")
        ],
        Chain.POLYGON: gamma_subgraphs[Protocol.UNISWAP][Chain.POLYGON][
            os.environ.get("GAMMA_SUBGRAPH_POLYGON", "prod")
        ],
        Chain.ARBITRUM: gamma_subgraphs[Protocol.UNISWAP][Chain.ARBITRUM][
            os.environ.get("GAMMA_SUBGRAPH_ARBITRUM", "prod")
        ],
        Chain.OPTIMISM: gamma_subgraphs[Protocol.UNISWAP][Chain.OPTIMISM][
            os.environ.get("GAMMA_SUBGRAPH_OPTIMISM", "prod")
        ],
        Chain.CELO: gamma_subgraphs[Protocol.UNISWAP][Chain.CELO][
            os.environ.get("GAMMA_SUBGRAPH_CELO", "prod")
        ],
    },
    Protocol.QUICKSWAP: {
        Chain.POLYGON: gamma_subgraphs[Protocol.QUICKSWAP][Chain.POLYGON][
            os.environ.get("GAMMA_QUICKSWAP_POLYGON_SUBGRAPH", "prod")
        ],
    },
    Protocol.ZYBERSWAP: {
        Chain.ARBITRUM: gamma_subgraphs[Protocol.ZYBERSWAP][Chain.ARBITRUM][
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
    Chain.MAINNET: f"https://eth-mainnet.g.alchemy.com/v2/{os.environ.get('ALCHEMY_MAINNET_KEY', '')}",
    Chain.POLYGON: f"https://polygon-mainnet.g.alchemy.com/v2/{os.environ.get('ALCHEMY_POLYGON_KEY', '')}",
    Chain.OPTIMISM: f"https://opt-mainnet.g.alchemy.com/v2/{os.environ.get('ALCHEMY_OPTIMISM_KEY', '')}",
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
    "eth": Chain.MAINNET,
    "matic": Chain.POLYGON,
    "oeth": Chain.OPTIMISM,
    "arb1": Chain.ARBITRUM,
    "celo": Chain.CELO,
}

# Max fees per rebalance to remove outliers
GROSS_FEES_MAX = 10**6
