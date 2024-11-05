import json
import os
import pandas as pd
import requests
import websocket
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Environment variables and constants
INFURA_WS_URL = os.getenv("INFURA_WS_URL")
INFURA_HTTP_URL = os.getenv("INFURA_HTTP_URL")
DATA_DIR = Path("/data/mempool")
DATA_DIR.mkdir(parents=True, exist_ok=True)  # Ensure the data directory exists

# Global configuration for batch sizes
FETCH_DETAIL_BATCH_SIZE = 10  # Number of transaction details to fetch at once (for rate limiting)
SAVE_BATCH_SIZE = 1000        # Number of transactions to accumulate before saving (for storing in different files)

class MempoolDataFetcher:
    """Fetches Ethereum mempool transaction data and saves transaction details."""

    def __init__(self, ws_url: str, http_url: str, save_dir: Path, fetch_detail_batch_size: int = FETCH_DETAIL_BATCH_SIZE, save_batch_size: int = SAVE_BATCH_SIZE):
        self.ws_url = ws_url
        self.http_url = http_url
        self.save_dir = save_dir
        self.fetch_detail_batch_size = fetch_detail_batch_size
        self.save_batch_size = save_batch_size
        self.transaction_hashes = []
        self.transaction_details = []
        self.logged_progress = 0  # Track last logged percentage (for debugging)

    def on_message(self, ws, message: str):
        """Handle incoming messages from the WebSocket."""
        transaction_hash = self._extract_transaction_hash(message)
        if transaction_hash:
            self.transaction_hashes.append(transaction_hash)

        # Fetch transaction details in batches
        if len(self.transaction_hashes) >= self.fetch_detail_batch_size:
            self._fetch_transaction_details()
            self.transaction_hashes.clear()
        
        self._log_progress()

        # Save accumulated transactions in SAVE_BATCH_SIZE batches
        if len(self.transaction_details) >= self.save_batch_size:
            self._save_to_parquet(self.transaction_details[:self.save_batch_size])
            self.transaction_details = self.transaction_details[self.save_batch_size:]
            self.logged_progress = 0  # Reset logged progress after saving

    def _extract_transaction_hash(self, message: str) -> Optional[str]:
        """Extracts the transaction hash from the WebSocket message."""
        try:
            data = json.loads(message)
            return data.get("params", {}).get("result")
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode message: {e}")
            return None

    def _fetch_transaction_details(self):
        """Fetches transaction details for a batch of transaction hashes."""
        payload = [
            {"jsonrpc": "2.0", "method": "eth_getTransactionByHash", "params": [tx_hash], "id": idx}
            for idx, tx_hash in enumerate(self.transaction_hashes)
        ]
        try:
            response = requests.post(self.http_url, json=payload)
            response.raise_for_status()
            for tx in response.json():
                if tx.get("result"):
                    self.transaction_details.append(self._parse_transaction(tx["result"]))
        except requests.RequestException as e:
            logging.error(f"Failed to fetch transaction details: {e}")

    @staticmethod
    def _parse_transaction(tx: dict) -> dict:
        """Extracts relevant transaction fields and converts large integers to strings."""
        return {
            "hash": tx["hash"],
            "from": tx["from"],
            "to": tx.get("to"),
            "value": str(int(tx["value"], 16)),
            "gas": int(tx["gas"], 16),
            "gasPrice": int(tx["gasPrice"], 16),
            "nonce": int(tx["nonce"], 16),
            "input": tx["input"]
        }

    def _save_to_parquet(self, transactions: List[dict]):
        """Saves transactions to a Parquet file."""
        df = pd.DataFrame(transactions)
        filename = self.save_dir / f"mempool_{datetime.now().strftime('%Y%m%d%H%M%S')}.parquet"
        try:
            df.to_parquet(filename, index=False)
            logging.info(f"Saved {len(transactions)} transactions to {filename}")
        except Exception as e:
            logging.error(f"Failed to save transactions to Parquet: {e}")

    def _log_progress(self):
        """Logs the progress of transactions accumulation in 10% increments of save_batch_size."""
        current_count = len(self.transaction_details)
        progress_percentage = (current_count / self.save_batch_size) * 100

        # Check if progress reached the next 10% increment
        if progress_percentage >= self.logged_progress + 10:
            self.logged_progress += 10
            logging.info(f"Accumulated {current_count}/{self.save_batch_size} transactions for saving "
                          f"({progress_percentage:.0f}%)")


    def on_error(self, ws, error: str):
        """Handles WebSocket errors."""
        logging.error(f"WebSocket error: {error}")

    def on_close(self, ws):
        """Logs when the WebSocket connection is closed."""
        logging.info("WebSocket connection closed")

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

def main():
    """Main function to initialize and start the mempool data fetcher."""
    if not INFURA_WS_URL or not INFURA_HTTP_URL:
        logging.error("Environment variables INFURA_WS_URL and INFURA_HTTP_URL are required.")
        return

    fetcher = MempoolDataFetcher(
        ws_url=INFURA_WS_URL,
        http_url=INFURA_HTTP_URL,
        save_dir=DATA_DIR
    )
    fetcher.start()

if __name__ == "__main__":
    main()