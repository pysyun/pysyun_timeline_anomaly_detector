# pysyun_timeline_anomaly_detector
PySyun Timeline Framework Anomaly Detection Components

# pysyun_timeline_anomaly_detector
PySyun Timeline Framework Anomaly Detection Components

## Overview
A Python library for detecting and cleaning anomalies in time series data. The library provides two main components:
- `SignalCleaner`: Removes outliers and smooths time series data
- `AnomalyExtractor`: Identifies anomalous points by comparing original and cleaned signals

## Installation
```
pip install git+https://github.com/pysyun/pysyun_timeline_anomaly_detector.git
```

## Usage

### SignalCleaner

```python
from pysyun_anomaly_detector import SignalCleaner

# Initialize with custom parameters
cleaner = SignalCleaner(
    extreme_window=60,
    extreme_threshold=3.0,
    local_window=15,
    local_threshold=2.0,
    transition_window=5,
    transition_threshold=0.8
)

# Input data format: list of dictionaries with 'time' and 'value' keys
data = [
    {"time": 1, "value": 10.5},
    {"time": 2, "value": 11.0},
    # ...
]

cleaned_data = cleaner.process(data)
```

### AnomalyExtractor

```python
from pysyun_anomaly_detector import AnomalyExtractor

extractor = AnomalyExtractor(epsilon=0.5)

# Compare original and cleaned signals
anomalies = extractor.process([original_data, cleaned_data])
```

## Parameters

### SignalCleaner
- `extreme_window`: Window size for extreme outlier detection (default: 60)
- `extreme_threshold`: MAD threshold for extreme outliers (default: 3.0)
- `local_window`: Window size for local anomaly detection (default: 15)
- `local_threshold`: IQR threshold for local anomalies (default: 2.0)
- `transition_window`: Window size for legitimate transition detection (default: 5)
- `transition_threshold`: Threshold for transition detection (default: 0.8)

### AnomalyExtractor
- `epsilon`: Minimum difference threshold for anomaly detection (default: 0.5)

## Requirements
- pandas
- numpy
- scipy