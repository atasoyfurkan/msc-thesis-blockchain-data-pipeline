from typing import Optional
import json
import logging

def extract_ethereum_node_ws_message(message: str) -> Optional[str]:
    try:
        data = json.loads(message)

        if not isinstance(data, dict):
            logging.warning(f"Invalid message format: {data}")
            return None

        if "error" in data:
            logging.error(f"Error response: {data['error']}")
            return None

        if "params" not in data:
            if "result" in data:
                logging.info(f"Received subscription message: {data}")
            else:
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
