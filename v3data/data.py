import asyncio
import datetime

import numpy as np
import pandas as pd
import requests
from gql.dsl import DSLQuery
from httpx import HTTPStatusError

from v3data import LlamaClient
from v3data import SubgraphClient as SubgraphClientOld
from v3data.config import DEX_SUBGRAPH_URLS, TOKEN_LIST_URL
from v3data.constants import DAY_SECONDS
from v3data.enums import Chain, Protocol
from v3data.hype_fees.schema import Time
from v3data.subgraphs import SubgraphClient
from v3data.utils import (
    estimate_block_from_timestamp_diff,
    sqrtPriceX96_to_priceDecimal,
)


class BlockRange:
    """Manage time ranges"""

    def __init__(
        self,
        chain: Chain,
        subgraph_client: SubgraphClient | None = None,
    ) -> None:
        self.chain = chain
        self.initial: Time | None = None
        self.end: Time | None = None
        if subgraph_client:
            self._subgraph_client = subgraph_client
        self._llama_client = LlamaClient(chain)

    async def set_end(self, timestamp: int | None = None) -> None:
        """Set end time and block"""
        if timestamp:
            self.end = await self._get_time_from_timestamp(timestamp)
        else:
            self.end = await self._query_current_time()

    async def set_initial_with_timestamp(self, timestamp: int) -> None:
        """Set initial timestamp and block by providing the timestamp"""
        self.initial = await self._get_time_from_timestamp(timestamp)

    async def set_initial_with_days_ago(self, days_ago: int) -> None:
        """Set initial timestamp and block using days before current time"""
        timestamp_start = self.end.timestamp - (days_ago * DAY_SECONDS)
        try:
            response = await self._llama_client.block_from_timestamp(
                timestamp_start, True
            )
            self.initial = Time(
                block=response["height"], timestamp=response["timestamp"]
            )
        except HTTPStatusError:
            # Estimate start time if not found
            self.initial = Time(
                block=estimate_block_from_timestamp_diff(
                    self.chain,
                    self.end.block,
                    self.end.timestamp,
                    timestamp_start,
                ),
                timestamp=timestamp_start,
            )

    async def _get_time_from_timestamp(self, timestamp: int) -> Time:
        response = await self._llama_client.block_from_timestamp(timestamp, True)
        return Time(block=response["height"], timestamp=response["timestamp"])

    async def _query_current_time(self) -> Time:
        query = DSLQuery(
            self._subgraph_client.data_schema.Query._meta.select(
                self._subgraph_client.meta_fields_fragment()
            )
        )

        response = await self._subgraph_client.execute(query)

        return Time(
            block=response["_meta"]["block"]["number"],
            timestamp=response["_meta"]["block"]["timestamp"],
        )


class UniV3Data(SubgraphClientOld):
    def __init__(self, protocol: Protocol, chain: Chain):
        super().__init__(DEX_SUBGRAPH_URLS[protocol][chain])

    def get_token_list(self):
        response = requests.get(TOKEN_LIST_URL)
        token_list = response.json()["tokens"]

        token_addresses = {}
        for token in token_list:
            symbol = token["symbol"]
            if token_addresses.get(symbol):
                token_addresses[symbol].append(token["address"])
            else:
                token_addresses[symbol] = [token["address"]]

        return token_addresses

    async def get_pools_by_tokens(self, token_addresses):
        query0 = """
        query whitelistPools($ids: [String!]!)
        {
          pools(
            first: 1000
            where: {
              token0_in: $ids
            }
            orderBy: volumeUSD
            orderDirection: desc
          ) {
            id
            feeTier
            volumeUSD
            token0{
              id
              symbol
            }
            token1{
              id
              symbol
            }
          }
        }
        """
        query1 = """
        query whitelistPools($ids: [String!]!)
        {
          pools(
            first: 1000
            where: {
              token1_in: $ids
            }
            orderBy: volumeUSD
            orderDirection: desc
          ) {
            id
            feeTier
            volumeUSD
            token0{
              id
              symbol
            }
            token1{
              id
              symbol
            }
          }
        }
        """
        variables = {"ids": [address.lower() for address in token_addresses]}

        pool0_response, pool1_response = await asyncio.gather(
            self.query(query0, variables), self.query(query1, variables)
        )

        pool0 = pool0_response["data"]["pools"]
        pool1 = pool1_response["data"]["pools"]

        return pool0 + pool1

    async def get_pool(self, pool_address):
        """Get metadata for pool"""
        query = """
        query poolData($id: String!) {
          pool(
            id: $id
          ){
            id
            token0{
              id
              symbol
              decimals
            }
            token1{
              id
              symbol
              decimals
            }
          }
        }
        """

        variables = {"id": pool_address.lower()}

        response = await self.query(query, variables)
        return response["data"]["pool"]

    async def get_historical_pool_prices(self, pool_address, time_delta=None):
        pool_address = pool_address.lower()
        query = """
            query poolPrices($id: String!, $timestamp_start: Int!){
                pool(
                    id: $id
                ){
                    swaps(
                        first: 1000
                        orderBy: timestamp
                        orderDirection: asc
                        where: { timestamp_gte: $timestamp_start }
                    ){
                        id
                        timestamp
                        sqrtPriceX96
                    }
                }
            }
        """

        if time_delta:
            timestamp_start = int(
                (datetime.datetime.utcnow() - time_delta)
                .replace(tzinfo=datetime.timezone.utc)
                .timestamp()
            )
        else:
            timestamp_start = 0

        variables = {"id": pool_address, "timestamp_start": timestamp_start}
        has_data = True
        all_swaps = []
        while has_data:
            response = await self.query(query, variables)
            swaps = response["data"]["pool"]["swaps"]

            all_swaps.extend(swaps)
            timestamps = set([int(swap["timestamp"]) for swap in swaps])
            variables["timestamp_start"] = max(timestamps)

            if len(swaps) < 1000:
                has_data = False

        pool = await self.get_pool(pool_address)

        df_swaps = pd.DataFrame(all_swaps, dtype=np.float64)
        df_swaps.timestamp = df_swaps.timestamp.astype(np.int64)
        df_swaps.drop_duplicates(inplace=True)
        df_swaps["priceDecimal"] = df_swaps.sqrtPriceX96.apply(
            sqrtPriceX96_to_priceDecimal,
            args=(int(pool["token0"]["decimals"]), int(pool["token1"]["decimals"])),
        )
        data = df_swaps.to_dict("records")

        return data
