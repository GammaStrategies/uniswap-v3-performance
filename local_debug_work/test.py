
########################
### TEST ENVIRONMENT ###
########################


import json
import asyncio

import sys
import os
import csv
import datetime as dt
from pathlib import Path




# append parent directory pth
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)



########  BLOCK as STRING error
from v3data.gamma import GammaCalculations,GammaYield
from v3data.hypervisor import HypervisorInfo
def test_block_keys():

    # start time log
    _startime = dt.datetime.utcnow()

    calculations = HypervisorInfo(protocol="uniswap_v3", chain="mainnet")

    hyplst=asyncio.run(calculations.all_data())

    # end time log
    _timelapse = dt.datetime.utcnow() - _startime
    print(" took {:,.2f} seconds to complete".format(_timelapse.total_seconds()))


    for hyp_id, hyp in hyplst.items():
        try:
            current_feeApr = no_mod[hyp_id]["returns"]["daily"]["feeApr"]
            current_feeApy = no_mod[hyp_id]["returns"]["daily"]["feeApy"]

            modded_feeApr = hyp["returns"]["daily"]["feeApr"]
            modded_feeApy = hyp["returns"]["daily"]["feeApy"]

            diff_feeApr = ((current_feeApr-modded_feeApr)/current_feeApr) if (current_feeApr-modded_feeApr) != 0 else 0
            diff_feeApy = ((current_feeApy-modded_feeApy)/current_feeApy) if (current_feeApy-modded_feeApy) != 0 else 0

            name = "".join([(hyp["name"][x] if x < len(hyp["name"]) else "_") for x in range(20)])

            print("{} \t current | modded | diff ->    feeApr: {:,.2%} | {:,.2%} | {:,.2%}    -> feeApy: {:,.2%} | {:,.2%} | {:,.2%}        hyp_id:0x..{}".format(name, current_feeApr, modded_feeApr, diff_feeApr, current_feeApy, modded_feeApy, diff_feeApy, hyp_id[-5:]))
        except:
            print("{} \t current | modded | diff ->    error     hyp_id:{}".format(name, hyp_id))



########  IMPERMANENT LOSS GAIN 
from v3data.hypes import impermanent_data
def test_Impermanent():

    # define parameters
    period_days = 7
    protocol = "uniswap_v3"
    chain = "mainnet" 

    # start time log
    _startime = dt.datetime.utcnow()

    IM = impermanent_data.ImpermanentData(period_days=period_days, protocol=protocol, chain=chain)

    asyncio.run(IM.get_data())

    # end time log
    _timelapse = dt.datetime.utcnow() - _startime
    print(" took {:,.2f} seconds to complete".format(_timelapse.total_seconds()))


    # save result file
    csv_filename = "impermanent_{}_{}_{}_{}.csv".format(chain, protocol, IM.data["initial_block"], IM.data["current_block"])
    # remove file if exists
    try:
        os.remove(csv_filename)
    except:
        pass

    # save csv 
    SaveCSV(csv_filename,list(IM.data["hype_data"].values())[0].keys(), IM.data["hype_data"].values())
    








########  DEBUG HELPER FUNCs ################################################
def SaveCSV(filename, columns, rows):
    """ Save multiple rows to CSV

     Arguments:
        rows {[type]} -- corresponding to fieldname headers defined like: 
                        [{
                        'time': self.time,
                        'id': self.oid,
                        'side': self.side,
                        'price': self.price, 
                        'size': self.size
                        }, ...]
     """
    my_file = Path(filename)
    if not my_file.is_file():
        with open(filename, 'a') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()

    with open(filename, 'a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        for i in rows:
            writer.writerow(i)

def SaveCSV_row(filename, columns, row):
    """ Save 1 row to CSV

     Arguments:
        row (dict)
     """

    my_file = Path(filename)
    # check if folder exists
    if not os.path.exists(my_file.parent):
        # Create a new directory
        os.makedirs(name=my_file.parent, exist_ok=True)

    if not my_file.is_file():
        with open(filename, 'a') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()

    with open(filename, 'a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writerow(row)









######## TEST WHAT ################################################
if __name__ == "__main__":

    # change dir to current
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)


    #test_block_keys()
    test_Impermanent()
