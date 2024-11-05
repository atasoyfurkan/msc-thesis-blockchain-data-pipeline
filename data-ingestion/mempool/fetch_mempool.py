import json
import os
import pandas as pd
import requests
import websocket
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Environment variables and constants
INFURA_WS_URL = os.getenv("INFURA_WS_URL")
INFURA_HTTP_URL = os.getenv("INFURA_HTTP_URL")
DATA_DIR = Path("/data/mempool")
SAVE_BATCH_SIZE = 100  # Number of transactions per batch

DATA_DIR.mkdir(parents=True, exist_ok=True)  # Ensure the data directory exists

class MempoolDataFetcher:
    """Fetches Ethereum mempool data from Infura WebSocket API and saves transaction details."""
    
    def __init__(self, ws_url: str, http_url: str, save_dir: Path, batch_size: int = SAVE_BATCH_SIZE):
        self.ws_url = ws_url
        self.http_url = http_url
        self.save_dir = save_dir
        self.batch_size = batch_size
        self.transaction_hashes = []

    def on_message(self, ws, message: str):
        """Processes received WebSocket messages, collecting transaction hashes."""
        data = self._parse_message(message)
        if not data:
            return

        transaction_hash = data.get("params", {}).get("result")
        if transaction_hash:
            self.transaction_hashes.append(transaction_hash)

        if len(self.transaction_hashes) >= self.batch_size:
            self._fetch_and_save_transaction_details()
            self.transaction_hashes.clear()

    def _parse_message(self, message: str) -> dict:
        """Parses JSON messages, handling errors."""
        try:
            return json.loads(message)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode message: {e}")
            return {}

    def _fetch_and_save_transaction_details(self):
        """Fetches transaction details from Infura and saves them in Parquet format."""
        transactions = self._fetch_transaction_details()
        if transactions:
            self._save_to_parquet(transactions)
        
    def _fetch_transaction_details(self) -> list[dict]:
        """Fetches detailed information for each transaction hash."""
        payload = [{"jsonrpc": "2.0", "method": "eth_getTransactionByHash", "params": [tx_hash], "id": idx}
                   for idx, tx_hash in enumerate(self.transaction_hashes)]
        try:
            response = requests.post(self.http_url, json=payload)
            response.raise_for_status()
            return [self._parse_transaction(tx) for tx in response.json() if tx.get("result")]
        except requests.RequestException as e:
            logging.error(f"Failed to fetch transaction details: {e}")
            return []

    def _parse_transaction(self, tx: dict) -> dict:
        """Extracts necessary fields from transaction data."""
        tx_data = tx["result"]
        return {
            "hash": tx_data["hash"],
            "from": tx_data["from"],
            "to": tx_data["to"],
            "value": int(tx_data["value"], 16),
            "gas": int(tx_data["gas"], 16),
            "gasPrice": int(tx_data["gasPrice"], 16),
            "nonce": int(tx_data["nonce"], 16),
            "input": tx_data["input"]
        }

    def _save_to_parquet(self, transactions: list[dict]):
        """Saves transactions to a Parquet file."""
        df = pd.DataFrame(transactions)
        output_path = self.save_dir / f"mempool_{datetime.now().strftime('%Y%m%d%H%M%S')}.parquet"
        try:
            df.to_parquet(output_path, index=False)
            logging.info(f"Saved {len(transactions)} transactions to {output_path}")
        except Exception as e:
            logging.error(f"Failed to save transactions to Parquet: {e}")

    def on_error(self, ws, error: str):
        """Handles WebSocket errors."""
        logging.error(f"WebSocket error: {error}")

    def on_close(self, ws):
        """Logs WebSocket closure."""
        logging.info("WebSocket connection closed")

    def on_open(self, ws):
        """Subscribes to Ethereum newPendingTransactions when WebSocket connection opens."""
        ws.send(json.dumps({
            "jsonrpc": "2.0",
            "method": "eth_subscribe",
            "params": ["newPendingTransactions"],
            "id": 1
        }))
        logging.info("Subscribed to newPendingTransactions")

    def start(self):
        """Begins the WebSocket connection and data collection."""
        ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        ws.run_forever()

def main():
    """Entry point to initialize and start the mempool data fetcher."""
    if not INFURA_WS_URL or not INFURA_HTTP_URL:
        logging.error("Environment variables INFURA_WS_URL and INFURA_HTTP_URL are required.")
        return

    fetcher = MempoolDataFetcher(ws_url=INFURA_WS_URL, http_url=INFURA_HTTP_URL, save_dir=DATA_DIR)
    fetcher.start()

if __name__ == "__main__":
    main()