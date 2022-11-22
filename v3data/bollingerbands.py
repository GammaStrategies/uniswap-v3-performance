import datetime
import asyncio
import numpy as np
import pandas as pd
from v3data.data import UniV3Data


class BollingerBand:
    def __init__(
        self,
        pool_address: str,
        total_period_hours,
        protocol: str,
        n_intervals=20,
        chain: str = "mainnet",
    ):
        self.pool_address = pool_address.lower()
        self.total_period_hours = total_period_hours  # how long to average over
        self.n_intervals = n_intervals
        self.client = UniV3Data(protocol, chain)

    async def get_data(self, report_hours=None):
        # Defaults to 10 times the total_period_hour if no report_hours is given
        if not report_hours:
            report_hours = 10 * self.total_period_hours
        data = await self.client.get_historical_pool_prices(
            self.pool_address, datetime.timedelta(hours=1.1 * report_hours)
        )  # 1.1 factor for buffer
        df = pd.DataFrame(data, dtype=np.float64)  # Pandas future warning
        df["datetime"] = pd.to_datetime(df.timestamp, unit="s")

        interval = self.total_period_hours / self.n_intervals
        df_resampled = (
            df.sort_values("datetime").resample(f"{interval}H", on="datetime").last()
        )
        df_resampled.fillna(method="ffill", inplace=True)
        df_resampled["mid"] = df_resampled.priceDecimal.rolling(self.n_intervals).mean()
        df_resampled["std"] = df_resampled.priceDecimal.rolling(self.n_intervals).std()
        df_resampled["upper"] = df_resampled["mid"] + 2 * df_resampled["std"]
        df_resampled["lower"] = df_resampled["mid"] - 2 * df_resampled["std"]
        df_resampled.dropna(inplace=True)

        self.df_resampled = df_resampled[["priceDecimal", "mid", "upper", "lower"]]

    async def chart_data(self):
        pool, _ = await asyncio.gather(
            self.client.get_pool(self.pool_address), self.get_data()
        )

        df = self.df_resampled.reset_index()
        df.rename(
            columns={"priceDecimal": "value", "lower": "min", "upper": "max"},
            inplace=True,
        )
        df["group"] = f"{pool['token0']['symbol']}-{pool['token1']['symbol']}"
        df["date"] = df.datetime.dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        return df[["group", "date", "value", "min", "max"]].to_dict("records")

    async def latest_bands(self):
        pool, _ = await asyncio.gather(
            self.client.get_pool(self.pool_address),
            self.get_data(report_hours=self.total_period_hours),
        )
        bands = self.df_resampled.tail(1).reset_index().to_dict("records")[0]
        bands["datetime"] = bands["datetime"].strftime("%Y-%m-%dT%H:%M:%SZ")
        return {"pool": pool, "bands": bands}
