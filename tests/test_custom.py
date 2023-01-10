
import sys
import os
import datetime as dt
import logging
import asyncio
import csv
from pathlib import Path

# append parent directory pth
CURRENT_FOLDER = os.path.dirname(os.path.realpath(__file__))
PARENT_FOLDER = os.path.dirname(CURRENT_FOLDER)
sys.path.append(PARENT_FOLDER)

from dbdata import db_managers
from v3data.constants import PROTOCOL_UNISWAP_V3
#from v3data.common import hypervisor
from v3data.hypes import impermanent_data, fees_yield


CHAIN = "mainnet" # polygon
mongo_srv_url = "mongodb://10.10.0.39:49154"
db_name = "gamma_v1"
collections = {
    "static": {"id":True},
    "returns":{"id":True}
}



async def simulate_query():

    block = timestamp = 0
    result = dict()
    for days in [1,7,30]:
        # init 
        result[days] = dict()

        # add ilg to result
        all_dta = impermanent_data.ImpermanentData_permanent(period_days=days,protocol=PROTOCOL_UNISWAP_V3,chain=CHAIN)
        returns_dta = await all_dta.get_feesYield_data()
        imperm_dta = await all_dta.get_impermanent_data(get_data=False)

        # get block n timestamp
        block = all_dta.raw_data["current_block"]
        timestamp = all_dta.raw_data["current_timestamp"]

        # fee yield data process
        for k,v in returns_dta.items():
            if not k in result[days].keys():
                result[days][k] = dict()
                # no ilg data for this hypervisor
                result[days][k]["id"] = f"{CHAIN}_{k}_{block}"
                result[days][k]["chain"] = CHAIN
                result[days][k]["period"] = days
                result[days][k]["hypervisor_id"] = k
                result[days][k]["symbol"] = v["symbol"]
                result[days][k]["block"] = block
                result[days][k]["timestamp"] = timestamp
            result[days][k]["return"] = {
                        "feeApr": v["feeApr"],
                        "feeApy": v["feeApy"],
                        "hasOutlier": v["hasOutlier"]
                        }
        
        # impermanent data process 
        for k,v in imperm_dta.items():
            # only hypervisors with FeeYield data 
            if k in result[days].keys():
                result[days][k]["ilg"] = {
                        "vs_HODL_USD": v["vs_HODL_USD"],
                        "vs_HODL_deposited": v["vs_HODL_deposited"],
                        "vs_HODL_token0": v["vs_HODL_token0"],
                        "vs_HODL_token1": v["vs_HODL_token1"]
                        }

    # create database manager/connector
    db_connector = db_managers.MongoDbManager(url=mongo_srv_url, db_name=db_name, collections=collections)

    # add item by item to database
    for period,hypervisors in result.items():

        for hyp_id, hyp in hypervisors.items():
            # convert int to string ( mongo 8bit int)
            # value = { k:str(v) for k,v in value.items()}
            # add to mongodb
            db_connector.add_item(coll_name="returns", item_id=hyp["id"], data=hyp)



# TESTING
if __name__ == "__main__":
    asyncio.run(simulate_query())