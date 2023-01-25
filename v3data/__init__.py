import httpx
from web3 import Web3
import logging

from v3data.config import (
    ALCHEMY_URLS,
    VISOR_SUBGRAPH_URL,
    GAMMA_SUBGRAPH_URLS,
    UNI_V2_SUBGRAPH_URL,
    DEX_SUBGRAPH_URLS,
    DEX_FEEGROWTH_SUBGRAPH_URLS,
    ETH_BLOCKS_SUBGRAPH_URL,
    THEGRAPH_INDEX_NODE_URL,
    XGAMMA_SUBGRAPH_URL,
)

from v3data import abi

logger = logging.getLogger(__name__)
async_client = httpx.AsyncClient(timeout=180)


class SubgraphClient:
    def __init__(self, url: str, chain: str = "mainnet"):
        self._url = url
        self.chain = chain

    async def query(self, query: str, variables=None) -> dict:
        """Make graphql query to subgraph"""
        if variables:
            params = {"query": query, "variables": variables}
        else:
            params = {"query": query}
        # TODO: error handling -> connection, result and others   httpcore.RemoteProtocolError
        #                                                         ssl.SSLError:   [SSL: SSLV3_ALERT_HANDSHAKE_FAILURE] sslv3 alert handshake failure
        #
        response = await async_client.post(self._url, json=params)

        if response.status_code == 200:
            if parsed_response := response.json():
                return parsed_response
            else:
                # handle bad gql query
                logger.error(
                    " Unexpected error while converting response to json. resp.text: {} ".format(
                        response.text,
                    )
                )
        else:
            # handle bad status code
            # Can expand this to handle specific codes once we have specific examples
            logger.error(
                " Unexpected response code {} received  resp.text: {} ".format(
                    response.status_code,
                    response.text,
                )
            )
        # error return
        return {}

    async def paginate_query(self, query, paginate_variable, variables={}):

        # if not variables:
        #     variables = {}

        if f"{paginate_variable}_gt" not in query:
            raise ValueError("Paginate variable missing in query")

        variables["orderBy"] = paginate_variable
        variables["orderDirection"] = "asc"

        all_data = []
        has_data = True
        params = {"query": query, "variables": variables}
        while has_data:
            response = await async_client.post(self._url, json=params)
            data = next(iter(response.json()["data"].values()))
            has_data = bool(data)
            if has_data:
                all_data += data
                params["variables"]["paginate"] = data[-1][paginate_variable]

        return all_data


class VisorClient(SubgraphClient):
    def __init__(self):
        super().__init__(VISOR_SUBGRAPH_URL)

    def hypervisors_tvl(self):
        query_tvl = """
        {
            uniswapV3Hypervisors(first:1000) {
                id
                pool{
                    id
                    token0{
                        decimals
                    }
                    token1{
                        decimals
                    }
                }
                tvl0
                tvl1
                tvlUSD
                totalSupply
            }
        }
        """
        tvls = self.query(query_tvl)["data"]["uniswapV3Hypervisors"]

        return {
            hypervisor["id"]: {
                "tvl0": hypervisor["tvl0"],
                "tvl1": hypervisor["tvl1"],
                "tvlUSD": hypervisor["tvlUSD"],
                "tvl0Decimal": int(hypervisor["tvl0"])
                / 10 ** int(hypervisor["pool"]["token0"]["decimals"]),
                "tvl1Decimal": int(hypervisor["tvl1"])
                / 10 ** int(hypervisor["pool"]["token1"]["decimals"]),
                "totalSupply": int(hypervisor["totalSupply"]),
            }
            for hypervisor in tvls
        }


class GammaClient(SubgraphClient):
    def __init__(self, protocol: str, chain: str):
        super().__init__(GAMMA_SUBGRAPH_URLS[protocol][chain], chain)


class UniswapV2Client(SubgraphClient):
    def __init__(self):
        super().__init__(UNI_V2_SUBGRAPH_URL)


class UniswapV3Client(SubgraphClient):
    def __init__(self, protocol: str, chain: str):
        super().__init__(DEX_SUBGRAPH_URLS[protocol][chain], chain)


class DexFeeGrowthClient(SubgraphClient):
    def __init__(self, protocol: str, chain: str):
        super().__init__(DEX_FEEGROWTH_SUBGRAPH_URLS[protocol][chain], chain)


class EthBlocksClient(SubgraphClient):
    def __init__(self):
        super().__init__(ETH_BLOCKS_SUBGRAPH_URL)

    def block_from_timestamp(self, timestamp):
        """Get closest from timestamp"""
        ten_minutes_in_seconds = 600
        query = """
        query blockQuery($startTime: Int!, $endTime:Int!){
          blocks(first: 1, orderBy: timestamp, orderDirection: asc,
                 where: {timestamp_gt: $startTime, timestamp_lt: $endTime}) {
            id
            number
            timestamp
          }
        }
        """

        variables = {
            "startTime": timestamp,
            "endTime": timestamp + ten_minutes_in_seconds,
        }

        return int(self.query(query, variables)["data"]["blocks"][0]["number"])


class IndexNodeClient(SubgraphClient):
    def __init__(self, protocol: str, chain: str):
        super().__init__(THEGRAPH_INDEX_NODE_URL)
        self.url = GAMMA_SUBGRAPH_URLS[protocol][chain]
        self.set_subgraph_name()

    def set_subgraph_name(self):
        split_subgraph_url = self.url.split("/")
        if not split_subgraph_url[-1]:
            split_subgraph_url.pop(-1)
        self.subgraph_name = f"{split_subgraph_url[-2]}/{split_subgraph_url[-1]}"

    async def status(self):
        query = f"""
        {{ 
            indexingStatusForCurrentVersion(
                subgraphName: "{self.subgraph_name}"
            ){{
                chains{{
                    latestBlock {{ hash number }}
                }}
            }}
        }}
        """

        response = await self.query(query)
        latestBlock = int(
            response["data"]["indexingStatusForCurrentVersion"]["chains"][0][
                "latestBlock"
            ]["number"]
        )

        return {"url": self.url, "latestBlock": latestBlock}


class XgammaClient(SubgraphClient):
    def __init__(self):
        super().__init__(XGAMMA_SUBGRAPH_URL)


class CoingeckoClient:
    def __init__(self):
        self.base = "https://api.coingecko.com/api/v3/"

    async def get_price(self, ids, vs_currencies):
        endpoint = f"{self.base}/simple/price"

        params = {"ids": ids, "vs_currencies": vs_currencies}

        response = await async_client.get(endpoint, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return {"gamma-strategies": {"usd": 0.623285, "eth": 0.00016391}}


class LlamaClient:
    def __init__(self, chain):
        self.base = "https://coins.llama.fi/"
        self.chain = self._translate_chain_name(chain)

    def _translate_chain_name(self, chain):
        mapping = {"mainnet": "ethereum"}
        return mapping.get(chain, chain)

    async def block_from_timestamp(self, timestamp):
        endpoint = f"{self.base}/block/{self.chain}/{timestamp}"

        response = await async_client.get(endpoint)
        if response.status_code == 200:
            return response.json()["height"]

        return None


class MasterChefContract:
    def __init__(self, address, chain: str):
        w3 = Web3(Web3.HTTPProvider(ALCHEMY_URLS[chain]))
        self.contract = w3.eth.contract(
            address=Web3.toChecksumAddress(address), abi=abi.MASTERCHEF_ABI
        )

    def pending_rewards(self, pool_id, user_address):
        return self.contract.functions.pendingSushi(
            pool_id, Web3.toChecksumAddress(user_address)
        )


class RewarderContract:
    def __init__(self, address, chain: str):
        w3 = Web3(Web3.HTTPProvider(ALCHEMY_URLS[chain]))
        self.contract = w3.eth.contract(
            address=Web3.toChecksumAddress(address), abi=abi.REWARDER_ABI
        )

    def pending_rewards(self, pool_id, user_address):
        return self.contract.functions.pendingToken(
            pool_id, Web3.toChecksumAddress(user_address)
        )
