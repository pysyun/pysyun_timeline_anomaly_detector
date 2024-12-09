import requests
import json
from time import sleep
from pysyun.anomaly.detector import Detector
from pysyun.anomaly.extractor import Extractor
from storage_timeline_client import Storage
from pysyun_chain import ChainableGroup, Chainable
from pysyun_uniswap_source.uniswap_source import UniswapV2ReservesSource


class UniswapPairsCollector:

    def __init__(self, provider_settings, storage_uri, schema_name, num_threads):
        self.provider_settings = provider_settings
        self.storage_uri = storage_uri
        self.schema_name = schema_name
        self.num_threads = num_threads

    def process(self, pool_address):
        reserves_processor = UniswapV2ReservesSource(self.provider_settings)

        pipeline = ChainableGroup(self.num_threads) | Chainable(reserves_processor)

        data = pipeline.process(pool_address)

        processed_data = [[address, [data[i][0]]] for i, address in enumerate(pool_address)]

        ((ChainableGroup(self.num_threads) | Chainable(StorageSaver(self.storage_uri, self.schema_name)))
         .process(processed_data))


class UniswapAnomalyDetector:

    # TODO: Document arguments
    def __init__(self, storage_uri, schema_name, num_threads, anomaly_threshold=0.7):
        self.storage_uri = storage_uri
        self.schema_name = schema_name
        self.num_threads = num_threads
        self.anomaly_threshold = anomaly_threshold

    # TODO: Document arguments
    # TODO: Add comments inside this method to understand, what is happening there?
    def process(self, pool_address):
        data_reader = StorageReader(self.storage_uri, self.schema_name)
        time_lines_pipeline = (ChainableGroup(self.num_threads) | Chainable(data_reader) | Chainable(ValueExtractor))

        # TODO: Is it possible to merge that into a single pipeline definition?
        clean_pipeline = ChainableGroup(self.num_threads) | Chainable(Detector())
        anomaly_pipeline = (ChainableGroup(self.num_threads) | Chainable(Extractor(self.anomaly_threshold)))

        time_lines = time_lines_pipeline.process(pool_address)
        clean_time_lines = clean_pipeline.process(time_lines)

        data_for_anomaly = list(zip(time_lines, clean_time_lines))
        anomalies = anomaly_pipeline.process(data_for_anomaly)

        processed_data = [[address, [anomalies[i]]] for i, address in enumerate(pool_address)]

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

        # TODO: How to handle multiple markets?
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


# TODO: Move values to environment variables
def main():
    while True:
        # TODO: How to process multiple markets?
        # TODO: Why do we need amount of threads?
        (UniswapPairsCollector(
            "https://bsc-dataseed1.binance.org",
            "https://europe-west1-hype-dev.cloudfunctions.net/storage-timeline/",
            "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73.last-1000-pair",
            3)
         .process(["0x0034642Dde527966486bb40198d82469cb92E55b"]))
        sleep(5)

        # TODO: Why do we need amount of threads?
        (UniswapAnomalyDetector(
            "https://europe-west1-hype-dev.cloudfunctions.net/storage-timeline/",
            "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73.last-1000-pair",
            3)
         .process("0x0034642Dde527966486bb40198d82469cb92E55b"))
        sleep(5)


if __name__ == "__main__":
    main()
