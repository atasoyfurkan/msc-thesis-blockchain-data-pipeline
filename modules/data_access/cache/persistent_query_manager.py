import re
import typing
import hashlib
from datetime import datetime, timedelta
import logging

if typing.TYPE_CHECKING:
    from modules.data_storage.minio.write_client import MinioWriteClient

PERSISTENT_QUERY_BUCKET_NAME = "persistent-queries"

class PersistentQueryManager:
    """
    Users can persist their queries results to MinIO for later retrieval.
    This class manages the saving and retrieval of query results.
    """

    def __init__(self, minio_write_client: "MinioWriteClient", retention_days: int):
        self.minio_write_client = minio_write_client
        self.minio_write_client.set_default_bucket(default_bucket_name=PERSISTENT_QUERY_BUCKET_NAME)
        self.minio_write_client.set_retention_days(retention_days=retention_days)
        self.retention_days = retention_days
        
        logging.info(f"Initialized PersistentQueryManager with retention_days={minio_write_client.client.get_bucket_lifecycle(PERSISTENT_QUERY_BUCKET_NAME)}")

    def _clean_query(self, query: str) -> str:
        """Cleans and normalizes an SQL query for safe metadata storage."""
        query = query.strip()  # Remove leading/trailing spaces
        query = re.sub(r'\s+', ' ', query)  # Replace multiple spaces/newlines with a single space
        return query

    def _generate_query_id(self, query: str) -> str:
        return hashlib.md5(query.encode()).hexdigest()

    def _build_metadata_minio_path(self, username: str, query: str) -> str:
        query_id = self._generate_query_id(query)
        return f"{username}/metadata/{query_id}.json"

    def _build_data_minio_path(self, username: str, query: str) -> str:
        query_id = self._generate_query_id(query)
        return f"{username}/data/{query_id}.parquet"

    def _build_metadata(self, query: str, retention_days: int, username: str, data_size_mb: float) -> dict:
        return {
            "id": self._generate_query_id(query),
            "query": query,
            "owner": username,
            "result_size_mb": data_size_mb,
            "retention_days": retention_days,
            "expires_at": (datetime.now() + timedelta(days=retention_days)).isoformat(),
            "created_at": datetime.now().isoformat(),
        }

    def persist(self, df, query: str, username: str):
        """
        Persist the query results to MinIO with metadata.
        """
        query = self._clean_query(query)

        data_minio_path = self._build_data_minio_path(username, query)
        data_size_mb = self.minio_write_client.upload_df_as_parquet(df=df, minio_path=data_minio_path, metadata={"Query": query, "Retention-Days": self.retention_days})
        
        if data_size_mb:
            # Save metadata if the data was saved successfully
            metadata = self._build_metadata(query=query, retention_days=self.retention_days, username=username, data_size_mb=data_size_mb)
            metadata_minio_path = self._build_metadata_minio_path(username, query)
            self.minio_write_client.upload_json(json_data=metadata, minio_path=metadata_minio_path)
