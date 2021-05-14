from v3data.data import UniV3Data

def pools_from_symbol(symbol):
    client = UniV3Data()
    token_list = client.get_token_list()
    token_addresses = token_list.get(symbol.upper())
    whitelist = client.get_whitelist_pools(token_addresses)

    pools = []
    for token in whitelist:
        for pool in token['whitelistPools']:
            pools.append(
                {
                    "tokenAddress": token['id'],
                    "poolAddress": pool['id'],
                    'feeTier': pool['feeTier'],
                    'symbol': f"{pool['token0']['symbol']}-{pool['token1']['symbol']}"
                }
            )

    return pools