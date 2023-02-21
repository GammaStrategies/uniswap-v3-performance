from v3data import IndexNodeClient


async def subgraph_status(protocol: str, chain: str):
    client = IndexNodeClient(protocol, chain)
    return await client.status()
