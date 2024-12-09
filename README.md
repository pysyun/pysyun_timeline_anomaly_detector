# PySyun Timeline Anomaly Detector
PySyun Timeline Framework Anomaly Detection Components

## Overview
A Python library for detecting and cleaning anomalies in time series data. The library provides two main components:
- `pysyun.anomaly.detector.Detector`: Removes outliers and smooths time series data.
- `pysyun.anomaly.extractor.Extractor`: Identifies anomalous points by comparing original and cleaned signals.

## Installation
```
pip install git+https://github.com/pysyun/pysyun_timeline_anomaly_detector.git
```

## Usage

### pysyun.anomaly.detector.Detector

```python
from pysyun.anomaly.detector import Detector

# Initialize with custom parameters
detector = Detector(
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

cleaned_data = detector.process(data)
```

### pysyun.anomaly.extractor.Extractor

```python
from pysyun.anomaly.extractor import Extractor

extractor = Extractor(epsilon=0.5)

# Compare original and cleaned signals
anomalies = extractor.process([original_data, cleaned_data])
```

## Parameters

### pysyun.anomaly.detector.Detector
- `extreme_window`: Window size for extreme outlier detection (default: 60)
- `extreme_threshold`: MAD threshold for extreme outliers (default: 3.0)
- `local_window`: Window size for local anomaly detection (default: 15)
- `local_threshold`: IQR threshold for local anomalies (default: 2.0)
- `transition_window`: Window size for legitimate transition detection (default: 5)
- `transition_threshold`: Threshold for transition detection (default: 0.8)

### pysyun.anomaly.extractor.Extractor
- `epsilon`: Minimum difference threshold for anomaly detection (default: 0.5)

## Requirements
- pandas
- numpy
- scipy

