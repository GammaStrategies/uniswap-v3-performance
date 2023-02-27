import logging

from v3data.hype_fees.data import ImpermanentDivergenceData
from v3data.hype_fees.fees import Fees
from v3data.hype_fees.schema import FeesDataRange
from v3data.constants import X128
from v3data.enums import Chain, Protocol

logger = logging.getLogger(__name__)


class ImpermanentDivergence:
    def __init__(self, data: FeesDataRange, protocol: Protocol, chain: Chain):
        self.protocol = protocol
        self.chain = chain
        self.data = data
        self._update_tvl_with_fees()

    def _update_tvl_with_fees(self) -> None:
        fees_initial = Fees(self.data.initial, self.protocol, self.chain)
        fees_amounts_initial = fees_initial.fee_amounts()

        self.data.initial.update_tvl(
            self.data.initial.tvl.value0.raw
            + (fees_amounts_initial.total.amount_x128.value0.raw // X128),
            self.data.initial.tvl.value1.raw
            + (fees_amounts_initial.total.amount_x128.value1.raw // X128),
            self.data.initial.tvl_usd
            + fees_amounts_initial.total.usd.value0
            + fees_amounts_initial.total.usd.value1,
        )

        fees_latest = Fees(self.data.initial, self.protocol, self.chain)
        fees_amounts_latest = fees_latest.fee_amounts()

        self.data.latest.update_tvl(
            self.data.latest.tvl.value0.raw
            + (fees_amounts_latest.total.amount_x128.value0.raw // X128),
            self.data.latest.tvl.value1.raw
            + (fees_amounts_latest.total.amount_x128.value1.raw // X128),
            self.data.latest.tvl_usd
            + fees_amounts_latest.total.usd.value0
            + fees_amounts_latest.total.usd.value1,
        )

    def deposit_in_vault_usd(self):
        """Gain/loss from staying in vault, denominated in USD"""
        initial_tokens_initial_price = (
            self.data.initial.tvl_usd / self.data.initial.total_supply.adjusted
        )
        latest_tokens_latest_price = (
            self.data.latest.tvl_usd / self.data.latest.total_supply.adjusted
        )

        return (
            (
                (latest_tokens_latest_price - initial_tokens_initial_price)
                / initial_tokens_initial_price
            )
            if initial_tokens_initial_price != 0
            else 0
        )

    def hold_initial_tokens_usd(self):
        """Gain/loss from holding initial tokens outside of vault, denominated in USD"""
        initial_tokens_latest_price = (
            (self.data.initial.tvl.value0.adjusted * self.data.latest.price.value0)
            + (self.data.initial.tvl.value1.adjusted * self.data.latest.price.value1)
        ) / self.data.initial.total_supply.adjusted

        latest_tokens_latest_price = (
            self.data.latest.tvl_usd / self.data.latest.total_supply.adjusted
        )

        return (
            (
                (latest_tokens_latest_price - initial_tokens_latest_price)
                / initial_tokens_latest_price
            )
            if initial_tokens_latest_price != 0
            else 0
        )

    def deposit_in_vault_token0(self):
        """Gain/loss from depositing in vault, denominated in token 0"""
        initial_tokens_initial_price = (
            self.data.initial.tvl.value0.adjusted
            + (
                self.data.initial.tvl.value1.adjusted
                * (
                    self.data.initial.price.value1 / self.data.initial.price.value0
                    if self.data.initial.price.value0 > 0
                    else 0
                )
            )
        ) / self.data.initial.total_supply.adjusted

        latest_tokens_latest_price = (
            self.data.latest.tvl.value0.adjusted
            + (
                self.data.latest.tvl.value1.adjusted
                * (
                    self.data.latest.price.value1 / self.data.latest.price.value0
                    if self.data.latest.price.value0 > 0
                    else 0
                )
            )
        ) / self.data.latest.total_supply.adjusted

        return (
            (
                (latest_tokens_latest_price - initial_tokens_initial_price)
                / initial_tokens_initial_price
            )
            if initial_tokens_initial_price != 0
            else 0
        )

    def deposit_in_vault_token1(self):
        """Gain/loss from depositing in vault, denominated in token 1"""
        initial_tokens_initial_price = (
            self.data.initial.tvl.value1.adjusted
            + (
                self.data.initial.tvl.value0.adjusted
                * (
                    self.data.initial.price.value0 / self.data.initial.price.value1
                    if self.data.initial.price.value1 > 0
                    else 0
                )
            )
        ) / self.data.initial.total_supply.adjusted

        latest_tokens_latest_price = (
            self.data.latest.tvl.value1.adjusted
            + (
                self.data.latest.tvl.value0.adjusted
                * (
                    self.data.latest.price.value0 / self.data.latest.price.value1
                    if self.data.latest.price.value1 > 0
                    else 0
                )
            )
        ) / self.data.latest.total_supply.adjusted

        return (
            (
                (latest_tokens_latest_price - initial_tokens_initial_price)
                / initial_tokens_initial_price
            )
            if initial_tokens_initial_price != 0
            else 0
        )

    def calculate(self):
        valid_total_supply = bool(
            self.data.initial.total_supply.raw > 0 and self.data.latest.total_supply.raw > 0
        )

        return {
            "id": self.data.latest.hypervisor,
            "symbol": self.data.latest.symbol,
            "blocks_passed": self.data.latest.block - self.data.initial.block,
            "seconds_passed": self.data.latest.timestamp - self.data.initial.timestamp,
            "vs_hodl_usd": self.deposit_in_vault_usd() if valid_total_supply else 0,
            "vs_hodl_deposited": self.hold_initial_tokens_usd() if valid_total_supply else 0,
            "vs_hodl_token0": self.deposit_in_vault_token0() if valid_total_supply else 0,
            "vs_hodl_token1": self.deposit_in_vault_token1() if valid_total_supply else 0,
        }


async def impermanent_divergence_all(protocol: Protocol, chain: Chain, days: int) -> dict:
    divergence_data = ImpermanentDivergenceData(days, protocol, chain)
    await divergence_data.get_data()

    results = {}
    for hypervisor_id, hypervisor in divergence_data.data.items():
        divergence = ImpermanentDivergence(hypervisor, protocol, chain)
        results[hypervisor_id] = divergence.calculate()

    return results
