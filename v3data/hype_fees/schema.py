from dataclasses import dataclass, field, InitVar

from v3data.constants import X128


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
class _FeeAmounts:
    amount: _TokenPairDecimals = field(init=False)
    amount_x128: _TokenPair = field(init=False)
    decimals: _TokenPair = field(init=False)
    usd: _TokenPairDecimals = field(init=False)
    amount0_x128: InitVar[int]
    amount1_x128: InitVar[int]
    decimals0: InitVar[int]
    decimals1: InitVar[int]
    price0: InitVar[float]
    price1: InitVar[float]

    def __post_init__(
        self,
        amount0_x128: int,
        amount1_x128: int,
        decimals0: int,
        decimals1: int,
        price0: float,
        price1: float,
    ) -> None:
        self.amount_x128 = _TokenPair(amount0_x128, amount1_x128)
        self.decimals = _TokenPair(decimals0, decimals1)
        self._adjust_values()
        self._calculate_usd(price0, price1)

    def _adjust_values(self) -> None:
        self.amount = _TokenPairDecimals(
            self.amount_x128.value0 / (10**self.decimals.value0) / X128,
            self.amount_x128.value1 / (10**self.decimals.value1) / X128,
        )

    def _calculate_usd(self, price0: float, price1: float) -> None:
        self.usd = _TokenPairDecimals(
            self.amount.value0 * price0,
            self.amount.value1 * price1,
        )


@dataclass
class PositionFees:
    fees: _FeeAmounts = field(init=False)
    owed: _FeeAmounts = field(init=False)
    total: _FeeAmounts = field(init=False)
    fees0_x128: InitVar[int]
    fees1_x128: InitVar[int]
    owed0_x128: InitVar[int]
    owed1_x128: InitVar[int]
    decimals0: InitVar[int]
    decimals1: InitVar[int]
    price0: InitVar[float]
    price1: InitVar[float]

    def __post_init__(
        self,
        fees0_x128: int,
        fees1_x128: int,
        owed0_x128: int,
        owed1_x128: int,
        decimals0: int,
        decimals1: int,
        price0: float,
        price1: float,
    ):
        self.fees = _FeeAmounts(
            amount0_x128=fees0_x128,
            amount1_x128=fees1_x128,
            decimals0=decimals0,
            decimals1=decimals1,
            price0=price0,
            price1=price1,
        )
        self.owed = _FeeAmounts(
            amount0_x128=owed0_x128,
            amount1_x128=owed1_x128,
            decimals0=decimals0,
            decimals1=decimals1,
            price0=price0,
            price1=price1,
        )
        self._calculate_totals(decimals0, decimals1, price0, price1)

    def _calculate_totals(
        self, decimals0: int, decimals1: int, price0: float, price1: float
    ):
        self.total = _FeeAmounts(
            amount0_x128=self.fees.amount_x128.value0 + self.owed.amount_x128.value0,
            amount1_x128=self.fees.amount_x128.value1 + self.owed.amount_x128.value1,
            decimals0=decimals0,
            decimals1=decimals1,
            price0=price0,
            price1=price1,
        )


@dataclass
class UncollectedFees:
    base: PositionFees = field(init=False)
    limit: PositionFees = field(init=False)
    total: _FeeAmounts = field(init=False)
    base_fees0_x128: InitVar[int]
    base_fees1_x128: InitVar[int]
    base_owed0_x128: InitVar[int]
    base_owed1_x128: InitVar[int]
    limit_fees0_x128: InitVar[int]
    limit_fees1_x128: InitVar[int]
    limit_owed0_x128: InitVar[int]
    limit_owed1_x128: InitVar[int]
    decimals0: InitVar[int]
    decimals1: InitVar[int]
    price0: InitVar[float]
    price1: InitVar[float]

    def __post_init__(
        self,
        base_fees0_x128: int,
        base_fees1_x128: int,
        base_owed0_x128: int,
        base_owed1_x128: int,
        limit_fees0_x128: int,
        limit_fees1_x128: int,
        limit_owed0_x128: int,
        limit_owed1_x128: int,
        decimals0: int,
        decimals1: int,
        price0: float,
        price1: float,
    ):
        self.base = PositionFees(
            fees0_x128=base_fees0_x128,
            fees1_x128=base_fees1_x128,
            owed0_x128=base_owed0_x128,
            owed1_x128=base_owed1_x128,
            decimals0=decimals0,
            decimals1=decimals1,
            price0=price0,
            price1=price1,
        )
        self.limit = PositionFees(
            fees0_x128=limit_fees0_x128,
            fees1_x128=limit_fees1_x128,
            owed0_x128=limit_owed0_x128,
            owed1_x128=base_owed1_x128,
            decimals0=decimals0,
            decimals1=decimals1,
            price0=price0,
            price1=price1,
        )
        self._calculate_totals(decimals0, decimals1, price0, price1)

    def _calculate_totals(
        self, decimals0: int, decimals1: int, price0: float, price1: float
    ):
        self.total = _FeeAmounts(
            amount0_x128=self.base.fees.amount_x128.value0
            + self.base.owed.amount_x128.value0
            + self.limit.fees.amount_x128.value0
            + self.limit.owed.amount_x128.value0,
            amount1_x128=self.base.fees.amount_x128.value1
            + self.base.owed.amount_x128.value1
            + self.limit.fees.amount_x128.value1
            + self.limit.owed.amount_x128.value1,
            decimals0=decimals0,
            decimals1=decimals1,
            price0=price0,
            price1=price1,
        )


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
