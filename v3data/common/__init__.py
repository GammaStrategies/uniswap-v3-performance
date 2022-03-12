from v3data import IndexNodeClient


async def subgraph_status(chain: str):
    client = IndexNodeClient(chain)
    return await client.status()