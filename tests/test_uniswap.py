import requests
import json
from time import sleep
import web3

from pysyun.anomaly.detector import Detector
from pysyun.anomaly.extractor import Extractor
from storage_timeline_client import Storage
from pysyun_chain import ChainableGroup, Chainable
from pysyun_uniswap_source.uniswap_source import UniswapV2ReservesSource


class UniswapPairsCollector:
    """
    Class for collecting data from Uniswap liquidity pools.

    Args:
        provider_settings (str): URL of the blockchain provider
        storage_uri (str): URI for accessing the data storage
        schema_name (str): Name of the schema in data storage
        num_threads (int): Number of threads for parallel processing
    """

    def __init__(self, provider_settings, storage_uri, schema_name, num_threads):
        self.provider_settings = provider_settings
        self.storage_uri = storage_uri
        self.schema_name = schema_name
        self.num_threads = num_threads

    def process(self, pool_address):
        """
        Processes liquidity pool addresses to collect reserve data.

        Args:
            pool_address (list): List of liquidity pool addresses to collect data from

        Returns:
            None: Data is saved directly to storage
        """

        # Check-summ the incoming addresses
        check_summed_addresses = []
        for address in pool_address:
            check_summed_addresses.append(web3.Web3.to_checksum_address(address))
        pool_address = check_summed_addresses

        # Initialize the reserves processor with blockchain provider settings
        reserves_processor = UniswapV2ReservesSource(self.provider_settings)

        # Create pipeline for fetching reserve data
        pipeline = ChainableGroup(self.num_threads) | Chainable(reserves_processor)

        # Get reserves data for each pool
        data = pipeline.process(pool_address)

        # Format data for storage - pair each address with its corresponding data
        processed_data = [[address, [data[i][0]]] for i, address in enumerate(pool_address)]

        # Save the processed data to storage using parallel processing
        ((ChainableGroup(self.num_threads) | Chainable(StorageSaver(self.storage_uri, self.schema_name)))
         .process(processed_data))


class UniswapAnomalyDetector:
    """
    Class for detecting anomalies in Uniswap liquidity pool data.

    Args:
        storage_uri (str): URI for accessing the data storage
        schema_name (str): Name of the schema in data storage
        num_threads (int): Number of threads for parallel processing
        anomaly_threshold (float, optional): Threshold for anomaly detection. Defaults to 0.7
    """
    def __init__(self, storage_uri, schema_name, num_threads, anomaly_threshold=0.7):
        self.storage_uri = storage_uri
        self.schema_name = schema_name
        self.num_threads = num_threads
        self.anomaly_threshold = anomaly_threshold

    def process(self, pool_address):
        """
        Processes liquidity pool data to detect anomalies.

        Args:
            pool_address (list): List of liquidity pool addresses to analyze

        Returns:
            list: List of detected anomalies for each pool
        """
        # Create reader for fetching data from storage
        data_reader = StorageReader(self.storage_uri, self.schema_name)

        # Create pipeline for retrieving and preprocessing time series
        time_lines_pipeline = (ChainableGroup(self.num_threads) |
                               Chainable(data_reader) |
                               Chainable(ValueExtractor))

        # Pipeline for cleaning data from noise and outliers
        clean_pipeline = ChainableGroup(self.num_threads) | Chainable(Detector())

        # Pipeline for detecting anomalies based on threshold value
        anomaly_pipeline = (ChainableGroup(self.num_threads) |
                            Chainable(Extractor(self.anomaly_threshold)))

        # Get time series for analysis
        time_lines = time_lines_pipeline.process(pool_address)

        # Clean time series from noise
        clean_time_lines = clean_pipeline.process(time_lines)

        # Prepare data for anomaly detection
        data_for_anomaly = list(zip(time_lines, clean_time_lines))

        # Detect anomalies by comparing original and cleaned data
        anomalies = anomaly_pipeline.process(data_for_anomaly)

        # Format results for storage
        processed_data = [[address, [anomalies[i]]] for i, address in enumerate(pool_address)]

        # Save results to storage
        ((ChainableGroup(self.num_threads) | Chainable(StorageSaver(self.storage_uri, self.schema_name)))
         .process(processed_data))

        return anomalies


class ValueExtractor:
    @staticmethod
    def process(data):
        processed_data = []

        for item in data:
            processed_item = {
                'time': item['time'],
                'value': item['value']['r'][0]
            }
            processed_data.append(processed_item)

        return processed_data


class StorageSaver:

    def __init__(self, storage_uri: str, schema_name: str):
        self.storage = Storage(storage_uri)
        self.schema_name = schema_name
        self._ensure_schema_exists()

    def _ensure_schema_exists(self):
        schema_list = self.storage.list()
        if self.schema_name not in schema_list:
            create_schema = self.storage.uri + 'storage/create'
            data = {"schema": self.schema_name}
            requests.post(create_schema, data=data, verify=False)

    def process(self, data):

        timeline_name = data[0]
        values = data[1]

        schema = self.storage.schema(self.schema_name)
        timeline = schema.time_line(timeline_name)

        for value in values:
            timeline.add_string(value["value"], time=value["time"])

        return data


# TODO: Replace with the existing PySyun timeline class
class StorageReader:

    def __init__(self, storage_uri: str, schema_name: str):
        self.storage = Storage(storage_uri)
        self.schema_name = schema_name

    @staticmethod
    def parse_value(item):
        try:
            parsed_item = item.copy()
            parsed_item['value'] = json.loads(item['value'])
            return parsed_item
        except json.JSONDecodeError:
            return item

    def process(self, data):
        timeline_name = data[0]

        schema = self.storage.schema(self.schema_name)
        timeline = schema.time_line(timeline_name)

        # Retrieve all string values with their timestamps
        values = timeline.all_strings()

        parsed_values = [self.parse_value(item) for item in values]

        # Return data in the same format as it was saved
        return parsed_values


def main():
    collector = UniswapPairsCollector(
            "https://bsc-dataseed1.binance.org",
            "https://34.69.255.10:82/",
            "uniswap_reserve_data",
            6)
    detector = UniswapAnomalyDetector(
            "https://34.69.255.10:82/",
            "uniswap_anomaly_data",
            6)

    cycle_count = 0
    while True:
        try:
            collector.process(
                [
                    "0xa43fe16908251ee70ef74718545e4fe6c5ccec9f",
                    "0x2f62f2b4c5fcd7570a709dec05d68ea19c82a9ec",
                    "0x7b73644935b8e68019ac6356c40661e1bc315860",
                    "0xa6cc3c2531fdaa6ae1a3ca84c2855806728693e8",
                    "0x744159757cac173a7a3ecf5e97adb10d1a725377",
                    "0x0b07188b12e3bba6a680e553e23c4079e98a034b"
                ]
            )
            sleep(5)

            cycle_count += 1

            # We execute detector.process every 10 cycles
            if cycle_count % 50 == 0:
                detector.process(
                    [
                        "0xa43fe16908251ee70ef74718545e4fe6c5ccec9f",
                        "0x2f62f2b4c5fcd7570a709dec05d68ea19c82a9ec",
                        "0x7b73644935b8e68019ac6356c40661e1bc315860",
                        "0xa6cc3c2531fdaa6ae1a3ca84c2855806728693e8",
                        "0x744159757cac173a7a3ecf5e97adb10d1a725377",
                        "0x0b07188b12e3bba6a680e553e23c4079e98a034b"
                    ]
                )
                sleep(5)

        except Exception as e:
            print(f"Error occurred: {e}")
            sleep(10)


if __name__ == "__main__":
    main()

