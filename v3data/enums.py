from enum import Enum


class Chain(str, Enum):
    ARBITRUM = "arbitrum"
    CELO = "celo"
    MAINNET = "mainnet"
    OPTIMISM = "optimism"
    POLYGON = "polygon"


class PositionType(str, Enum):
    BASE = "base"
    LIMIT = "limit"


class Protocol(str, Enum):
    QUICKSWAP = "quickswap"
    UNISWAP = "uniswap"
    ZYBERSWAP = "zyberswap"


class QueryType(str, Enum):
    DATABASE = "database"
    SUBGRAPH = "subgraph"
