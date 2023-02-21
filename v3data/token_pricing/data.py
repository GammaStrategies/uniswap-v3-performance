from v3data import GammaClient

from v3data.token_pricing.schema import PricingData


class HypervisorPricingData:
    def __init__(self, protocol: str, chain: str) -> None:
        self.data: {}
        self.protocol = protocol
        self.chain = chain
        self.gamma_client = GammaClient(protocol, chain)

    async def get_data(self) -> None:
        self.data = self._transform_data(await self._query_data())

    async def _query_data(self) -> dict:
        query = """
        {
            uniswapV3Hypervisors {
                id
                pool {
                    token0 { decimals }
                    token1 { decimals }
                }
                conversion {
                    baseTokenIndex
                    priceTokenInBase
                    priceBaseInUSD
                }
            }
        }
        """

        response = await self.gamma_client.query(query)

        return response["data"]

    def _transform_data(self, query_data) -> dict[str, PricingData]:
        return {
            hypervisor["id"]: PricingData(
                hypervisor=hypervisor["id"],
                decimals0=hypervisor["pool"]["token0"]["decimals"],
                decimals1=hypervisor["pool"]["token1"]["decimals"],
                base_token_index=hypervisor["conversion"]["baseTokenIndex"],
                price_token_in_base=hypervisor["conversion"]["priceTokenInBase"],
                price_base_in_usd=hypervisor["conversion"]["priceBaseInUSD"],
            )
            for hypervisor in query_data["uniswapV3Hypervisors"]
        }
