import time
import logging
import requests
from typing import Optional
from modules.data_storage.minio.write_client import MinioWriteClient
from modules.data_ingestion.base_fetcher import DataFetcherBase
from modules.data_ingestion.parsers import parse_price_data

class PriceDataFetcher(DataFetcherBase):
    """
    Fetches cryptocurrency price data and saves it to MinIO.
    """

    def __init__(self, minio_write_client: MinioWriteClient, url: str, symbols: list[str], source: str, fetch_interval_second: int = 5, save_batch_size: int = 100):
        super().__init__(minio_write_client=minio_write_client, save_batch_size=save_batch_size)
        self.minio_write_client = minio_write_client
        self.base_url = url 
        self.symbols = symbols
        self.source = source
        self.fetch_interval_second = fetch_interval_second
        self.save_batch_size = save_batch_size
        self.data_batch: list[dict] = []

    def fetch_price_data(self, symbol: str) -> Optional[dict[str, str]]:
        try:
            logging.debug(f"Fetching price data for symbol: {symbol} from source: {self.source}")
            response = requests.get(f"{self.base_url}?symbol={symbol}")
            response.raise_for_status()
            data = response.json()
            
            parsed_data = parse_price_data(price_data=data, source=self.source)
            logging.debug(f"Fetched price data: {parsed_data}")
            return parsed_data

        except requests.RequestException as e:
            logging.error(f"Failed to fetch price from Binance: {e}")
            return None

    def start(self):
        """
        Periodically fetches price data and saves it to MinIO.
        """
        logging.info("Starting the PriceDataFetcher...")
        while True:
            for symbol in self.symbols:
                price_data = self.fetch_price_data(symbol=symbol)
                
                if price_data:
                    self.data_batch.append(price_data)

            self.log_progress(data_batch=self.data_batch)

            if len(self.data_batch) >= self.save_batch_size:
                self.data_batch = self.save_to_minio(data_batch=self.data_batch)
            
            time.sleep(self.fetch_interval_second)