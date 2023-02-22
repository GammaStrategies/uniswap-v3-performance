import logging
from v3data.utils import sub_in_256
from v3data.hype_fees.schema import (
    FeesData,
    UncollectedFees,
    _TokenPair,
)
from v3data.hype_fees.data import FeeGrowthData

from enum import Enum

logger = logging.getLogger(__name__)


class PositionType(Enum):
    BASE = "BASE"
    LIMIT = "LIMIT"


class Fees:
    def __init__(self, data: FeesData, protocol: str, chain: str):
        self.data = data
        self.protocol = protocol
        self.chain = chain

    def fee_amounts(self):
        return self._calc_all_fees()

    def _calc_all_fees(self) -> tuple[_TokenPair, _TokenPair]:
        try:
            base_fees_x128 = self._calc_position_fees(PositionType.BASE)
        except (IndexError, TypeError):
            base_fees_x128 = _TokenPair(0, 0)
            logger.warning(
                f"Base fees set to 0, missing data for hype: {self.data.hypervisor}, "
                f"ticks: ({self.data.base_position.tick_lower.tick_index}, "
                f"{self.data.base_position.tick_upper.tick_index})"
            )

        try:
            limit_fees_x128 = self._calc_position_fees(PositionType.LIMIT)
        except (IndexError, TypeError):
            limit_fees_x128 = _TokenPair(0, 0)
            logger.warning(
                f"Limit fees set to 0, missing data for hype: {self.data.hypervisor}, "
                f"ticks: ({self.data.limit_position.tick_lower.tick_index}, "
                f"{self.data.limit_position.tick_lower.tick_index})"
            )

        return UncollectedFees(
            base_fees0_x128=base_fees_x128.value0,
            base_fees1_x128=base_fees_x128.value1,
            base_owed0_x128=self.data.base_position.tokens_owed.value0,
            base_owed1_x128=self.data.base_position.tokens_owed.value1,
            limit_fees0_x128=limit_fees_x128.value0,
            limit_fees1_x128=limit_fees_x128.value1,
            limit_owed0_x128=self.data.limit_position.tokens_owed.value0,
            limit_owed1_x128=self.data.limit_position.tokens_owed.value1,
            decimals0=self.data.decimals.value0,
            decimals1=self.data.decimals.value1,
            price0=self.data.price.value0,
            price1=self.data.price.value1,
        )

    def _calc_position_fees(self, position_type: PositionType) -> _TokenPair:

        if position_type == PositionType.BASE:
            position = self.data.base_position
        elif position_type == PositionType.LIMIT:
            position = self.data.limit_position

        if self.data.currentTick >= position.tick_lower.tick_index:
            fee_growth_below_pos_0 = position.tick_lower.fee_growth_outside.value0
            fee_growth_below_pos_1 = position.tick_lower.fee_growth_outside.value1
        else:
            fee_growth_below_pos_0 = sub_in_256(
                self.data.fee_growth_global.value0,
                position.tick_lower.fee_growth_outside.value0,
            )
            fee_growth_below_pos_1 = sub_in_256(
                self.data.fee_growth_global.value1,
                position.tick_lower.fee_growth_outside.value1,
            )

        if self.data.currentTick >= position.tick_upper.tick_index:
            fee_growth_above_pos_0 = sub_in_256(
                self.data.fee_growth_global.value0,
                position.tick_upper.fee_growth_outside.value0,
            )
            fee_growth_above_pos_1 = sub_in_256(
                self.data.fee_growth_global.value1,
                position.tick_upper.fee_growth_outside.value1,
            )
        else:
            fee_growth_above_pos_0 = position.tick_upper.fee_growth_outside.value0
            fee_growth_above_pos_1 = position.tick_upper.fee_growth_outside.value1

        fees_accum_now_0 = sub_in_256(
            sub_in_256(self.data.fee_growth_global.value0, fee_growth_below_pos_0),
            fee_growth_above_pos_0,
        )
        fees_accum_now_1 = sub_in_256(
            sub_in_256(self.data.fee_growth_global.value1, fee_growth_below_pos_1),
            fee_growth_above_pos_1,
        )

        uncollected_fees_0 = position.liquidity * (
            sub_in_256(fees_accum_now_0, position.fee_growth_inside.value0)
        )

        uncollected_fees_1 = position.liquidity * (
            sub_in_256(fees_accum_now_1, position.fee_growth_inside.value1)
        )

        return _TokenPair(value0=uncollected_fees_0, value1=uncollected_fees_1)


async def fees_all(protocol: str, chain: str) -> dict[str, UncollectedFees]:
    fees_data = FeeGrowthData(protocol, chain)
    await fees_data.get_data()

    results = {}
    for hypervisor_id, fees_data in fees_data.data.items():
        fees = Fees(fees_data, protocol, chain)
        fee_amounts = fees.fee_amounts()

        results[hypervisor_id] = {
            "symbol": fees_data.symbol,
            "baseFees0": fee_amounts.base.fees.amount.value0,
            "baseFees1": fee_amounts.base.fees.amount.value1,
            "baseTokensOwed0": fee_amounts.base.owed.amount.value0,
            "baseTokensOwed1": fee_amounts.base.owed.amount.value1,
            "limitFees0": fee_amounts.limit.fees.amount.value0,
            "limitFees1": fee_amounts.limit.fees.amount.value1,
            "limitTokensOwed0": fee_amounts.limit.owed.amount.value0,
            "limitTokensOwed1": fee_amounts.limit.owed.amount.value1,
            "baseFees0USD": fee_amounts.base.fees.usd.value0,
            "baseFees1USD": fee_amounts.base.fees.usd.value1,
            "baseTokensOwed0USD": fee_amounts.base.owed.usd.value0,
            "baseTokensOwed1USD": fee_amounts.base.owed.usd.value1,
            "limitFees0USD": fee_amounts.limit.fees.usd.value0,
            "limitFees1USD": fee_amounts.limit.fees.usd.value1,
            "limitTokensOwed0USD": fee_amounts.limit.owed.usd.value0,
            "limitTokensOwed1USD": fee_amounts.limit.owed.usd.value1,
            "totalFees0": fee_amounts.total.amount.value0,
            "totalFees1": fee_amounts.total.amount.value1,
            "totalFeesUSD": fee_amounts.total.usd.value0,
        }

    return results
