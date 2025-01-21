from datetime import datetime
from typing import Optional

def parse_hex(value: Optional[str], default: Optional[int] = None) -> Optional[int]:
    return int(value, 16) if value else default

def parse_price_data(price_data: dict, source: str) -> dict:
    """Parses the fetched price data."""
    return {
        "symbol": price_data.get("symbol"),
        "price": float(price_data.get("lastPrice")), 
        "volume": float(price_data.get("volume")),
        "quote_volume": float(price_data.get("quoteVolume")),
        "count": int(price_data.get("count")),
        "price_change": float(price_data.get("priceChange")),
        "price_change_percent": float(price_data.get("priceChangePercent")),
        "weighted_avg_price": float(price_data.get("weightedAvgPrice")),
        "prev_close_price": float(price_data.get("prevClosePrice")),
        "last_price": float(price_data.get("lastPrice")),
        "last_qty": float(price_data.get("lastQty")),
        "bid_price": float(price_data.get("bidPrice")),
        "bid_qty": float(price_data.get("bidQty")),
        "ask_price": float(price_data.get("askPrice")),
        "ask_qty": float(price_data.get("askQty")),
        "open_price": float(price_data.get("openPrice")),
        "high_price": float(price_data.get("highPrice")),
        "low_price": float(price_data.get("lowPrice")),
        "source": source,
        "fetched_at": datetime.now().isoformat()
    }

def parse_transaction(tx: dict[str, str], latest_block: Optional[dict[str, str]] = None) -> dict[str, Optional[int]]:
    transaction =  {
        "hash": tx["hash"],
        "block_hash": tx.get("blockHash"),
        "block_number": parse_hex(tx.get("blockNumber")),
        "from": tx["from"],
        "to": tx.get("to"),
        "type": parse_hex(tx.get("type")),
        "chain_id": parse_hex(tx.get("chainId")),
        "transaction_index": parse_hex(tx.get("transactionIndex")),
        "nonce": parse_hex(tx.get("nonce")),
        "value": str(parse_hex(tx["value"])),
        "gas": parse_hex(tx["gas"]),
        "gas_price": parse_hex(tx.get("gasPrice")),
        "max_fee_per_gas": parse_hex(tx.get("maxFeePerGas")),
        "max_priority_fee_per_gas": parse_hex(tx.get("maxPriorityFeePerGas")),
        "input": tx["input"],
        "fetched_at": datetime.now().isoformat()
    }
    
    # Calculate effective gas price
    if latest_block and transaction["max_fee_per_gas"] and transaction["max_priority_fee_per_gas"]:
        base_fee_per_gas = parse_hex(latest_block.get("baseFeePerGas"))
        
        transaction["latest_block_base_fee_per_gas"] = base_fee_per_gas
        transaction["estimated_effective_gas_price"] = min(
            transaction["max_fee_per_gas"],
            transaction["max_priority_fee_per_gas"] + base_fee_per_gas
        )

    return transaction

def parse_block_header(block_header: dict) -> dict:
    return {
        "hash": block_header["hash"],
        "mix_hash": block_header.get("mixHash"),
        "base_fee_per_gas": parse_hex(block_header.get("baseFeePerGas")),
        "difficulty": parse_hex(block_header.get("difficulty")),
        "extra_data": block_header.get("extraData"),
        "gas_limit": parse_hex(block_header.get("gasLimit")),
        "gas_used": parse_hex(block_header.get("gasUsed")),
        "blob_gas_used": parse_hex(block_header.get("blobGasUsed")),
        "excess_blob_gas": parse_hex(block_header.get("excessBlobGas")),
        "logs_bloom": block_header.get("logsBloom"),
        "miner": block_header.get("miner"),
        "nonce": block_header.get("nonce"),
        "parent_hash": block_header.get("parentHash"),
        "receipt_root": block_header.get("receiptRoot"),
        "sha3_uncles": block_header.get("sha3Uncles"),
        "state_root": block_header.get("stateRoot"),
        "transaction_root": block_header.get("transactionsRoot"),
        "withdrawals_root": block_header.get("withdrawalsRoot"),
        "parent_beacon_block_root": block_header.get("parentBeaconBlockRoot"),
        "number": parse_hex(block_header.get("number")),
        "created_at": datetime.fromtimestamp(parse_hex(block_header["timestamp"])).isoformat(),
        "fetched_at": datetime.now().isoformat()
    }


def parse_block(block: dict) -> dict:
    parsed_block = parse_block_header(block)
    parsed_block["transactions"] = [parse_transaction(tx) for tx in block["transactions"]]
    return parsed_block


def parse_transfer_event(transfer_event: dict, symbol: str, decimals: int, respective_block: Optional[dict[str, str]] = None) -> dict:
    transfer_event = {
        "symbol": symbol,
        "block_number": parse_hex(transfer_event.get("blockNumber")),
        "block_hash": transfer_event.get("blockHash"),
        "transaction_hash": transfer_event.get("transactionHash"),
        "transaction_index": parse_hex(transfer_event.get("transactionIndex")),
        "log_index": parse_hex(transfer_event.get("logIndex")),
        "address": transfer_event.get("address"),
        "topics": transfer_event.get("topics"),
        "data": transfer_event.get("data"),
        "removed": transfer_event.get("removed"),
        "fetched_at": datetime.now().isoformat()
    }

    if transfer_event["topics"] and len(transfer_event["topics"]) == 3:
        # Remove leading zeroes from 'from' and 'to'
        transfer_event["from"] = "0x" + transfer_event["topics"][1][-40:]
        transfer_event["to"] = "0x" + transfer_event["topics"][2][-40:]
    
    if transfer_event["data"]:
        transfer_event["value"] = float(parse_hex(transfer_event["data"]) / 10**decimals)
    
    if respective_block and respective_block["timestamp"]:
        transfer_event["block_created_at"] = datetime.fromtimestamp(parse_hex(respective_block["timestamp"])).isoformat()

    return transfer_event