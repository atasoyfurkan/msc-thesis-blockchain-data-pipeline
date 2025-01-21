import json
import logging
import requests
import websocket
from typing import Optional
from modules.data_storage.minio.write_client import MinioWriteClient
from modules.data_ingestion.base_fetcher import DataFetcherBase
from modules.data_ingestion.parsers import parse_block_header, parse_block
from modules.data_ingestion.extractors import extract_ethereum_node_ws_message

class BlockDataFetcher(DataFetcherBase):
    """Fetches Ethereum mempool transaction data and saves transaction details to MinIO."""

    def __init__(self, minio_write_client: MinioWriteClient, ws_url: str, http_url: str, bucket_name_header: str, bucket_name: str, save_batch_size: int = 10):
        super().__init__(minio_write_client=minio_write_client, save_batch_size=save_batch_size)
        self.ws_url = ws_url
        self.http_url = http_url
        self.bucket_name_header = bucket_name_header
        self.bucket_name = bucket_name
        self.data_batch_block_headers: list[dict] = []
        self.data_batch_blocks: list[dict] = []

    def on_message(self, ws, message: str):
        """Handle incoming WebSocket messages."""
        logging.debug(f"Received websocket message: {message}")
        
        block_header = extract_ethereum_node_ws_message(message)
        if block_header:
            parsed_block_header = parse_block_header(block_header)
            self.data_batch_block_headers.append(parsed_block_header)

            block = parse_block(self._fetch_block(block_hash=parsed_block_header["hash"]))
            if block:
                self.data_batch_blocks.append(block)

        self.log_progress(data_batch=self.data_batch_block_headers)

        if len(self.data_batch_block_headers) >= self.save_batch_size:
            self.data_batch_block_headers = self.save_to_minio(data_batch=self.data_batch_block_headers, bucket_name=self.bucket_name_header)

        if len(self.data_batch_blocks) >= self.save_batch_size:
            self.data_batch_blocks = self.save_to_minio(data_batch=self.data_batch_blocks, bucket_name=self.bucket_name)

    def _fetch_block(self, block_hash: str) -> Optional[dict]:
        """Fetches the latest block number from the Ethereum node."""
        try:
            response = requests.post(self.http_url, json={"jsonrpc": "2.0", "method": "eth_getBlockByHash", "params": [block_hash, True], "id": 1})
            response.raise_for_status()
            response_json = response.json()

            if "result" not in response_json:
                logging.warning(f"Invalid response format for fetching block: {response_json}")
                return None

            return response_json["result"]
        except requests.RequestException as e:
            logging.error(f"Failed to fetch block: {e}")
            return None

    def on_error(self, ws, error: str):
        """Handles WebSocket errors."""
        logging.error(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        """Logs when the WebSocket connection is closed."""
        logging.info(f"WebSocket connection closed with status code: {close_status_code} and message: {close_msg}")

    def on_open(self, ws):
        """Subscribes to new pending transactions on WebSocket connection open."""
        ws.send(json.dumps({
            "jsonrpc": "2.0",
            "method": "eth_subscribe",
            "params": ["newHeads"],
            "id": 1
        }))
        logging.info("Subscribed to newHeads")

    def start(self):
        """Starts the WebSocket connection and begins data collection."""
        ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        ws.run_forever()
