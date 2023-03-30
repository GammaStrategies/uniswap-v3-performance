"""Initialise configurations"""

import os

import yaml

from v3data.enums import Chain, Protocol, QueryType, Enum

try:
    with open("config.yaml", mode="r", encoding="utf-8") as stream:
        YAML_CONFIG = yaml.safe_load(stream)
except FileNotFoundError:
    YAML_CONFIG = None

with open("config.defaults.yaml", mode="r", encoding="utf-8") as stream:
    YAML_CONFIG_DEFAULTS = yaml.safe_load(stream)


def get_config(key: str):
    """Find config in env var/config.yaml"""
    value = os.environ.get(key)
    if not value and YAML_CONFIG:
        value = YAML_CONFIG.get(key)
    if not value:
        value = YAML_CONFIG_DEFAULTS[key]
    return value


def convert_to_enum(string: str, enum: Enum, default=None):
    """converts a string to an enum

    Args:
        string (str): string to be converted
        enum (Enum): enum to convert to
        default (Enum, optional): default value to return if the string cannot be converted to the enum. Defaults to None.

    Raises:
        ValueError: if the string can't be converted to the enum

    Returns:
        Enum: the converted enum
    """
    for itm in enum:  # for each item in the enum
        if string == itm.value:  # if the string is the same as the items's value
            return itm  # return the item
    else:  # otherwise
        if default:  # if a default is provided
            return default
        else:  # otherwise
            raise ValueError(f"can't convert {string} to Enum")  # raise a ValueError


DEPLOYMENTS = [
    (Protocol.UNISWAP, Chain.MAINNET),
    (Protocol.UNISWAP, Chain.ARBITRUM),
    (Protocol.UNISWAP, Chain.OPTIMISM),
    (Protocol.UNISWAP, Chain.POLYGON),
    (Protocol.UNISWAP, Chain.BSC),
    (Protocol.UNISWAP, Chain.CELO),
    (Protocol.QUICKSWAP, Chain.POLYGON),
    (Protocol.ZYBERSWAP, Chain.ARBITRUM),
    (Protocol.THENA, Chain.BSC),
]

THEGRAPH_INDEX_NODE_URL = "https://api.thegraph.com/index-node/graphql"
ETH_BLOCKS_SUBGRAPH_URL = (
    "https://api.thegraph.com/subgraphs/name/blocklytics/ethereum-blocks"
)
UNI_V2_SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/ianlapham/uniswapv2"


DEX_SUBGRAPH_URLS = {
    Protocol.UNISWAP: {
        Chain.MAINNET: get_config("UNISWAP_MAINNET_SUBGRAPH_URL"),
        Chain.POLYGON: get_config("UNISWAP_POLYGON_SUBGRAPH_URL"),
        Chain.ARBITRUM: get_config("UNISWAP_ARBITRUM_SUBGRAPH_URL"),
        Chain.OPTIMISM: get_config("UNISWAP_OPTIMISM_SUBGRAPH_URL"),
        Chain.CELO: get_config("UNISWAP_CELO_SUBGRAPH_URL"),
        Chain.BSC: get_config("UNISWAP_BSC_SUBGRAPH_URL"),
    },
    Protocol.QUICKSWAP: {
        Chain.POLYGON: get_config("QUICKSWAP_POLYGON_SUBGRAPH_URL"),
    },
    Protocol.ZYBERSWAP: {
        Chain.ARBITRUM: get_config("ZYBERSWAP_ARBITRUM_SUBGRAPH_URL"),
    },
    Protocol.THENA: {
        Chain.BSC: get_config("THENA_BSC_SUBGRAPH_URL"),
    },
}

DEX_HYPEPOOL_SUBGRAPH_URLS = {
    Protocol.UNISWAP: {
        Chain.MAINNET: get_config("UNISWAP_MAINNET_HP_SUBGRAPH_URL"),
        Chain.POLYGON: get_config("UNISWAP_POLYGON_HP_SUBGRAPH_URL"),
        Chain.ARBITRUM: get_config("UNISWAP_ARBITRUM_HP_SUBGRAPH_URL"),
        Chain.OPTIMISM: get_config("UNISWAP_OPTIMISM_HP_SUBGRAPH_URL"),
        Chain.CELO: get_config("UNISWAP_CELO_HP_SUBGRAPH_URL"),
        Chain.BSC: get_config("UNISWAP_BSC_HP_SUBGRAPH_URL"),
    },
    Protocol.QUICKSWAP: {
        Chain.POLYGON: get_config("QUICKSWAP_POLYGON_HP_SUBGRAPH_URL"),
    },
    Protocol.ZYBERSWAP: {
        Chain.ARBITRUM: get_config("ZYBERSWAP_ARBITRUM_HP_SUBGRAPH_URL"),
    },
    Protocol.THENA: {
        Chain.BSC: get_config("THENA_BSC_HP_SUBGRAPH_URL"),
    },
}

GAMMA_SUBGRAPH_URLS = {
    Protocol.UNISWAP: {
        Chain.MAINNET: get_config("UNISWAP_MAINNET_GAMMA_SUBGRAPH_URL"),
        Chain.POLYGON: get_config("UNISWAP_POLYGON_GAMMA_SUBGRAPH_URL"),
        Chain.ARBITRUM: get_config("UNISWAP_ARBITRUM_GAMMA_SUBGRAPH_URL"),
        Chain.OPTIMISM: get_config("UNISWAP_OPTIMISM_GAMMA_SUBGRAPH_URL"),
        Chain.CELO: get_config("UNISWAP_CELO_GAMMA_SUBGRAPH_URL"),
        Chain.BSC: get_config("UNISWAP_BSC_GAMMA_SUBGRAPH_URL"),
    },
    Protocol.QUICKSWAP: {
        Chain.POLYGON: get_config("QUICKSWAP_POLYGON_GAMMA_SUBGRAPH_URL"),
    },
    Protocol.ZYBERSWAP: {
        Chain.ARBITRUM: get_config("ZYBERSWAP_ARBITRUM_GAMMA_SUBGRAPH_URL"),
    },
    Protocol.THENA: {
        Chain.BSC: get_config("THENA_BSC_GAMMA_SUBGRAPH_URL"),
    },
}

XGAMMA_SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/l0c4t0r/xgamma"

DEFAULT_TIMEZONE = get_config("TIMEZONE")

CHARTS_CACHE_TIMEOUT = int(get_config("CHARTS_CACHE_TIMEOUT"))
APY_CACHE_TIMEOUT = int(get_config("APY_CACHE_TIMEOUT"))
DASHBOARD_CACHE_TIMEOUT = int(get_config("DASHBOARD_CACHE_TIMEOUT"))
ALLDATA_CACHE_TIMEOUT = int(get_config("ALLDATA_CACHE_TIMEOUT"))
DB_CACHE_TIMEOUT = int(get_config("DB_CACHE_TIMEOUT"))  # database calls cache

EXCLUDED_HYPERVISORS = list(filter(None, get_config("EXCLUDED_HYPES").split(",")))

legacy_stats = {
    "visr_distributed": 987998.1542393989,
    "visr_distributed_usd": 1246656.7073805775,
    "estimated_visr_annual_distribution": 1237782.0442017058,
    "estimated_visr_annual_distribution_usd": 1197097.0895269862,
}

MONGO_DB_URL = get_config("MONGO_DB_URL")
MONGO_DB_TIMEOUTMS = int(get_config("MONGO_DB_TIMEOUTMS"))
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

GQL_CLIENT_TIMEOUT = int(get_config("GQL_CLIENT_TIMEOUT"))

# What to run first
RUN_FIRST_QUERY_TYPE = convert_to_enum(
    get_config("RUN_FIRST_QUERY_TYPE"), QueryType, QueryType.SUBGRAPH
)
