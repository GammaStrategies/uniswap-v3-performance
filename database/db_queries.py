



class db_returns_queries():

    # TODO: group by period
    @staticmethod
    def hypervisors_average(chain:str, period:str)->list[dict]:
        return [{
                    "$match": 
                    {
                        "chain": chain,
                        "period": period,
                    }
                },
                {
                    "$sort": { "block" : 1 }
                },
                {
                    "$project":
                    {       "address":"$address",
                            "timestamp": "$timestamp",
                            "block": "$block",
                            "feeApr": "$fees.feeApr",
                            "feeApy": "$fees.feeApy",
                            "imp_vs_hodl_usd": "$impermanent.vs_hodl_usd",
                            "imp_vs_hodl_deposited":"$impermanent.vs_hodl_deposited",
                            "imp_vs_hodl_token0": "$impermanent.vs_hodl_token0",
                            "imp_vs_hodl_token1": "$impermanent.vs_hodl_token1",
                    }
                },
                {   "$group":
                    {
                        "_id": "$address",
                        "items": { "$push" : "$$ROOT" },
                        "min_timestamp": { "$min": '$timestamp'},
                        "max_timestamp": { "$max": '$timestamp'},
                        "min_block": { "$min": '$block'},
                        "max_block": { "$max": '$block'},
                        "av_feeApr": { "$avg": '$feeApr'},
                        "av_feeApy": { "$avg": '$feeApy'},
                        "av_imp_vs_hodl_usd": { "$avg": '$imp_vs_hodl_usd'},
                        "av_imp_vs_hodl_deposited": { "$avg": '$imp_vs_hodl_deposited'},
                        "av_imp_vs_hodl_token0": { "$avg": '$imp_vs_hodl_token0'},
                        "av_imp_vs_hodl_token1": { "$avg": '$imp_vs_hodl_token1'},
                    }
                },
                ]