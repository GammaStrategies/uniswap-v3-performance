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

        fees_latest = Fees(self.data.latest, self.protocol, self.chain)
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
            if self.data.initial.total_supply.adjusted
            else 0
        )
        latest_tokens_latest_price = (
            self.data.latest.tvl_usd / self.data.latest.total_supply.adjusted
            if self.data.latest.total_supply.adjusted
            else 0
        )

        return (
            (
                (latest_tokens_latest_price - initial_tokens_initial_price)
                / initial_tokens_initial_price
            )
            if initial_tokens_initial_price
            else 0
        )

    def hold_fifty_tokens_usd(self):
        """Gain/loss from holding 50% / 50% tokens outside of vault, denominated in USD"""
        total_ini_value = (
            self.data.initial.tvl.value0.adjusted * self.data.initial.price.value0
        ) + (self.data.initial.tvl.value1.adjusted * self.data.initial.price.value1)
        # calc fifty percent total in each token
        total_token0_qtty = (
            ((total_ini_value * 0.5) / self.data.initial.price.value0)
            if self.data.initial.price.value0
            else 0
        )
        total_token1_qtty = (
            ((total_ini_value * 0.5) / self.data.initial.price.value1)
            if self.data.initial.price.value1
            else 0
        )

        initial_tokens_initial_price = (
            total_ini_value / self.data.initial.total_supply.adjusted
            if self.data.initial.total_supply.adjusted
            else 0
        )

        initial_tokens_latest_price = (
            (
                (total_token0_qtty * self.data.latest.price.value0)
                + (total_token1_qtty * self.data.latest.price.value1)
            )
            / self.data.initial.total_supply.adjusted
            if self.data.initial.total_supply.adjusted
            else 0
        )

        return (
            (
                (initial_tokens_latest_price - initial_tokens_initial_price)
                / initial_tokens_initial_price
            )
            if initial_tokens_initial_price
            else 0
        )

    def hold_initial_tokens_usd(self):
        """Gain/loss from holding initial supplied tokens outside of vault, denominated in USD"""

        initial_tokens_initial_price = (
            (
                (self.data.initial.tvl.value0.adjusted * self.data.initial.price.value0)
                + (
                    self.data.initial.tvl.value1.adjusted
                    * self.data.initial.price.value1
                )
            )
            / self.data.initial.total_supply.adjusted
            if self.data.initial.total_supply.adjusted
            else 0
        )

        initial_tokens_latest_price = (
            (
                (self.data.initial.tvl.value0.adjusted * self.data.latest.price.value0)
                + (
                    self.data.initial.tvl.value1.adjusted
                    * self.data.latest.price.value1
                )
            )
            / self.data.initial.total_supply.adjusted
            if self.data.initial.total_supply.adjusted
            else 0
        )

        return (
            (
                (initial_tokens_latest_price - initial_tokens_initial_price)
                / initial_tokens_initial_price
            )
            if initial_tokens_initial_price
            else 0
        )

    def hold_token0(self):
        """Gain/loss from holding token9 outside the vault, denominated in token usd"""

        total_ini_value = (
            self.data.initial.tvl.value0.adjusted * self.data.initial.price.value0
        ) + (self.data.initial.tvl.value1.adjusted * self.data.initial.price.value1)

        # calc token quantity
        total_token0_qtty = self.data.initial.tvl.value0.adjusted + (
            self.data.initial.tvl.value1.adjusted
            * (
                self.data.initial.price.value1 / self.data.initial.price.value0
                if self.data.initial.price.value0
                else 0
            )
        )

        initial_token0_initial_price = (
            total_ini_value / self.data.initial.total_supply.adjusted
            if self.data.initial.total_supply.adjusted
            else 0
        )

        initial_token0_latest_price = (
            (total_token0_qtty * self.data.latest.price.value0)
            / self.data.initial.total_supply.adjusted
            if self.data.initial.total_supply.adjusted
            else 0
        )

        return (
            (
                (initial_token0_latest_price - initial_token0_initial_price)
                / initial_token0_initial_price
            )
            if initial_token0_initial_price != 0
            else 0
        )

    def hold_token1(self):
        """Gain/loss from holding token1 outside the vault, denominated in token usd"""

        total_ini_value = (
            self.data.initial.tvl.value0.adjusted * self.data.initial.price.value0
        ) + (self.data.initial.tvl.value1.adjusted * self.data.initial.price.value1)

        # calc token quantity
        total_token1_qtty = self.data.initial.tvl.value1.adjusted + (
            self.data.initial.tvl.value0.adjusted
            * (
                self.data.initial.price.value0 / self.data.initial.price.value1
                if self.data.initial.price.value1
                else 0
            )
        )

        initial_token1_initial_price = (
            total_ini_value / self.data.initial.total_supply.adjusted
            if self.data.initial.total_supply.adjusted
            else 0
        )

        initial_token1_latest_price = (
            (total_token1_qtty * self.data.latest.price.value1)
            / self.data.initial.total_supply.adjusted
            if self.data.initial.total_supply.adjusted
            else 0
        )

        return (
            (
                (initial_token1_latest_price - initial_token1_initial_price)
                / initial_token1_initial_price
            )
            if initial_token1_initial_price
            else 0
        )

    def calculate(self) -> dict:
        valid_total_supply = bool(
            self.data.initial.total_supply.raw > 0
            and self.data.latest.total_supply.raw > 0
        )

        # warn over weird data
        self.check_inconsistencies()

        return {
            "id": self.data.latest.hypervisor,
            "symbol": self.data.latest.symbol,
            "ini_block": self.data.initial.block,
            "end_block": self.data.latest.block,
            "ini_timestamp": self.data.initial.timestamp,
            "end_timestamp": self.data.latest.timestamp,
            "seconds_passed": self.data.latest.timestamp - self.data.initial.timestamp,
            "lping": self.deposit_in_vault_usd() if valid_total_supply else 0,
            "hodl_deposited": self.hold_initial_tokens_usd()
            if valid_total_supply
            else 0,
            "hodl_fifty": self.hold_fifty_tokens_usd() if valid_total_supply else 0,
            "hodl_token0": self.hold_token0() if valid_total_supply else 0,
            "hodl_token1": self.hold_token1() if valid_total_supply else 0,
        }

    def check_inconsistencies(self):
        """Warn on data inconsistencies"""
        for item in [self.data.initial, self.data.latest]:
            if not item.price.value0:
                logger.warning(
                    " {}'s {} {} token 0 usd price is zero at block {}  [ hype address {}]".format(
                        self.chain,
                        self.protocol,
                        item.symbol,
                        item.block,
                        item.hypervisor,
                    )
                )
            if not item.price.value1:
                logger.warning(
                    " {}'s {} {} token 1 usd price is zero at block {}  [ hype address {}]".format(
                        self.chain,
                        self.protocol,
                        item.symbol,
                        item.block,
                        item.hypervisor,
                    )
                )


async def impermanent_divergence_all(
    protocol: Protocol,
    chain: Chain,
    days: int,
    hypervisors: list[str] | None = None,
    current_timestamp: int | None = None,
) -> dict:
    divergence_data = ImpermanentDivergenceData(protocol, chain)
    await divergence_data.init_time(days_ago=days, end_timestamp=current_timestamp)
    await divergence_data.get_data(hypervisors)

    results = {}
    for hypervisor_id, hypervisor in divergence_data.data.items():
        divergence = ImpermanentDivergence(hypervisor, protocol, chain)
        results[hypervisor_id] = divergence.calculate()

    return results
