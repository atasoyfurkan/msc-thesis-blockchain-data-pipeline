import os
import logging
from data_storage.minio.read_client import MinioReadClient
from data_access.duckdb.manager import DuckDBManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
    MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
    MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")

    if not MINIO_ENDPOINT or not MINIO_ROOT_USER or not MINIO_ROOT_PASSWORD:
        logging.error("Missing required environment variables.")
        return

    minio_read_client = MinioReadClient(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ROOT_USER,
        secret_key=MINIO_ROOT_PASSWORD
    )

    buckets = minio_read_client.list_buckets()
    objects = minio_read_client.list_objects(bucket_name=buckets[0])
    logging.info(f"Found buckets: {buckets}")

    dates = minio_read_client.list_dates(bucket_name=buckets[0])

    logging.info(f"Found dates: {dates}")

    duckdb_manager = DuckDBManager(
        minio_read_client=minio_read_client
    )

    # tables = duckdb_manager.get_tables_with_range(
    #     bucket_name=buckets[0],
    #     start_date="2024/11/10",
    #     end_date="2024/11/13"
    # )

    tables = duckdb_manager.get_tables_with_dates(
        bucket_name=buckets[0],
        dates=["2024/11/10", "2024/11/11", "2024/11/12"]
    )

    logging.info(f"FROM tables: {tables}")

    query = f"SELECT * FROM {tables} WHERE fetched_at IS NULL"
    result_df = duckdb_manager.query(query)

    logging.info(f"Query result: {result_df}")


    

if __name__ == "__main__":
    main()