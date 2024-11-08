import os
import logging
from mempool_data_fetcher import MempoolDataFetcher
from minio_client import MinioClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    """Main function to initialize and start the mempool data fetcher."""
    INFURA_WS_URL = os.getenv("INFURA_WS_URL")
    INFURA_HTTP_URL = os.getenv("INFURA_HTTP_URL")
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
    MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
    MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")
    MINIO_BUCKET = os.getenv("MINIO_BUCKET")

    FETCH_DETAIL_BATCH_SIZE = 10
    SAVE_BATCH_SIZE = 100

    if not INFURA_WS_URL or not INFURA_HTTP_URL or not MINIO_ENDPOINT or not MINIO_ROOT_USER or not MINIO_ROOT_PASSWORD:
        logging.error("Missing required environment variables.")
        return

    minio_client = MinioClient(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ROOT_USER,
        secret_key=MINIO_ROOT_PASSWORD,
        bucket_name=MINIO_BUCKET
    )

    mempool_data_fetcher = MempoolDataFetcher(
        ws_url=INFURA_WS_URL,
        http_url=INFURA_HTTP_URL,
        minio_client=minio_client,
        fetch_detail_batch_size=FETCH_DETAIL_BATCH_SIZE,
        save_batch_size=SAVE_BATCH_SIZE
    )
    mempool_data_fetcher.start()

if __name__ == "__main__":
    main()