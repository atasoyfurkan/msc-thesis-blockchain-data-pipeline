from minio import Minio
from minio.error import S3Error
import logging

class MinioReadClient:

    def __init__(self, endpoint: str, access_key: str, secret_key: str):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=False
        )

    def list_buckets(self) -> list[str]:
        """List all buckets in the MinIO server."""
        try:
            buckets = self.client.list_buckets()
            return [bucket.name for bucket in buckets]
        except S3Error as e:
            logging.error(f"Failed to list buckets: {e}")
            return []

    def list_objects(self, bucket_name: str) -> list[dict]:
        """
        List all objects in the given bucket and return their basic info.
        """
        try:
            objects_info = []
            for obj in self.client.list_objects(bucket_name, recursive=True):
                objects_info.append({
                    "object_name": obj.object_name,
                    "size": obj.size
                })
            return objects_info
        except S3Error as e:
            logging.error(f"Failed to list objects in bucket {bucket_name}: {e}")
            return []
        
    def is_prefix_exist(self, bucket_name: str, prefix: str) -> bool:
        """Check if the given prefix exists in the bucket."""
        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix)
            return any(objects)
        except S3Error as e:
            logging.error(f"Failed to list objects in bucket {bucket_name}: {e}")
            return False
    
    def list_dates(self, bucket_name: str) -> list[str]:
        """List all date folders (year/month/day) in the specified bucket."""
        date_folders = []
        try:
            # Step 1: List top-level folders (years)
            year_prefixes = self.client.list_objects(bucket_name, prefix='', recursive=False)
                        
            for year_prefix in year_prefixes:
                # Step 2: List second-level folders (months)
                month_prefixes = self.client.list_objects(bucket_name, prefix=f"{year_prefix.object_name}", recursive=False)
                
                for month_prefix in month_prefixes:
                    # Step 3: List third-level folders (days)
                    day_prefixes = self.client.list_objects(bucket_name, prefix=f"{month_prefix.object_name}", recursive=False)
                    date_folders.extend([day_prefix.object_name[:-1] for day_prefix in day_prefixes]) # Remove trailing slash
            
            return date_folders

        except S3Error as e:
            logging.error(f"Failed to list date folders in bucket {bucket_name}: {e}")
            return []
