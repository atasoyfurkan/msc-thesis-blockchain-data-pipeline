from pathlib import Path
from minio import Minio
from minio.error import S3Error
import logging

class MinioClient:
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

    def upload_file(self, file_path: Path, object_name: str):
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