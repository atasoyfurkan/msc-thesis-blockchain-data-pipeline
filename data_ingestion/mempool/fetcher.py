import json
import logging
import requests
import websocket
from datetime import datetime
from typing import Optional
from data_storage.minio.write_client import MinioWriteClient
from data_ingestion.base_fetcher import DataFetcherBase

class MempoolDataFetcher(DataFetcherBase):
    """Fetches Ethereum mempool transaction data and saves transaction details to MinIO."""

    def __init__(self, minio_write_client: MinioWriteClient, ws_url: str, http_url: str, fetch_detail_batch_size: int = 10, save_batch_size: int = 100):
        super().__init__(minio_write_client=minio_write_client, save_batch_size=save_batch_size)
        self.ws_url = ws_url
        self.http_url = http_url
        self.fetch_detail_batch_size = fetch_detail_batch_size
        self.transaction_hashes = []

    def on_message(self, ws, message: str):
        """Handle incoming WebSocket messages."""
        transaction_hash = self._extract_transaction_hash(message)
        if transaction_hash:
            self.transaction_hashes.append(transaction_hash)

        if len(self.transaction_hashes) >= self.fetch_detail_batch_size:
            self._fetch_transaction_details()
            self.transaction_hashes.clear()

        self.log_progress()

        if len(self.data_batch) >= self.save_batch_size:
            self.save_to_minio()

    def _extract_transaction_hash(self, message: str) -> Optional[str]:
        """Extracts the transaction hash from the WebSocket message."""
        try:
            data = json.loads(message)

            if "error" in data:
                logging.error(f"Error response: {data['error']}")
                return None

            return data.get("params", {}).get("result")
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode message: {e}")
            return None

    def _fetch_transaction_details(self):
        """Fetches transaction details for a batch of transaction hashes."""
        payload = [{"jsonrpc": "2.0", "method": "eth_getTransactionByHash", "params": [tx_hash], "id": idx}
                   for idx, tx_hash in enumerate(self.transaction_hashes)]
        try:
            response = requests.post(self.http_url, json=payload)
            response.raise_for_status()
            for tx in response.json():
                if tx.get("result"):
                    transaction_detail = self._parse_transaction(tx["result"])
                    logging.debug(f"Fetched transaction detail: {transaction_detail}")
                    self.data_batch.append(transaction_detail)
        except requests.RequestException as e:
            logging.error(f"Failed to fetch transaction details: {e}")

    @staticmethod
    def _parse_transaction(tx: dict) -> dict:
        """Extracts relevant fields from transaction data."""
        return {
            "hash": tx["hash"],
            "from": tx["from"],
            "to": tx.get("to"),
            "value": str(int(tx["value"], 16)),
            "gas": int(tx["gas"], 16),
            "gas_price": int(tx["gasPrice"], 16),
            "nonce": int(tx["nonce"], 16),
            "input": tx["input"],
            "fetched_at": datetime.now().isoformat()
        }
    
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
            "params": ["newPendingTransactions"],
            "id": 1
        }))
        logging.info("Subscribed to newPendingTransactions")

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
