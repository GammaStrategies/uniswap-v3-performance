import logging
from v3data.utils import sub_in_256
from v3data.hype_fees.schema import (
    FeesData,
    UncollectedFees,
    UncollectedFeesUsd,
    _TokenPair,
    _TokenPairDecimals,
)
from v3data.hype_fees.data import FeeGrowthData
from v3data.constants import X128

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

    def fee_usd(self):

        uncollected_fees = self._calc_all_fees()

        return UncollectedFeesUsd(
            base=_TokenPairDecimals(
                uncollected_fees.base.value0
                * self.data.price.value0
                / 10 ** self.data.decimals.value0 / X128,
                uncollected_fees.base.value1
                * self.data.price.value1
                / 10 ** self.data.decimals.value1 / X128,
            ),
            limit=_TokenPairDecimals(
                uncollected_fees.limit.value0
                * self.data.price.value0
                / 10 ** self.data.decimals.value0 / X128,
                uncollected_fees.limit.value1
                * self.data.price.value1
                / 10 ** self.data.decimals.value1 / X128,
            ),
        )

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

        return UncollectedFees(base=base_fees_x128, limit=limit_fees_x128)

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


async def fees_usd_all(protocol: str, chain: str):
    fees_data = FeeGrowthData(protocol, chain)
    await fees_data.get_data()

    results = {}
    for hypervisor_id, fees_data in fees_data.data.items():
        fees = Fees(fees_data, protocol, chain)
        results[hypervisor_id] = fees.fee_usd()

    return results
