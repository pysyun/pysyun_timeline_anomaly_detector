import pandas as pd
import numpy as np


class Extractor:

    def __init__(self, epsilon=0.5):
        self.epsilon = epsilon

    @staticmethod
    def _convert_to_series(data):
        if isinstance(data[0], list):
            data = data[0]
        df = pd.DataFrame(data)

        if df['time'].duplicated().any():
            df = df.groupby('time')['value'].mean().reset_index()
        return pd.Series(df['value'].values, index=df['time'])

    def process(self, data):
        if not data or len(data) != 2:
            return []

        original_series = self._convert_to_series(data[0])
        cleaned_series = self._convert_to_series(data[1])

        common_index = original_series.index.intersection(cleaned_series.index)
        original_series = original_series[common_index]
        cleaned_series = cleaned_series[common_index]

        difference = np.abs(original_series - cleaned_series)

        anomaly_mask = difference > self.epsilon

        anomalies = original_series[anomaly_mask]

        result = [
            {"time": int(t), "value": float(v)}
            for t, v in anomalies.items()
        ]

        return result
