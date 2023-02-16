from dataclasses import dataclass


@dataclass
class Time:
    block: int
    timestamp: int


@dataclass
class _TokenPair:
    value0: int
    value1: int

    def __post_init__(self):
        self.value0 = int(self.value0)
        self.value1 = int(self.value1)


@dataclass
class _TokenPairDecimals:
    value0: float
    value1: float

    def __post_init__(self):
        self.value0 = float(self.value0)
        self.value1 = float(self.value1)


@dataclass
class HypervisorStaticInfo:
    symbol: str
    decimals: _TokenPair


@dataclass
class _TickData:
    tick_index: int
    fee_growth_outside: _TokenPair

    def __post_init__(self):
        self.tick_index = int(self.tick_index)


@dataclass
class _PositionData:
    liquidity: int
    tokens_owed: _TokenPair
    fee_growth_inside: _TokenPair
    tick_lower: _TickData
    tick_upper: _TickData

    def __post_init__(self):
        self.liquidity = int(self.liquidity)


@dataclass
class FeesData:
    block: int
    timestamp: int
    hypervisor: str
    symbol: str
    currentTick: int
    price: _TokenPairDecimals
    decimals: _TokenPair
    tvl: _TokenPair
    tvl_usd: float
    fee_growth_global: _TokenPair
    base_position: _PositionData
    limit_position: _PositionData

    def __post_init__(self):
        self.block = int(self.block)
        self.timestamp = int(self.timestamp)
        self.currentTick = int(self.currentTick)
        self.tvl_usd = float(self.tvl_usd)


@dataclass
class UncollectedFees:
    base: _TokenPair
    limit: _TokenPair


@dataclass
class UncollectedFeesUsd:
    base: _TokenPairDecimals
    limit: _TokenPairDecimals


@dataclass
class FeesSnapshot:
    block: int
    timestamp: int
    tvl_usd: float
    total_fees_0: float
    total_fees_1: float
    price_0: float
    price_1: float

    def __post_init__(self):
        self.block = int(self.block)
        self.timestamp = int(self.timestamp)
        self.tvl_usd = float(self.tvl_usd)
        self.total_fees_0 = float(self.total_fees_0)
        self.total_fees_1 = float(self.total_fees_1)
        self.price_0 = float(self.price_0)
        self.price_1 = float(self.price_1)


@dataclass
class FeeYield:
    apr: float
    apy: float
    status: str

    def __post_init__(self):
        self.apr = float(self.apr)
        self.apy = float(self.apy)
