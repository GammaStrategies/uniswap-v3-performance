
import logging
from v3data.hypes import impermanent_data, fees_yield
from database.db_data_models import hypervisor_return, hypervisor_fees, hypervisor_impermanent, token, pool, hypervisor_static
from v3data.hypervisor import HypervisorData

logger = logging.getLogger(__name__)


# db data formats
async def create_db_returns(chain: str, protocol: str, period_days: int) -> dict:

    # define result var
    result = dict()

    # define calculation class
    all_data = impermanent_data.ImpermanentDivergence(
        period_days=period_days, protocol=protocol, chain=chain
    )
    # calculate return
    returns_data = await all_data.get_fees_yield(get_data=True)
    # calculate impermanent divergence
    imperm_data = await all_data.get_impermanent_data(get_data=False)

    # get block n timestamp
    block = all_data.data["current_block"]
    timestamp = all_data._block_ts_map[block]

    # fee yield data process
    for k, v in returns_data.items():
        if not k in result.keys():

            result[k] = hypervisor_return(
                chain=chain,
                period=period_days,
                address=k,
                symbol=v["symbol"],
                block=block,
                timestamp=timestamp,
                fees=hypervisor_fees(
                    feeApr=v["feeApr"], feeApy=v["feeApy"], hasOutlier=v["hasOutlier"]
                ),
            )

    # impermanent data process
    for k, v in imperm_data.items():
        # only hypervisors with FeeYield data
        if k in result.keys():
            result[k].impermanent = hypervisor_impermanent(
                vs_hodl_usd=v["vs_hodl_usd"],
                vs_hodl_deposited=v["vs_hodl_deposited"],
                vs_hodl_token0=v["vs_hodl_token0"],
                vs_hodl_token1=v["vs_hodl_token1"],
            )

    return result

async def create_db_static_hypervisor_info(chain: str, protocol: str) -> dict:

    # define result var
    result = dict()
    hypervisors_data = HypervisorData(protocol=protocol, chain=chain)
    # get all hypervisors & their pools data
    await hypervisors_data._get_all_data()
    for hypervisor in hypervisors_data.basics_data:
        # temporal vars
        address = hypervisor["id"]
        hypervisor_name = f'{hypervisor["pool"]["token0"]["symbol"]}-{hypervisor["pool"]["token1"]["symbol"]}-{hypervisor["pool"]["fee"]}'

        _tokens = [
            token(
                address=hypervisor["pool"]["token0"]["id"],
                symbol=hypervisor["pool"]["token0"]["symbol"],
                chain=chain,
                position=0,
            ),
            token(
                address=hypervisor["pool"]["token1"]["id"],
                symbol=hypervisor["pool"]["token1"]["symbol"],
                chain=chain,
                position=1,
            ),
        ]
        _pool = pool(
            address=hypervisor["pool"]["id"],
            chain=chain,
            fee=hypervisor["pool"]["fee"],
            tokens=_tokens,
        )

        # add to result
        result[address] = hypervisor_static(
            chain=chain,
            address=address,
            symbol=hypervisor_name,
            protocol=protocol,
            created=hypervisor["created"],
            pool=_pool,
        )

    return result

