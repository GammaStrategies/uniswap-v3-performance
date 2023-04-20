from dataclasses import dataclass, field


@dataclass
class ValueWithDecimal:
    raw: int
    adjusted: float = field(init=False)
    decimals: int

    def __post_init__(self):
        self.raw = int(self.raw)
        self.decimals = int(self.decimals)
        self.adjusted = self.raw / 10**self.decimals