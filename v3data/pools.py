from v3data.data import UniV3Data


def pools_from_symbol(symbol):
    client = UniV3Data()
    token_list = client.get_token_list()
    token_addresses = token_list.get(symbol.upper())
    pool_list = client.get_pools_by_tokens(token_addresses)

    pools = [
        {
            "token0Address": pool['token0']['id'],
            "token1Address": pool['token1']['id'],
            "poolAddress": pool['id'],
            'symbol': f"{pool['token0']['symbol']}-{pool['token1']['symbol']}",
            'feeTier': pool['feeTier'],
            'volumeUSD': pool['volumeUSD']
        } for pool in pool_list
    ]

    return pools
