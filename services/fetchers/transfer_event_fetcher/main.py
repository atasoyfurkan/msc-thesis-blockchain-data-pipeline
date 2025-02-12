import os
import logging
import json
from modules.data_ingestion.transfer_event.fetcher import TransferEventDataFetcher
from modules.data_storage.minio.write_client import MinioWriteClient

logging.basicConfig(level=os.getenv("LOGGING_LEVEL", "INFO"), format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    """Main function to initialize and start the mempool data fetcher."""
    NODE_WS_URL = os.getenv("NODE_WS_URL")
    NODE_HTTP_URL = os.getenv("NODE_HTTP_URL")
    SAVE_BATCH_SIZE = int(os.getenv("SAVE_BATCH_SIZE"))
    PROMETHEUS_PUSHGATEWAY_URL = os.getenv("PROMETHEUS_PUSHGATEWAY_URL")

    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
    MINIO_BUCKET = os.getenv("MINIO_BUCKET")
    MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
    MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")

    try:
        with open("token_configurations.json", "r") as config_file:
            TOKEN_CONFIGURATIONS = json.load(config_file)["token_configurations"]
        logging.debug(f"Loaded token configurations: {TOKEN_CONFIGURATIONS}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error reading token configurations: {e}")
        return

    if not NODE_WS_URL or not NODE_HTTP_URL or not MINIO_ENDPOINT or not MINIO_ROOT_USER or not MINIO_ROOT_PASSWORD or not MINIO_BUCKET:
        logging.error("Missing required environment variables.")
        return

    minio_write_client = MinioWriteClient(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ROOT_USER,
        secret_key=MINIO_ROOT_PASSWORD,
        default_bucket_name=MINIO_BUCKET
    )

    mempool_data_fetcher = TransferEventDataFetcher(
        minio_write_client=minio_write_client,
        ws_url=NODE_WS_URL,
        http_url=NODE_HTTP_URL,
        token_configurations=TOKEN_CONFIGURATIONS,
        save_batch_size=SAVE_BATCH_SIZE,
        prometheus_pushgateway_url=PROMETHEUS_PUSHGATEWAY_URL
    )
    mempool_data_fetcher.start()

if __name__ == "__main__":
    main()