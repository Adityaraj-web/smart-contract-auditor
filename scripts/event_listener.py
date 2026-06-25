import os
import json
from urllib import response
import requests as http_requests
from pathlib import Path
from datetime import datetime, timezone

from web3 import Web3
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SEPOLIA_RPC_URL = os.getenv("SEPOLIA_RPC_URL")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
DEPLOYMENT_BLOCK = int(os.getenv("DEPLOYMENT_BLOCK", "11132252"))

ARTIFACT_PATH = (
    Path(__file__).parent.parent
    / "hardhat"
    / "artifacts"
    / "contracts"
    / "AttestationRegistry.sol"
    / "AttestationRegistry.json"
)


def get_contract(w3):
    with open(ARTIFACT_PATH) as f:
        artifact = json.load(f)
    return w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS),
        abi=artifact["abi"],
    )


def fetch_events(contract, w3, from_block=0):
    """Fetch all AttestationCreated events using raw JSON-RPC call."""
    latest = w3.eth.block_number
    print(f"Fetching events from block {from_block} to {latest}...")

    event_signature = "AttestationCreated(bytes32,address,uint256,string,bytes32)"
    event_topic = Web3.to_hex(Web3.keccak(text=event_signature))

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_getLogs",
        "params": [{
            "fromBlock": hex(from_block),
            "toBlock": hex(latest),
            "address": Web3.to_checksum_address(CONTRACT_ADDRESS),
            "topics": [event_topic],
        }]
    }

    response = http_requests.post(SEPOLIA_RPC_URL, json=payload)
    print("Status:", response.status_code)
    print("Response:", response.text)
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        raise Exception(f"RPC error: {data['error']}")

    raw_logs = data.get("result", [])
    print(f"Found {len(raw_logs)} event(s).")

    events = []
    for log in raw_logs:
        decoded = contract.events.AttestationCreated().process_log(log)
        events.append(decoded)

    return events


def event_to_record(event, w3):
    """Convert a raw event log into a Supabase row dict."""
    args = event["args"]
    block = w3.eth.get_block(event["blockNumber"])
    timestamp = datetime.fromtimestamp(block["timestamp"], tz=timezone.utc)

    return {
        "contract_hash": args["contractHash"].hex(),
        "auditor_address": args["auditor"].lower(),
        "risk_level": args["riskLevel"],
        "report_hash": args["reportHash"].hex(),
        "tx_hash": event["transactionHash"].hex(),
        "block_number": event["blockNumber"],
        "attested_at": timestamp.isoformat(),
    }


def sync_to_supabase(records):
    """Upsert records into Supabase attestations table."""
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    for record in records:
        result = (
            supabase.table("attestations")
            .upsert(record, on_conflict="contract_hash")
            .execute()
        )
        print(f"Upserted: contract_hash={record['contract_hash'][:16]}... "
              f"tx={record['tx_hash'][:16]}...")


def main():
    w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))
    if not w3.is_connected():
        raise ConnectionError("Could not connect to Sepolia RPC")
    print(f"Connected to Sepolia. Latest block: {w3.eth.block_number}")

    contract = get_contract(w3)

    # Fetch from the block the contract was deployed
    # You can narrow this down later — 0 works but is slower
    events = fetch_events(contract, w3, from_block=DEPLOYMENT_BLOCK)

    if not events:
        print("No attestation events found.")
        return

    records = [event_to_record(e, w3) for e in events]
    sync_to_supabase(records)
    print("Sync complete.")


if __name__ == "__main__":
    main()