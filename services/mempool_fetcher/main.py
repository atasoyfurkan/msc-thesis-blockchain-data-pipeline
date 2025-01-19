import os
import logging
from modules.data_ingestion.mempool.fetcher import MempoolDataFetcher
from modules.data_storage.minio.write_client import MinioWriteClient

logging.basicConfig(level=os.getenv("LOGGING_LEVEL", "INFO"), format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    """Main function to initialize and start the mempool data fetcher."""
    NODE_WS_URL = os.getenv("NODE_WS_URL")
    NODE_HTTP_URL = os.getenv("NODE_HTTP_URL")
    FETCH_DETAIL_BATCH_SIZE = int(os.getenv("FETCH_DETAIL_BATCH_SIZE"))
    SAVE_BATCH_SIZE = int(os.getenv("SAVE_BATCH_SIZE"))

    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
    MINIO_BUCKET = os.getenv("MINIO_BUCKET")
    MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
    MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")

    if not NODE_WS_URL or not NODE_HTTP_URL or not MINIO_ENDPOINT or not MINIO_ROOT_USER or not MINIO_ROOT_PASSWORD or not MINIO_BUCKET:
        logging.error("Missing required environment variables.")
        return

    minio_write_client = MinioWriteClient(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ROOT_USER,
        secret_key=MINIO_ROOT_PASSWORD,
        default_bucket_name=MINIO_BUCKET
    )

    mempool_data_fetcher = MempoolDataFetcher(
        minio_write_client=minio_write_client,
        ws_url=NODE_WS_URL,
        http_url=NODE_HTTP_URL,
        fetch_detail_batch_size=FETCH_DETAIL_BATCH_SIZE,
        save_batch_size=SAVE_BATCH_SIZE
    )
    mempool_data_fetcher.start()

if __name__ == "__main__":
    main()