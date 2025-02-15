import logging
from abc import ABC, abstractmethod
from modules.data_storage.minio.write_client import MinioWriteClient
from typing import Optional
import time
from datetime import datetime
from prometheus_client import CollectorRegistry, Histogram, push_to_gateway

class DataFetcherBase(ABC):
    """Base class for data fetchers with common functionality."""

    def __init__(self, minio_write_client: MinioWriteClient, save_batch_size: int = 100, prometheus_pushgateway_url: Optional[str] = None, metric_origin: Optional[str] = None):
        """
        save_batch_size (int): The number of records to save to MinIO in each batch.
        """
        self.minio_write_client = minio_write_client
        self.save_batch_size = save_batch_size
        self.logged_progress = 0

        # Prometheus configuration
        self.prometheus_pushgateway_url = prometheus_pushgateway_url
        self.metric_registry = CollectorRegistry()
        self.metric_origin = metric_origin
        self.AVERAGE_INGESTION_LATENCY = Histogram(
            'fetcher_average_ingestion_latency_seconds', 
            'Time taken to ingest data', 
            buckets=[5, 10, 20, 40, 80, 160, 320, float("inf")],
            registry=self.metric_registry
        )

    def log_progress(self, data_batch: list[dict]):
        """Logs the progress of data accumulation in 10% increments."""
        current_count = len(data_batch)
        progress_percentage = (current_count / self.save_batch_size) * 100

        # Log progress at each 10% increment
        if progress_percentage >= self.logged_progress + 10:
            self.logged_progress += 10
            logging.info(f"Accumulated {current_count}/{self.save_batch_size} records for saving "
                         f"({progress_percentage:.0f}%)")

    def _build_structured_minio_path(self) -> str:
        """Create a structured path: `year/month/day/HHMMSS.parquet` for saving to MinIO"""
        now = datetime.now()

        year = now.strftime('%Y')
        month = now.strftime('%m')
        day = now.strftime('%d')
        time_str = now.strftime('%H%M%S') + f"{now.microsecond // 1000:03d}"
        filename = f"{time_str}.parquet"
        minio_path = f"{year}/{month}/{day}/{filename}"

        return minio_path

    def save_to_minio(self, data_batch: list[dict], bucket_name: Optional[str] = None, metric_disable: bool = False) -> list[dict]:
        """
        Saves accumulated data to MinIO as a Parquet file. Only save the first `save_batch_size` records.
        return: The remaining data batch after saving.
        """
        if not data_batch:
            return

        logging.info(f"Saving {self.save_batch_size} records to MinIO...")

        self.minio_write_client.upload_table_as_parquet(
            data_batch[:self.save_batch_size], 
            minio_path=self._build_structured_minio_path(),
            bucket_name=bucket_name, 
            metadata={"Record-Count": len(data_batch[:self.save_batch_size])}
        )

        if self.prometheus_pushgateway_url and not metric_disable:
            if all("ingest_start_time" in record for record in data_batch[:self.save_batch_size]):
                ingest_end_time = time.time()
                avg_ingest_time = sum(ingest_end_time - record["ingest_start_time"] for record in data_batch[:self.save_batch_size]) / len(data_batch[:self.save_batch_size])
                self.AVERAGE_INGESTION_LATENCY.observe(avg_ingest_time)
                logging.info(f"Average ingestion time: {avg_ingest_time:.4f} seconds")

                push_to_gateway(self.prometheus_pushgateway_url, job=self.metric_origin, registry=self.metric_registry)
            else:
                logging.error("Ingest start time not found in records")


        logging.info("Data successfully saved to MinIO")

        # Clear the batch after saving
        data_batch = data_batch[self.save_batch_size:]
        self.logged_progress = 0

        return data_batch

    @abstractmethod
    def start(self):
        """Abstract method to start the data fetching process. Must be implemented by subclasses."""
        pass