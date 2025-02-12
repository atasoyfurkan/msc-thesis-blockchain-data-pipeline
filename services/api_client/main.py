from modules.data_access.api_client.client import DataPipelineClient
import logging
import os

logging.basicConfig(level=os.getenv("LOGGING_LEVEL", "INFO"), format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    client = DataPipelineClient()

    # List buckets
    buckets = client.list_buckets()
    print("Buckets:", buckets)

    # List files in a specific bucket
    bucket_name = buckets[0]
    print("Files:", client.list_files(bucket_name))

    # List available dates in a bucket
    dates = client.list_dates(bucket_name)
    print("Dates:", dates)

    # Get table path for a specific date range
    table_path = client.get_table_path(bucket_name, dates=dates)
    print("Table path:", table_path)

    # Execute a query
    query=f"""
    SELECT *
    FROM {table_path}
    """
    query_result = client.query(query=query)
    print(query_result)


if __name__ == "__main__":
    main()