import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

class Detector:

    def __init__(self,
                 extreme_window=60,
                 extreme_threshold=3.0,
                 local_window=15,
                 local_threshold=2.0,
                 transition_window=5,
                 transition_threshold=0.8):
        self.extreme_window = extreme_window
        self.extreme_threshold = extreme_threshold
        self.local_window = local_window
        self.local_threshold = local_threshold
        self.transition_window = transition_window
        self.transition_threshold = transition_threshold

    @staticmethod
    def _convert_to_series(data):
        if isinstance(data[0], list):
            data = data[0]
        df = pd.DataFrame(data)

        if df['time'].duplicated().any():
            df = df.groupby('time')['value'].mean().reset_index()

        return pd.Series(df['value'].values, index=df['time'])

    def _detect_legitimate_transitions(self, series):
        rate_of_change = series.diff()
        avg_change = rate_of_change.abs().rolling(
            window=self.transition_window,
            center=True,
            min_periods=1
        ).mean()

        transitions = (avg_change > (avg_change.mean() * self.transition_threshold)).fillna(False).values
        transitions_expanded = np.zeros_like(transitions)

        for i in range(len(transitions)):
            start = max(0, i - 1)
            end = min(len(transitions), i + 2)
            if np.any(transitions[start:end]):
                transitions_expanded[i] = True

        return transitions_expanded

    def _remove_extreme_outliers(self, series):
        rolling = series.rolling(window=self.extreme_window, center=True, min_periods=1)

        median = rolling.median()
        mad = rolling.apply(lambda x: np.median(np.abs(x - np.median(x))))

        lower = median - self.extreme_threshold * mad
        upper = median + self.extreme_threshold * mad

        extreme_outliers = ((series < lower) | (series > upper)).values

        series_clean = series.copy()
        series_clean[extreme_outliers] = np.nan

        return series_clean.interpolate(method='linear', limit_direction='both')

    def _handle_local_anomalies(self, series):
        transitions = self._detect_legitimate_transitions(series)

        rolling = series.rolling(window=self.local_window, center=True, min_periods=1)

        q1 = rolling.quantile(0.25)
        q3 = rolling.quantile(0.75)
        iqr = q3 - q1

        lower = q1 - self.local_threshold * iqr
        upper = q3 + self.local_threshold * iqr

        anomalies = ((series < lower) | (series > upper)).values & (~transitions)

        series_clean = series.copy()
        series_clean[anomalies] = np.nan

        return series_clean.interpolate(method='linear', limit_direction='both')

    @staticmethod
    def _apply_final_smoothing(series):
        window_length = min(15, len(series) // 3)
        if window_length % 2 == 0:
            window_length += 1

        if len(series) > window_length:
            smoothed = savgol_filter(
                series.values,
                window_length=window_length,
                polyorder=3
            )
            return pd.Series(smoothed, index=series.index)
        return series

    def process(self, data):
        if not data:
            return []

        series = self._convert_to_series(data)

        series_no_extremes = self._remove_extreme_outliers(series)

        series_no_anomalies = self._handle_local_anomalies(series_no_extremes)

        series_smoothed = self._apply_final_smoothing(series_no_anomalies)

        result = [
            {"time": int(t), "value": float(v)}
            for t, v in series_smoothed.items()
            if not pd.isna(v)
        ]

        return result
