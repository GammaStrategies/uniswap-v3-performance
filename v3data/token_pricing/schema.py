from dataclasses import dataclass, field, InitVar


@dataclass
class PricingData:
    hypervisor: str
    decimals0: int
    decimals1: int
    price0: float = field(init=False)
    price1: float = field(init=False)
    base_token_index: InitVar[int]
    price_token_in_base: InitVar[int]
    price_base_in_usd: InitVar[int]

    def __post_init__(self, base_token_index, price_token_in_base, price_base_in_usd):
        self.decimals0 = int(self.decimals0)
        self.decimals1 = int(self.decimals1)

        base_token_index = int(base_token_index)
        price_token_in_base = float(price_token_in_base)
        price_base_in_usd = float(price_base_in_usd)

        if base_token_index == 0:
            self.price0 = price_base_in_usd
            self.price1 = price_token_in_base * price_base_in_usd
        elif base_token_index == 1:
            self.price0 = price_token_in_base * price_base_in_usd
            self.price1 = price_base_in_usd
        else:
            self.price0 = 0
            self.price1 = 0
