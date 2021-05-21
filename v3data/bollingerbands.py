import datetime
import numpy as np
import pandas as pd
from v3data.data import UniV3Data


class BollingerBand:
    def __init__(self, pool_address, total_period_hours, n_intervals=20):
        self.pool_address = pool_address
        self.total_period_hours = total_period_hours  # total_period_hours is how long we want to average over
        self.n_intervals = n_intervals
        self.client = UniV3Data()

    def get_data(self):
        data = self.client.get_historical_pool_prices(
            self.pool_address, datetime.timedelta(hours=10 * self.total_period_hours))
        df = pd.DataFrame(data, dtype=np.float64)
        df['datetime'] = pd.to_datetime(df.timestamp, unit='s')

        interval = self.total_period_hours / self.n_intervals
        df_resampled = df.sort_values('datetime').resample(f"{interval}H", on='datetime').last()
        df_resampled.fillna(method='ffill', inplace=True)
        df_resampled['mid'] = df_resampled.priceInToken1.rolling(self.n_intervals).mean()
        df_resampled['std'] = df_resampled.priceInToken1.rolling(self.n_intervals).std()
        df_resampled['upper'] = df_resampled['mid'] + 2 * df_resampled['std']
        df_resampled['lower'] = df_resampled['mid'] - 2 * df_resampled['std']
        df_resampled.dropna(inplace=True)

        self.df_resampled = df_resampled[['priceInToken1', 'mid', 'upper', 'lower']]

    def chart_data(self):
        pool = self.client.get_pool(self.pool_address)
        self.get_data()
        df = self.df_resampled.reset_index()
        df.rename(columns={
            'priceInToken1': 'value',
            'lower': 'min',
            'upper': 'max'
        }, inplace=True)
        df['group'] = f"{pool['token0']['symbol']}-{pool['token1']['symbol']}"
        df['date'] = df.datetime.dt.strftime('%Y-%m-%dT%H:%M:%SZ')

        return df[['group', 'date', 'value', 'min', 'max']].to_dict('records')
