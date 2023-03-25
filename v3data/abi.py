"""ABIs for contract calls"""

MASTERCHEF_ABI = [
    {
        "inputs": [
            {
                "internalType": "contract SushiToken",
                "name": "_sushi",
                "type": "address",
            },
            {"internalType": "address", "name": "_devaddr", "type": "address"},
            {"internalType": "uint256", "name": "_sushiPerBlock", "type": "uint256"},
            {"internalType": "uint256", "name": "_startBlock", "type": "uint256"},
            {"internalType": "uint256", "name": "_bonusEndBlock", "type": "uint256"},
        ],
        "stateMutability": "nonpayable",
        "type": "constructor",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "address",
                "name": "lpToken",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "allocPoint",
                "type": "uint256",
            },
        ],
        "name": "AddLp",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "user",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "pid",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256",
            },
        ],
        "name": "Deposit",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "user",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "pid",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256",
            },
        ],
        "name": "EmergencyWithdraw",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "previousOwner",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "newOwner",
                "type": "address",
            },
        ],
        "name": "OwnershipTransferred",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "address",
                "name": "lpToken",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "allocPoint",
                "type": "uint256",
            },
        ],
        "name": "SetAllocPoint",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "user",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "pid",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256",
            },
        ],
        "name": "Withdraw",
        "type": "event",
    },
    {
        "inputs": [],
        "name": "BONUS_MULTIPLIER",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_allocPoint", "type": "uint256"},
            {"internalType": "contract IERC20", "name": "_lpToken", "type": "address"},
            {"internalType": "bool", "name": "_withUpdate", "type": "bool"},
        ],
        "name": "add",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "bonusEndBlock",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_pid", "type": "uint256"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"},
        ],
        "name": "deposit",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "_devaddr", "type": "address"}],
        "name": "dev",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "devaddr",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_pid", "type": "uint256"}],
        "name": "emergencyWithdraw",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_from", "type": "uint256"},
            {"internalType": "uint256", "name": "_to", "type": "uint256"},
        ],
        "name": "getMultiplier",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "massUpdatePools",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_pid", "type": "uint256"}],
        "name": "migrate",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "migrator",
        "outputs": [
            {"internalType": "contract IMigratorChef", "name": "", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_pid", "type": "uint256"},
            {"internalType": "address", "name": "_user", "type": "address"},
        ],
        "name": "pendingSushi",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "poolInfo",
        "outputs": [
            {"internalType": "contract IERC20", "name": "lpToken", "type": "address"},
            {"internalType": "uint256", "name": "allocPoint", "type": "uint256"},
            {"internalType": "uint256", "name": "lastRewardBlock", "type": "uint256"},
            {"internalType": "uint256", "name": "accSushiPerShare", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "poolLength",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "renounceOwnership",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_pid", "type": "uint256"},
            {"internalType": "uint256", "name": "_allocPoint", "type": "uint256"},
            {"internalType": "bool", "name": "_withUpdate", "type": "bool"},
        ],
        "name": "set",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {
                "internalType": "contract IMigratorChef",
                "name": "_migrator",
                "type": "address",
            }
        ],
        "name": "setMigrator",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "startBlock",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "sushi",
        "outputs": [
            {"internalType": "contract SushiToken", "name": "", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "sushiPerBlock",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalAllocPoint",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "newOwner", "type": "address"}],
        "name": "transferOwnership",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_pid", "type": "uint256"}],
        "name": "updatePool",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"},
            {"internalType": "address", "name": "", "type": "address"},
        ],
        "name": "userInfo",
        "outputs": [
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "uint256", "name": "rewardDebt", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_pid", "type": "uint256"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"},
        ],
        "name": "withdraw",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


REWARDER_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "_MASTERCHEF_V2", "type": "address"}
        ],
        "stateMutability": "nonpayable",
        "type": "constructor",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "contract IERC20",
                "name": "rewardToken",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "address",
                "name": "owner",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "rewardPerSecond",
                "type": "uint256",
            },
            {
                "indexed": True,
                "internalType": "contract IERC20",
                "name": "masterLpToken",
                "type": "address",
            },
        ],
        "name": "LogInit",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "user",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "pid",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "to",
                "type": "address",
            },
        ],
        "name": "LogOnReward",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "rewardPerSecond",
                "type": "uint256",
            }
        ],
        "name": "LogRewardPerSecond",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "pid",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint64",
                "name": "lastRewardTime",
                "type": "uint64",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "lpSupply",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "accToken1PerShare",
                "type": "uint256",
            },
        ],
        "name": "LogUpdatePool",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "previousOwner",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "newOwner",
                "type": "address",
            },
        ],
        "name": "OwnershipTransferred",
        "type": "event",
    },
    {
        "inputs": [],
        "name": "MASTERCHEF_V2",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "claimOwnership",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "_rewardToken", "type": "address"},
            {"internalType": "address", "name": "_owner", "type": "address"},
            {"internalType": "uint256", "name": "_rewardPerSecond", "type": "uint256"},
            {"internalType": "address", "name": "_masterLpToken", "type": "address"},
        ],
        "name": "init",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "masterLpToken",
        "outputs": [{"internalType": "contract IERC20", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "pid", "type": "uint256"},
            {"internalType": "address", "name": "_user", "type": "address"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "", "type": "uint256"},
            {"internalType": "uint256", "name": "lpTokenAmount", "type": "uint256"},
        ],
        "name": "onSushiReward",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "pendingOwner",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_pid", "type": "uint256"},
            {"internalType": "address", "name": "_user", "type": "address"},
        ],
        "name": "pendingToken",
        "outputs": [{"internalType": "uint256", "name": "pending", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "pid", "type": "uint256"},
            {"internalType": "address", "name": "user", "type": "address"},
            {"internalType": "uint256", "name": "", "type": "uint256"},
        ],
        "name": "pendingTokens",
        "outputs": [
            {
                "internalType": "contract IERC20[]",
                "name": "rewardTokens",
                "type": "address[]",
            },
            {"internalType": "uint256[]", "name": "rewardAmounts", "type": "uint256[]"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "poolInfo",
        "outputs": [
            {"internalType": "uint128", "name": "accToken1PerShare", "type": "uint128"},
            {"internalType": "uint64", "name": "lastRewardTime", "type": "uint64"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "token", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "address payable", "name": "to", "type": "address"},
        ],
        "name": "reclaimTokens",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "rewardPerSecond",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "rewardRates",
        "outputs": [{"internalType": "uint256[]", "name": "", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "rewardToken",
        "outputs": [{"internalType": "contract IERC20", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_rewardPerSecond", "type": "uint256"}
        ],
        "name": "setRewardPerSecond",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "newOwner", "type": "address"},
            {"internalType": "bool", "name": "direct", "type": "bool"},
            {"internalType": "bool", "name": "renounce", "type": "bool"},
        ],
        "name": "transferOwnership",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "pid", "type": "uint256"}],
        "name": "updatePool",
        "outputs": [
            {
                "components": [
                    {
                        "internalType": "uint128",
                        "name": "accToken1PerShare",
                        "type": "uint128",
                    },
                    {
                        "internalType": "uint64",
                        "name": "lastRewardTime",
                        "type": "uint64",
                    },
                ],
                "internalType": "struct Rewarder.PoolInfo",
                "name": "pool",
                "type": "tuple",
            }
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"},
            {"internalType": "address", "name": "", "type": "address"},
        ],
        "name": "userInfo",
        "outputs": [
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "uint256", "name": "rewardDebt", "type": "uint256"},
            {"internalType": "uint256", "name": "unpaidRewards", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]
