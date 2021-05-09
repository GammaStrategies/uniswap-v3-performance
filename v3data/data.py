import requests

from v3data.utils import timestamp_to_date


class UniV3SubgraphClient:
    def __init__(self):
        self._url = "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-alt"

    def query(self, query: str) -> dict:
        """Make graphql query to subgraph"""
        response = requests.post(self._url, json={'query': query})
        return response.json()


class UniV3Data(UniV3SubgraphClient):
    def get_factory(self):
        """Get factory data."""
        query = """
        {
          factory(id: "0x1F98431c8aD98523631AE4a59f267346ea31F984") {
            id
            poolCount
            txCount
            totalVolumeUSD
            totalValueLockedUSD
          }
        }
        """

        self.factory = self.query(query)['data']['factory']

    def get_pools(self):
        """Get latest factory data."""
        query = """
        {
          pools(
            first: 1000
            orderBy: volumeUSD
            orderDirection: desc
          ){
            id
            token0{
              symbol
            }
            token1{
              symbol
            }
            volumeUSD
          }
        }
        """
        self.pools = self.query(query)['data']['pools']

    def get_daily_uniswap_data(self):
        """Get aggregated daily data for uniswap v3."""
        query = """
        {
          uniswapDayDatas(
            first: 1000
            orderBy: date
            orderDirection: asc
          ) {
            id
            date
            volumeUSD
            tvlUSD
            txCount
          }
        }
        """

        self.daily_uniswap_data = self.query(query)['data']['uniswapDayDatas']

    def get_daily_pool_data(self):
        """Get daily data for pools."""
        self.get_daily_uniswap_data()
        # Loop through days
        self.daily_pool_data = []
        for day in self.daily_uniswap_data:
            query = f"""
            {{
              poolDayDatas(
                first: 1000
                where: {{ date: {day['date']} }}
                orderBy: volumeUSD
                orderDirection: desc
              ){{
                id
                date
                pool{{
                  id
                  token0{{symbol}}
                  token1{{symbol}}
                }}
                tvlUSD
                volumeUSD
                txCount
              }}
            }}
            """
            self.daily_pool_data.extend(self.query(query)['data']['poolDayDatas'])

    def uniswap_data(self):
        """Current TVL, volume, transaction count."""
        self.get_factory()
        data = {
            'totalValueLockedUSD': self.factory['totalValueLockedUSD'],
            'totalVolumeUSD': self.factory['totalVolumeUSD'],
            'txCount': self.factory['txCount']
        }
        return data

    def volume_pie_chart_data(self):
        """Data for pie chart of pool volumes"""
        self.get_pools()

        volume = [float(pool['volumeUSD']) for pool in self.pools]
        labels = [f"{pool['token0']['symbol']}-{pool['token1']['symbol']}" for pool in self.pools]

        data = {
            "datasets": [{
                "data": volume
            }],
            "labels": labels
        }

        return data

    def hourly_volume_by_pair(self):
        """Hourly volume by pair"""
        self.get_daily_pool_data()
        data = [
            {
                'pair': f"{pool_day['pool']['token0']['symbol']}-{pool_day['pool']['token1']['symbol']}",
                'date': timestamp_to_date(pool_day['date']),
                'volumeUSD': pool_day['volumeUSD']
            }
            for pool_day in self.daily_pool_data if pool_day['volumeUSD'] != '0'
        ]

        return data

    def cumulative_trade_volume(self):
        """Daily cumulative trade volume."""
        self.get_daily_uniswap_data()
        # This assumes data is ordered already
        cumulative = []
        cumulativeVolumeUSD = 0
        for uniswap_day in self.daily_uniswap_data:
            cumulativeVolumeUSD += float(uniswap_day['volumeUSD'])
            cumulative.append(
                {
                    "date": timestamp_to_date(uniswap_day['date']),
                    "cumulativeVolumeUSD": cumulativeVolumeUSD
                }
            )

        return cumulative
