import json
import logging
import websocket
import requests
from typing import Optional
from modules.data_storage.minio.write_client import MinioWriteClient
from modules.data_ingestion.base_fetcher import DataFetcherBase
from modules.data_ingestion.parsers import parse_transfer_event
from modules.data_ingestion.extractors import extract_ethereum_node_ws_message

class TransferEventDataFetcher(DataFetcherBase):
    """Fetches Ethereum Transfer Event data and saves transaction details to MinIO."""

    def __init__(self, minio_write_client: MinioWriteClient, ws_url: str, http_url: str, token_configurations: list[dict], save_batch_size: int = 1000):
        super().__init__(minio_write_client=minio_write_client, save_batch_size=save_batch_size)
        self.ws_url = ws_url
        self.http_url = http_url
        self.token_configurations_lookup = { token_configuration["address"].lower(): token_configuration for token_configuration in token_configurations }
        self.data_batch: list[dict] = []


    def on_message(self, ws, message: str):
        """Handle incoming WebSocket messages."""
        logging.debug(f"Received websocket message: {message}")
        
        transfer_event = extract_ethereum_node_ws_message(message)
        if transfer_event:
            token_contract_address = transfer_event["address"].lower()
            if token_contract_address not in self.token_configurations_lookup:
                logging.error(f"Received transfer event for unknown token contract: {token_contract_address}")
                return 
            symbol = self.token_configurations_lookup[token_contract_address]["symbol"]
            decimals = self.token_configurations_lookup[token_contract_address]["decimals"]

            respective_block = self._fetch_block(block_hash=transfer_event["blockHash"])

            parsed_transfer_event = parse_transfer_event(transfer_event=transfer_event, symbol=symbol, decimals=decimals, respective_block=respective_block)
            self.data_batch.append(parsed_transfer_event)

        self.log_progress(data_batch=self.data_batch)

        if len(self.data_batch) >= self.save_batch_size:
            self.data_batch = self.save_to_minio(data_batch=self.data_batch)

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
        for index, token_configuration in enumerate(self.token_configurations_lookup.values()):
            ws.send(json.dumps({
                "jsonrpc": "2.0",
                "method": "eth_subscribe",
                "params": [
                    "logs", 
                    {
                        "address": token_configuration["address"],
                        "topics": [
                            token_configuration["topic"]
                        ]
                    }
                ],
                "id": index
            }))
            logging.info(f"Subscribed to logs for token: {token_configuration['symbol']}")

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
