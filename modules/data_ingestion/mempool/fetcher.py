import json
import logging
import requests
import websocket
from datetime import datetime
from typing import Optional
from modules.data_storage.minio.write_client import MinioWriteClient
from modules.data_ingestion.base_fetcher import DataFetcherBase

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
        logging.debug(f"Received websocket message: {message}")
        
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

            if not isinstance(data, dict):
                logging.warning(f"Invalid message format: {data}")
                return None

            if "error" in data:
                logging.error(f"Error response: {data['error']}")
                return None
            
            if "params" not in data:
                logging.warning(f"Missing 'params' in data: {data}")
                return None

            params = data["params"]
            if not isinstance(params, dict) or "result" not in params:
                logging.warning(f"Missing 'result' in params: {params}")
                return None
            
            return params["result"]
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode message: {e}")
            return None

    def _fetch_transaction_details(self):
        """Fetches transaction details for a batch of transaction hashes."""
        try:
            latest_block = self._fetch_latest_block()

            payload = [{"jsonrpc": "2.0", "method": "eth_getTransactionByHash", "params": [tx_hash], "id": idx}
                   for idx, tx_hash in enumerate(self.transaction_hashes)]
            response = requests.post(self.http_url, json=payload)
            response.raise_for_status()
            response_json = response.json()

            if not isinstance(response_json, list):
                logging.warning(f"Invalid response format for fetching transaction detail: {response_json}")
                return

            for tx in response_json:
                logging.debug(f"Fetched transaction detail: {tx}")

                if isinstance(tx, dict) and "result" in tx and isinstance(tx["result"], dict):
                    transaction_detail = self._parse_transaction(tx["result"], latest_block)
                    logging.debug(f"Parsed transaction detail: {transaction_detail}")
                    self.data_batch.append(transaction_detail)
        except requests.RequestException as e:
            logging.error(f"Failed to fetch transaction details: {e}")

    def _fetch_latest_block(self) -> Optional[dict]:
        """Fetches the latest block number from the Ethereum node."""
        try:
            response = requests.post(self.http_url, json={"jsonrpc": "2.0", "method": "eth_getBlockByNumber", "params": ["latest", False], "id": 1})
            response.raise_for_status()
            response_json = response.json()

            if "result" not in response_json:
                logging.warning(f"Invalid response format for fetching latest block: {response_json}")
                return None

            return response_json["result"]
        except requests.RequestException as e:
            logging.error(f"Failed to fetch latest block: {e}")
            return None

    @staticmethod
    def _parse_transaction(tx: dict, latest_block: Optional[dict]) -> dict:
        """Extracts relevant fields from transaction data."""
        transaction = {
            "hash": tx["hash"],
            "from": tx["from"],
            "to": tx.get("to"),
            "type": int(tx["type"], 16) if "type" in tx else None,
            "chain_id": int(tx["chainId"], 16) if "chainId" in tx else None,
            "value": str(int(tx["value"], 16)),
            "gas": int(tx["gas"], 16),
            "gas_price": int(tx["gasPrice"], 16) if "gasPrice" in tx else None,
            "max_fee_per_gas": int(tx["maxFeePerGas"], 16) if "maxFeePerGas" in tx else None,
            "max_priority_fee_per_gas": int(tx["maxPriorityFeePerGas"], 16) if "maxPriorityFeePerGas" in tx else None,
            "nonce": int(tx["nonce"], 16),
            "input": tx["input"],
            "fetched_at": datetime.now().isoformat()
        }
        
        # Calculate effective gas price
        if latest_block and transaction["max_fee_per_gas"] and transaction["max_priority_fee_per_gas"]:
            base_fee_per_gas = int(latest_block["baseFeePerGas"], 16)
            transaction["latest_block_base_fee_per_gas"] = base_fee_per_gas
            transaction["estimated_effective_gas_price"] = min(
                transaction["max_fee_per_gas"],
                transaction["max_priority_fee_per_gas"] + base_fee_per_gas
            )
        
        return transaction

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
