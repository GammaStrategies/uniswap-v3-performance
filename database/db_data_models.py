from dataclasses import dataclass, field, asdict, InitVar

@dataclass
class tool_mongodb_general:

    def create_dbFilter(self)->dict:
        return {}

    def asdict(self)->dict:
        return asdict(self)

class tool_database_id:
    id: str = ""

    def __post_init__(self):
        if self.id == "":
            self.id = self.create_id()

    def create_id(self)->str:
        return ""


@dataclass
class token(tool_mongodb_general,tool_database_id):
    address:str
    symbol: int
    chain: str
    position: int

    def create_id(self)->str:
        return f"{self.chain}_{self.address}"

    def _fill_fromDict(self, data: dict):
        """fill class fields from dictionary

        Args:
            data (dict): _description_

        Returns:
            _type_: _description_
        """
        self.id_ = data["id"]
        self.symbol = data["symbol"]
        self.chain = data["chain"]
        self.position = data["position"]


@dataclass
class pool(tool_mongodb_general,tool_database_id):
    address:str
    chain: str
    fee: int
    tokens: list[token]

    def create_id(self)->str:
        return f"{self.chain}_{self.address}"

    def _fill_fromDict(self, data: dict):
        """create class from dictionary

        Args:
            data (dict): _description_

        Returns:
            _type_: _description_
        """
        self.address = data["feeApr"]
        self.chain = data["feeApy"]
        self.fee = data["hasOutlier"]
        self.tokens = []


@dataclass
class hypervisor_fees(tool_mongodb_general):
    feeApr: float = 0
    feeApy: float = 0
    hasOutlier: bool = 0

    def _fill_fromDict(self, data: dict):
        """create class from dictionary

        Args:
            data (dict): _description_

        Returns:
            _type_: _description_
        """
        self.feeApr = data["feeApr"]
        self.feeApy = data["feeApy"]
        self.hasOutlier = data["hasOutlier"]


@dataclass
class hypervisor_impermanent(tool_mongodb_general):
    vs_hodl_usd: float = 0
    vs_hodl_deposited: float = 0
    vs_hodl_token0: float = 0
    vs_hodl_token1: float = 0


    def _fill_fromDict(self, data: dict):
        """create class from dictionary

        Args:
            data (dict): _description_

        Returns:
            _type_: _description_
        """
        self.vs_hodl_usd = data["vs_hodl_usd"]
        self.vs_hodl_deposited = data["vs_hodl_deposited"]
        self.vs_hodl_token0 = data["vs_hodl_token0"]
        self.vs_hodl_token1 = data["vs_hodl_token1"]


@dataclass
class hypervisor_return(tool_mongodb_general,tool_database_id):
    chain: str
    period: str
    address: str
    symbol: str
    block: int
    timestamp: int
    fees: hypervisor_fees = None
    impermanent: hypervisor_impermanent = None

    def create_id(self)->str:
        return f"{self.chain}_{self.address}_{self.block}_{self.period}"


@dataclass
class hypervisor_static(tool_mongodb_general,tool_database_id):
    chain: str
    address: str
    symbol: str
    protocol: int
    created: int
    pool: pool
 
    def create_id(self)->str:
        return f"{self.chain}_{self.address}"




