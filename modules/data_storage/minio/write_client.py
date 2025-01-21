from pathlib import Path
from minio import Minio
from minio.error import S3Error
import pandas as pd
import logging
from datetime import datetime
from typing import Optional

class MinioWriteClient:
    """Handles interactions with MinIO for storing Parquet files."""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, default_bucket_name: Optional[str] = None):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )
        self.cached_buckets: set[str] = set(self.client.list_buckets())
        if default_bucket_name:
            self.default_bucket_name = default_bucket_name
            self._ensure_bucket_exists(bucket_name=self.default_bucket_name)

    def _ensure_bucket_exists(self, bucket_name: str):
        """Ensure that the bucket exists, if not, create it."""
        if bucket_name not in self.cached_buckets and not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
            self.cached_buckets.add(bucket_name)
            logging.info(f"Created bucket: {bucket_name}")

    def _get_bucket_name(self, bucket_name: Optional[str] = None) -> str:
        """Get the bucket name, using the default if not specified."""
        if not bucket_name and not self.default_bucket_name:
            raise ValueError("No default bucket specified. Bucket name must be provided.")

        bucket_name = bucket_name or self.default_bucket_name
        self._ensure_bucket_exists(bucket_name)

        return bucket_name

    def _upload_file(self, file_path: Path, object_name: str, bucket_name: Optional[str] = None, metadata: dict = {}):
        """Upload a file to the specified bucket."""
        bucket_name = self._get_bucket_name(bucket_name)
        try:
            self.client.fput_object(
                bucket_name,
                object_name,
                str(file_path),
                metadata=metadata
            )
            logging.info(f"Uploaded {object_name} to MinIO bucket {bucket_name} with metadata: {metadata}")
        except S3Error as e:
            logging.error(f"Failed to upload to MinIO: {e}")

    def upload_table_as_parquet(self, table: list[dict], bucket_name: Optional[str] = None, metadata: dict = {}):
        """
        Saves the DataFrame as a Parquet file and uploads it to MinIO
        using a structured directory format.
        """
        bucket_name = self._get_bucket_name(bucket_name)

        df = pd.DataFrame(table)
        # Generate the current timestamp
        now = datetime.now()

        # Create the structured path: `year/month/day/HHMMSS.parquet`
        year = now.strftime('%Y')
        month = now.strftime('%m')
        day = now.strftime('%d')
        time_str = now.strftime('%H%M%S') + f"{now.microsecond // 1000:03d}"
        filename = f"{time_str}.parquet"
        minio_path = f"{year}/{month}/{day}/{filename}"

        # Temporary local file path
        temp_file = Path("/tmp") / filename

        try:
            # Save DataFrame to a Parquet file locally
            df.to_parquet(temp_file, index=False)

            # Upload the Parquet file to MinIO
            self._upload_file(temp_file, minio_path, bucket_name, metadata=metadata)

            # Remove the local file after uploading
            temp_file.unlink()
            logging.info(f"Saved DataFrame to MinIO at {minio_path}")
        except Exception as e:
            logging.error(f"Failed to save DataFrame to MinIO: {e}")