from dataclasses import dataclass, field, InitVar

from v3data.constants import X128


@dataclass
class Time:
    block: int
    timestamp: int


@dataclass
class ValueWithDecimal:
    raw: int
    adjusted: float = field(init=False)
    decimals: int

    def __post_init__(self):
        self.raw = int(self.raw)
        self.decimals = int(self.decimals)
        self.adjusted = self.raw / 10**self.decimals


@dataclass
class _TokenPair:
    value0: ValueWithDecimal = field(init=False)
    value1: ValueWithDecimal = field(init=False)
    raw0: InitVar[int]
    raw1: InitVar[int]
    decimals0: InitVar[int]
    decimals1: InitVar[int]

    def __post_init__(self, raw0: int, raw1: int, decimals0: int, decimals1: int):
        self.value0 = ValueWithDecimal(raw=raw0, decimals=decimals0)
        self.value1 = ValueWithDecimal(raw=raw1, decimals=decimals1)


@dataclass
class _TokenPairInt:
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
    decimals: _TokenPairInt = field(init=False)
    decimals0: InitVar[int]
    decimals1: InitVar[int]

    def __post_init__(self, decimals0: int, decimals1: int):
        self.decimals = _TokenPairInt(value0=decimals0, value1=decimals1)


@dataclass
class _TickData:
    tick_index: int
    fee_growth_outside: _TokenPairInt = field(init=False)
    fee_growth_outside0: InitVar[int]
    fee_growth_outside1: InitVar[int]

    def __post_init__(
        self,
        fee_growth_outside0: int,
        fee_growth_outside1: int,
    ):
        self.tick_index = int(self.tick_index)
        self.fee_growth_outside = _TokenPairInt(
            value0=fee_growth_outside0,
            value1=fee_growth_outside1,
        )


@dataclass
class _PositionData:
    liquidity: int
    tokens_owed: _TokenPair = field(init=False)
    fee_growth_inside: _TokenPairInt = field(init=False)
    tick_lower: _TickData = field(init=False)
    tick_upper: _TickData = field(init=False)
    tokens_owed0: InitVar[int]
    tokens_owed1: InitVar[int]
    fee_growth_inside0: InitVar[int]
    fee_growth_inside1: InitVar[int]
    tick_index_lower: InitVar[int]
    fee_growth_outside_lower0: InitVar[int]
    fee_growth_outside_lower1: InitVar[int]
    tick_index_upper: InitVar[int]
    fee_growth_outside_upper0: InitVar[int]
    fee_growth_outside_upper1: InitVar[int]
    decimals0: InitVar[int]
    decimals1: InitVar[int]

    def __post_init__(
        self,
        tokens_owed0: int,
        tokens_owed1: int,
        fee_growth_inside0: int,
        fee_growth_inside1: int,
        tick_index_lower: int,
        fee_growth_outside_lower0: int,
        fee_growth_outside_lower1: int,
        tick_index_upper: int,
        fee_growth_outside_upper0: int,
        fee_growth_outside_upper1: int,
        decimals0: int,
        decimals1: int,
    ):
        self.liquidity = int(self.liquidity)
        self.tokens_owed = _TokenPair(
            raw0=tokens_owed0,
            raw1=tokens_owed1,
            decimals0=decimals0,
            decimals1=decimals1,
        )
        self.fee_growth_inside = _TokenPairInt(
            value0=fee_growth_inside0,
            value1=fee_growth_inside1,
        )
        self.tick_lower = _TickData(
            tick_index=tick_index_lower,
            fee_growth_outside0=fee_growth_outside_lower0,
            fee_growth_outside1=fee_growth_outside_lower1,
        )
        self.tick_upper = _TickData(
            tick_index=tick_index_upper,
            fee_growth_outside0=fee_growth_outside_upper0,
            fee_growth_outside1=fee_growth_outside_upper1,
        )


@dataclass
class FeesData:
    block: int
    timestamp: int
    hypervisor: str
    symbol: str
    currentTick: int
    price: _TokenPairDecimals = field(init=False)
    decimals: _TokenPairInt = field(init=False)
    tvl: _TokenPair = field(init=False)
    tvl_usd: float
    fee_growth_global: _TokenPairInt = field(init=False)
    base_position: _PositionData = field(init=False)
    limit_position: _PositionData = field(init=False)
    price0: InitVar[float]
    price1: InitVar[float]
    decimals0: InitVar[int]
    decimals1: InitVar[int]
    tvl0: InitVar[int]
    tvl1: InitVar[int]
    fee_growth_global0: InitVar[int]
    fee_growth_global1: InitVar[int]
    liquidity_base: InitVar[int]
    tokens_owed_base0: InitVar[int]
    tokens_owed_base1: InitVar[int]
    fee_growth_inside_base0: InitVar[int]
    fee_growth_inside_base1: InitVar[int]
    tick_index_lower_base: InitVar[int]
    fee_growth_outside_lower_base0: InitVar[int]
    fee_growth_outside_lower_base1: InitVar[int]
    tick_index_upper_base: InitVar[int]
    fee_growth_outside_upper_base0: InitVar[int]
    fee_growth_outside_upper_base1: InitVar[int]
    liquidity_limit: InitVar[int]
    tokens_owed_limit0: InitVar[int]
    tokens_owed_limit1: InitVar[int]
    fee_growth_inside_limit0: InitVar[int]
    fee_growth_inside_limit1: InitVar[int]
    tick_index_lower_limit: InitVar[int]
    fee_growth_outside_lower_limit0: InitVar[int]
    fee_growth_outside_lower_limit1: InitVar[int]
    tick_index_upper_limit: InitVar[int]
    fee_growth_outside_upper_limit0: InitVar[int]
    fee_growth_outside_upper_limit1: InitVar[int]
    total_supply: ValueWithDecimal | None = field(init=False)
    total_supply: InitVar[int | None] = None
    total_supply_decimals: InitVar[int] = 0

    def __post_init__(
        self,
        price0: float,
        price1: float,
        decimals0: int,
        decimals1: int,
        tvl0: int,
        tvl1: int,
        fee_growth_global0: int,
        fee_growth_global1: int,
        liquidity_base: int,
        tokens_owed_base0: int,
        tokens_owed_base1: int,
        fee_growth_inside_base0: int,
        fee_growth_inside_base1: int,
        tick_index_lower_base: int,
        fee_growth_outside_lower_base0: int,
        fee_growth_outside_lower_base1: int,
        tick_index_upper_base: int,
        fee_growth_outside_upper_base0: int,
        fee_growth_outside_upper_base1: int,
        liquidity_limit: int,
        tokens_owed_limit0: int,
        tokens_owed_limit1: int,
        fee_growth_inside_limit0: int,
        fee_growth_inside_limit1: int,
        tick_index_lower_limit: int,
        fee_growth_outside_lower_limit0: int,
        fee_growth_outside_lower_limit1: int,
        tick_index_upper_limit: int,
        fee_growth_outside_upper_limit0: int,
        fee_growth_outside_upper_limit1: int,
        total_supply: int | None = None,
        total_supply_decimals: int = 0,
    ):
        self.block = int(self.block)
        self.timestamp = int(self.timestamp)
        self.currentTick = int(self.currentTick)
        self.tvl_usd = float(self.tvl_usd)

        self.price = _TokenPairDecimals(value0=price0, value1=price1)
        self.decimals = _TokenPairInt(value0=decimals0, value1=decimals1)
        self.tvl = _TokenPair(
            raw0=tvl0, raw1=tvl1, decimals0=decimals0, decimals1=decimals1
        )
        self.fee_growth_global = _TokenPairInt(
            value0=fee_growth_global0,
            value1=fee_growth_global1,
        )
        self.base_position = _PositionData(
            liquidity=liquidity_base,
            tokens_owed0=tokens_owed_base0,
            tokens_owed1=tokens_owed_base1,
            fee_growth_inside0=fee_growth_inside_base0,
            fee_growth_inside1=fee_growth_inside_base1,
            tick_index_lower=tick_index_lower_base,
            fee_growth_outside_lower0=fee_growth_outside_lower_base0,
            fee_growth_outside_lower1=fee_growth_outside_lower_base1,
            tick_index_upper=tick_index_upper_base,
            fee_growth_outside_upper0=fee_growth_outside_upper_base0,
            fee_growth_outside_upper1=fee_growth_outside_upper_base1,
            decimals0=decimals0,
            decimals1=decimals1,
        )
        self.limit_position = _PositionData(
            liquidity=liquidity_limit,
            tokens_owed0=tokens_owed_limit0,
            tokens_owed1=tokens_owed_limit1,
            fee_growth_inside0=fee_growth_inside_limit0,
            fee_growth_inside1=fee_growth_inside_limit1,
            tick_index_lower=tick_index_lower_limit,
            fee_growth_outside_lower0=fee_growth_outside_lower_limit0,
            fee_growth_outside_lower1=fee_growth_outside_lower_limit1,
            tick_index_upper=tick_index_upper_limit,
            fee_growth_outside_upper0=fee_growth_outside_upper_limit0,
            fee_growth_outside_upper1=fee_growth_outside_upper_limit1,
            decimals0=decimals0,
            decimals1=decimals1,
        )
        if total_supply:
            self.total_supply = ValueWithDecimal(
                raw=total_supply, decimals=total_supply_decimals
            )

    def update_tvl(self, tvl0: int, tvl1: int, tvl_usd: int) -> None:
        self.tvl = self.tvl = _TokenPair(
            raw0=tvl0,
            raw1=tvl1,
            decimals0=self.decimals.value0,
            decimals1=self.decimals.value1,
        )
        self.tvl_usd = tvl_usd


@dataclass
class FeesDataRange:
    initial: FeesData
    latest: FeesData


@dataclass
class _FeeAmounts:
    amount: _TokenPairDecimals = field(init=False)
    amount_x128: _TokenPair = field(init=False)
    decimals: _TokenPairInt = field(init=False)
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
        self.amount_x128 = _TokenPair(
            raw0=amount0_x128,
            raw1=amount1_x128,
            decimals0=decimals0,
            decimals1=decimals1,
        )
        self.decimals = _TokenPairInt(decimals0, decimals1)
        self._adjust_values()
        self._calculate_usd(price0, price1)

    def _adjust_values(self) -> None:
        self.amount = _TokenPairDecimals(
            self.amount_x128.value0.adjusted / X128,
            self.amount_x128.value1.adjusted / X128,
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
            amount0_x128=self.fees.amount_x128.value0.raw
            + self.owed.amount_x128.value0.raw,
            amount1_x128=self.fees.amount_x128.value1.raw
            + self.owed.amount_x128.value1.raw,
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
            amount0_x128=self.base.fees.amount_x128.value0.raw
            + self.base.owed.amount_x128.value0.raw
            + self.limit.fees.amount_x128.value0.raw
            + self.limit.owed.amount_x128.value0.raw,
            amount1_x128=self.base.fees.amount_x128.value1.raw
            + self.base.owed.amount_x128.value1.raw
            + self.limit.fees.amount_x128.value1.raw
            + self.limit.owed.amount_x128.value1.raw,
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
