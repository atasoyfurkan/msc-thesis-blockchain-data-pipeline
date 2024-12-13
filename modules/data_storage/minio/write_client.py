from pathlib import Path
from minio import Minio
from minio.error import S3Error
import pandas as pd
import logging
from datetime import datetime

class MinioWriteClient:
    """Handles interactions with MinIO for storing Parquet files."""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket_name: str):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )
        self.bucket_name = bucket_name
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Ensure that the bucket exists, if not, create it."""
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)
            logging.info(f"Created bucket: {self.bucket_name}")

    def _upload_file(self, file_path: Path, object_name: str):
        """Upload a file to the specified bucket."""
        try:
            self.client.fput_object(
                self.bucket_name,
                object_name,
                str(file_path)
            )
            logging.info(f"Uploaded {object_name} to MinIO bucket {self.bucket_name}")
        except S3Error as e:
            logging.error(f"Failed to upload to MinIO: {e}")

    def upload_table_as_parquet(self, table: list[dict]):
        """
        Saves the DataFrame as a Parquet file and uploads it to MinIO
        using a structured directory format.
        """
        df = pd.DataFrame(table)
        # Generate the current timestamp
        now = datetime.now()

        # Create the structured path: `year/month/day/HHMMSS.parquet`
        year = now.strftime('%Y')
        month = now.strftime('%m')
        day = now.strftime('%d')
        time_str = now.strftime('%H%M%S')
        filename = f"{time_str}.parquet"
        minio_path = f"{year}/{month}/{day}/{filename}"

        # Temporary local file path
        temp_file = Path("/tmp") / filename

        try:
            # Save DataFrame to a Parquet file locally
            df.to_parquet(temp_file, index=False)

            # Upload the Parquet file to MinIO
            self._upload_file(temp_file, minio_path)

            # Remove the local file after uploading
            temp_file.unlink()
            logging.info(f"Saved DataFrame to MinIO at {minio_path}")
        except Exception as e:
            logging.error(f"Failed to save DataFrame to MinIO: {e}")