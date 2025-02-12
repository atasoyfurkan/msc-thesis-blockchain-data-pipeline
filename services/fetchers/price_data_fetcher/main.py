import os
import logging
from modules.data_ingestion.price_data.fetcher import PriceDataFetcher
from modules.data_storage.minio.write_client import MinioWriteClient

logging.basicConfig(level=os.getenv("LOGGING_LEVEL", "INFO"), format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    """Main function to initialize and start the mempool data fetcher."""
    BINANCE_URL = os.getenv("BINANCE_URL")
    TOKEN_SYMBOLS = os.getenv("TOKEN_SYMBOLS").split(",")
    PRICE_DATA_SOURCE = os.getenv("PRICE_DATA_SOURCE")
    FETCH_INTERVAL_SECOND = float(os.getenv("FETCH_INTERVAL_SECOND"))
    SAVE_BATCH_SIZE = int(os.getenv("SAVE_BATCH_SIZE"))
    PROMETHEUS_PUSHGATEWAY_URL = os.getenv("PROMETHEUS_PUSHGATEWAY_URL")

    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
    MINIO_BUCKET = os.getenv("MINIO_BUCKET")
    MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
    MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")

    if not BINANCE_URL or not TOKEN_SYMBOLS or not PRICE_DATA_SOURCE or not MINIO_ENDPOINT or not MINIO_ROOT_USER or not MINIO_ROOT_PASSWORD or not MINIO_BUCKET:
        logging.error("Missing required environment variables.")
        return

    minio_write_client = MinioWriteClient(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ROOT_USER,
        secret_key=MINIO_ROOT_PASSWORD,
        default_bucket_name=MINIO_BUCKET
    )

    price_data_fetcher = PriceDataFetcher(
        minio_write_client=minio_write_client,
        url=BINANCE_URL,
        symbols=TOKEN_SYMBOLS,
        source=PRICE_DATA_SOURCE,
        fetch_interval_second=FETCH_INTERVAL_SECOND,
        save_batch_size=SAVE_BATCH_SIZE,
        prometheus_pushgateway_url=PROMETHEUS_PUSHGATEWAY_URL
    )
    price_data_fetcher.start()

if __name__ == "__main__":
    main()