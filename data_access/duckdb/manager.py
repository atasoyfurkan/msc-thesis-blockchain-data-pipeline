import duckdb
import logging
from datetime import datetime, timedelta

class DuckDBManager:
    """Handles querying Parquet files stored in MinIO using DuckDB."""

    def __init__(self, minio_read_client):
        self.minio_read_client = minio_read_client

    def _configure_duckdb_connection(self):
        """Configures DuckDB to connect to MinIO."""
        conn = duckdb.connect()
        conn.execute(f"""
            SET s3_endpoint='{self.minio_read_client.endpoint}';
            SET s3_access_key_id='{self.minio_read_client.access_key}';
            SET s3_secret_access_key='{self.minio_read_client.secret_key}';
            SET s3_use_ssl=false;
            SET s3_url_style='path';
        """)
        return conn

    def query_parquet(self, query):
        """
        Queries a Parquet file stored in MinIO using DuckDB.
        Filters rows where gasPrice is above the threshold.
        """
        conn = self._configure_duckdb_connection()
        try:
            result_df = conn.execute(query).fetchdf()
            return result_df
        except Exception as e:
            logging.error(f"Failed to query Parquet file: {e}")
            return None
        finally:
            conn.close()

    def get_table(self, bucket_name: str, file_name: str):
        """
        This function is for testing purposes only and no practical use.
        """
        return f"read_parquet('s3://{bucket_name}/{file_name}')"

    def get_tables_with_dates(self, bucket_name: str, dates: list[str]) -> str:
        """
        Generate a list of S3 paths for the given date range.
        Expects dates in 'YYYY/MM/DD' format.
        """
        s3_paths = []
        for date in dates:
            year, month, day = date.split('/')
            if self.minio_read_client.is_prefix_exist(bucket_name, f"{year}/{month}/{day}"):
                s3_paths.append(f"s3://{bucket_name}/{year}/{month}/{day}/*.parquet")
        
        return f"read_parquet({s3_paths}, union_by_name=True)"

    def get_tables_with_range(self, bucket_name: str, start_date: str, end_date: str) -> str:
        """
        Generate a list of S3 paths for the given date range.
        Expects dates in 'YYYY/MM/DD' format.
        """
        # Parse the input dates
        start_dt = datetime.strptime(start_date, "%Y/%m/%d")
        end_dt = datetime.strptime(end_date, "%Y/%m/%d")

        dates = []
        current_date = start_dt

        while current_date <= end_dt:
            dates.append(current_date.strftime("%Y/%m/%d"))
            current_date += timedelta(days=1)
        
        return self.get_tables_with_dates(bucket_name, dates)
