import logging
from abc import ABC, abstractmethod
from data_storage.minio.write_client import MinioWriteClient

class DataFetcherBase(ABC):
    """Base class for data fetchers with common functionality."""

    def __init__(self, minio_write_client: MinioWriteClient, save_batch_size: int = 100):
        """
        save_batch_size (int): The number of records to save to MinIO in each batch.
        """
        self.minio_write_client = minio_write_client
        self.save_batch_size = save_batch_size
        self.data_batch: list[dict] = []
        self.logged_progress = 0

    def log_progress(self):
        """Logs the progress of data accumulation in 10% increments."""
        current_count = len(self.data_batch)
        progress_percentage = (current_count / self.save_batch_size) * 100

        # Log progress at each 10% increment
        if progress_percentage >= self.logged_progress + 10:
            self.logged_progress += 10
            logging.info(f"Accumulated {current_count}/{self.save_batch_size} records for saving "
                         f"({progress_percentage:.0f}%)")

    def save_to_minio(self):
        """
        Saves accumulated data to MinIO as a Parquet file.
        """
        if not self.data_batch:
            return

        logging.info(f"Saving {self.save_batch_size} records to MinIO...")

        self.minio_write_client.upload_table_as_parquet(self.data_batch[:self.save_batch_size])

        logging.info("Data successfully saved to MinIO")

        # Clear the batch after saving
        self.data_batch = self.data_batch[self.save_batch_size:]
        self.logged_progress = 0

    @abstractmethod
    def start(self):
        """Abstract method to start the data fetching process. Must be implemented by subclasses."""
        pass