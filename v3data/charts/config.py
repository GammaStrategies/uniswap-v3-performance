BASE_POOLS_CONFIG = {
    "mainnet": {
        # OHM 
        "0x64aa3364f17a4d01c6f1751fd97c2bd3d7e7f1d5": {
            "priority": 1,
            "v3": {
                "pool": "0x584ec2562b937c4ac0452184d8d83346382b5d3a",
                "usdc_token_index": 3,
            }
        },
        # OCEAN 
        "0x967da4048cd07ab37855c090aaf366e4ce1b9f48": {
            "priority": 2,
            "v3": {
                "pool": "0x283e2e83b7f3e297c4b7c02114ab0196b001a109",
                "usdc_token_index": 3,
            }
        },
        # WBTC
        "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": {
            "priority": 3,
            "v2": {
                "pool": "0x004375dff511095cc5a197a54140a24efef3a416",
                "usdc_token_index": 1,
            },
            "v3": {
                "pool": "0x99ac8ca7087fa4a2a1fb6357269965a2014abc35",
                "usdc_token_index": 1,
            }
        },
        # WETH
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": {
            "priority": 4,
            "v2": {
                "pool": "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc",
                "usdc_token_index": 0,
            },
            "v3": {
                "pool": "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8",
                "usdc_token_index": 0,
            }
        },
        # DAI
        "0x6b175474e89094c44da98b954eedeac495271d0f": {
            "priority": 5,
            "v2": {
                "pool": "0xae461ca67b15dc8dc81ce7615e0320da1a9ab8d5",
                "usdc_token_index": 1,
            },
            "v3": {
                "pool": "0x5777d92f208679db4b9778590fa3cab3ac9e2168",
                "usdc_token_index": 1,
            }
        },
        # USDT
        "0xdac17f958d2ee523a2206206994597c13d831ec7": {
            "priority": 6,
            "v2": {
                "pool": "0x3041cbd36888becc7bbcbc0045e3b1f144466f5f",
                "usdc_token_index": 0,
            },
            "v3": {
                "pool": "0x3416cf6c708da44db2624d63ea0aaef7113527c6",
                "usdc_token_index": 0,
            }
        },
        # USDC
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {
            "priority": 7,
            "v2": {
                "pool": "0x3041cbd36888becc7bbcbc0045e3b1f144466f5f",  # Use a dummy pool
                "usdc_token_index": None,
            },
            "v3": {
                "pool": "0x3416cf6c708da44db2624d63ea0aaef7113527c6",
                "usdc_token_index": 0,
            }
        },
    },
    "polygon": {
        # WBTC
        "0x1bfd67037b42cf73acf2047067bd4f2c47d9bfd6": {
            "priority": 1,
            "v3": {
                "pool": "0x847b64f9d3a95e977d157866447a5c0a5dfa0ee5",
                "usdc_token_index": 1,
            }
        },
        # WETH
        "0x7ceb23fd6bc0add59e62ac25578270cff1b9f619": {
            "priority": 2,
            "v3": {
                "pool": "0x45dda9cb7c25131df268515131f647d726f50608",
                "usdc_token_index": 0,
            }
        },
        # DAI
        "0x8f3cf7ad23cd3cadbd9735aff958023239c6a063": {
            "priority": 3,
            "v3": {
                "pool": "0x5645dcb64c059aa11212707fbf4e7f984440a8cf",
                "usdc_token_index": 0,
            }
        },
        # USDT
        "0xc2132d05d31c914a87c6611c10748aeb04b58e8f": {
            "priority": 4,
            "v3": {
                "pool": "0xdac8a8e6dbf8c690ec6815e0ff03491b2770255d",
                "usdc_token_index": 1,
            }
        },
        # USDC
        "0x2791bca1f2de4661ed88a30c99a7a9449aa84174": {
            "priority": 5,
            "v3": {
                "pool": "0xdac8a8e6dbf8c690ec6815e0ff03491b2770255d",  # dummy
                "usdc_token_index": 1,
            }
        },
    },
    "optimism": {
        # WBTC
        "0x68f180fcce6836688e9084f035309e29bf0a2095": {
            "priority": 1,
            "v3": {
                "pool": "0x6168ec836d0b1f0c37381ec7ed1891a412872121",
                "usdc_token_index": 1,
            }
        },
        # WETH
        "0x4200000000000000000000000000000000000006": {
            "priority": 2,
            "v3": {
                "pool": "0x85149247691df622eaf1a8bd0cafd40bc45154a9",
                "usdc_token_index": 1,
            }
        },
        # DAI
        "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1": {
            "priority": 3,
            "v3": {
                "pool": "0x100bdc1431a9b09c61c0efc5776814285f8fb248",
                "usdc_token_index": 0,
            }
        },
        # USDT
        "0x94b008aa00579c1307b0ef2c499ad98a8ce58e58": {
            "priority": 4,
            "v3": {
                "pool": "0xf3f3433c3a97f70349c138ada81da4d3554982db",
                "usdc_token_index": 0,
            }
        },
        # USDC
        "0x7f5c764cbc14f9669b88837ca1490cca17c31607": {
            "priority": 5,
            "v3": {
                "pool": "0xf3f3433c3a97f70349c138ada81da4d3554982db",  # Dummy
                "usdc_token_index": 0,
            }
        },
    },
    "arbitrum": {
        # WBTC
        "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f": {
            "priority": 1,
            "v3": {
                "pool": "0xa62ad78825e3a55a77823f00fe0050f567c1e4ee",
                "usdc_token_index": 1,
            }
        },
        # WETH
        "0x82af49447d8a07e3bd95bd0d56f35241523fbab1": {
            "priority": 2,
            "v3": {
                "pool": "0xc31e54c7a869b9fcbecc14363cf510d1c41fa443",
                "usdc_token_index": 1,
            }
        },
        # DAI
        "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1": {
            "priority": 3,
            "v3": {
                "pool": "0xd37af656abf91c7f548fffc0133175b5e4d3d5e6",
                "usdc_token_index": 1,
            }
        },
        # USDT
        "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9": {
            "priority": 4,
            "v3": {
                "pool": "0x13398e27a21be1218b6900cbedf677571df42a48",
                "usdc_token_index": 1,
            }
        },
        # USDC
        "0xff970a61a04b1ca14834a43f5de4533ebddb5cc8": {
            "priority": 5,
            "v3": {
                "pool": "0x13398e27a21be1218b6900cbedf677571df42a48",  # Dummy
                "usdc_token_index": 1,
            }
        },
    },
    "celo": {
        # WETH
        # "0x66803fb87abd4aac3cbb3fad7c3aa01f6f3fb207": {
        #     "priority": 1,
        #     "v3": {
        #         "pool": "0xc31e54c7a869b9fcbecc14363cf510d1c41fa443",
        #         "usdc_token_index": 1,
        #     }
        # },
        # CELO
        "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1": {
            "priority": 2,
            "v3": {
                "pool": "0x079e7a44f42e9cd2442c3b9536244be634e8f888",
                "usdc_token_index": 1,
            }
        },
        # cUSD
        "0x765de816845861e75a25fca122bb6898b8b1282a": {
            "priority": 3,
            "v3": {
                "pool": "0xea3fb6e3313a2a90757e4ca3d6749efd0107b0b6",
                "usdc_token_index": 0,
            }
        },
        # USDC
        "0x37f750b7cc259a2f741af45294f6a16572cf5cad": {
            "priority": 4,
            "v3": {
                "pool": "0xea3fb6e3313a2a90757e4ca3d6749efd0107b0b6",  # Dummy
                "usdc_token_index": 0,
            }
        },
    }
}

WETH_USDC_POOL = {
    "mainnet": "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8",
    "polygon": "0x45dda9cb7c25131df268515131f647d726f50608",
    "optimism": "0x85149247691df622eaf1a8bd0cafd40bc45154a9",
    "arbitrum": "0x17c14d2c404d167802b16c450d3c99f88f2c4f4d",
    "celo": "0xd88d5f9e6c10e6febc9296a454f6c2589b1e8fae"  # needs to be fixed
}
