from pathlib import Path
from minio import Minio
from minio.error import S3Error
from minio.lifecycleconfig import LifecycleConfig, Expiration, Rule
import pandas as pd
import logging
from typing import Optional
import tempfile
import json
import os

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
            self.set_default_bucket(default_bucket_name=default_bucket_name)

    def _ensure_bucket_exists(self, bucket_name: str):
        """Ensure that the bucket exists, if not, create it."""
        if bucket_name not in self.cached_buckets and not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
            self.cached_buckets.add(bucket_name)
            logging.info(f"Created bucket: {bucket_name}")

    def set_default_bucket(self, default_bucket_name: str):
        self.default_bucket_name = default_bucket_name
        self._ensure_bucket_exists(default_bucket_name)
    
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
            raise e

    def upload_df_as_parquet(self, df: pd.DataFrame, minio_path: str, bucket_name: Optional[str] = None, metadata: dict = {}) -> Optional[float]:
        """
        Saves the DataFrame as a Parquet file and uploads it to MinIO
        using the specified path.
        """
        bucket_name = self._get_bucket_name(bucket_name)

        try:
            with tempfile.NamedTemporaryFile(suffix=".parquet", delete=True) as temp_file:
                temp_file_path = temp_file.name
                # Save DataFrame to a Parquet file locally
                df.to_parquet(temp_file_path, index=False)
                file_size_mb = os.path.getsize(temp_file_path) / (1024 * 1024)

                # Upload the Parquet file to MinIO
                self._upload_file(temp_file_path, minio_path, bucket_name, metadata=metadata)

            logging.info(f"Saved DataFrame to MinIO at {minio_path}")

            return file_size_mb
        except Exception as e:
            logging.error(f"Failed to save DataFrame to MinIO: {e}")


    def upload_table_as_parquet(self, table: list[dict], minio_path: str, bucket_name: Optional[str] = None, metadata: dict = {}) -> Optional[float]:
        """
        Saves the DataFrame as a Parquet file and uploads it to MinIO
        """
        df = pd.DataFrame(table)
        return self.upload_df_as_parquet(df=df, minio_path=minio_path, bucket_name=bucket_name, metadata=metadata)

    def upload_json(self, json_data: dict, minio_path: str, bucket_name: Optional[str] = None, metadata: dict = {}):
        """
        Uploads a JSON-serializable dictionary to MinIO as a JSON file.
        """
        bucket_name = self._get_bucket_name(bucket_name)

        try:
            with tempfile.NamedTemporaryFile(suffix=".json", delete=True) as temp_file:
                temp_file_path = temp_file.name
                with open(temp_file_path, "w") as f:
                    json.dump(json_data, f)

                self._upload_file(temp_file_path, minio_path, bucket_name, metadata=metadata)

            logging.info(f"Uploaded JSON to MinIO at {minio_path}")
        except Exception as e:
            logging.error(f"Failed to upload JSON to MinIO: {e}")

    def set_retention_days(self, retention_days: int, bucket_name: Optional[str] = None):
        """Set the default retention days for objects in the bucket. They will be deleted after this period."""
        rule = Rule(
            rule_id="expire-objects-after-{}-days".format(retention_days),  # Unique rule ID
            status="Enabled",
            expiretion=Expiration(days=retention_days),
        )
        lifecycle_config = LifecycleConfig([rule])
        bucket_name = self._get_bucket_name(bucket_name)

        try:
            self.client.set_bucket_lifecycle(bucket_name, lifecycle_config)
            logging.info(f"Set retention days for bucket {bucket_name} to {retention_days}")
        except S3Error as e:
            logging.error(f"Failed to set retention days for bucket {bucket_name}: {e}")
            raise e
