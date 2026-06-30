import os
import json
from pathlib import Path
from datetime import datetime, timezone
from web3 import Web3
from web3.exceptions import TimeExhausted
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SEPOLIA_RPC_URL           = os.getenv("SEPOLIA_RPC_URL")
DEPLOYER_PRIVATE_KEY      = os.getenv("DEPLOYER_PRIVATE_KEY")
CONTRACT_ADDRESS          = os.getenv("CONTRACT_ADDRESS")
SUPABASE_URL              = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

ARTIFACT_PATH = (
    Path(__file__).parent.parent
    / "hardhat"
    / "artifacts"
    / "contracts"
    / "AttestationRegistry.sol"
    / "AttestationRegistry.json"
)


def _load_contract():
    w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))
    if not w3.is_connected():
        raise ConnectionError("Could not connect to Sepolia RPC")
    with open(ARTIFACT_PATH) as f:
        artifact = json.load(f)
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS),
        abi=artifact["abi"],
    )
    return w3, contract


def _get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def _write_to_supabase(record: dict):
    _get_supabase().table("attestations").upsert(
        record, on_conflict="contract_hash"
    ).execute()


def _check_existing(contract_hash_hex: str) -> dict | None:
    result = (
        _get_supabase()
        .table("attestations")
        .select("*")
        .eq("contract_hash", contract_hash_hex)
        .limit(1)
        .execute()
    )
    if result.data and len(result.data) > 0:
        return result.data[0]
    return None


def _already_attested_response(existing: dict | None, contract_hash_hex: str, report_hash_hex: str) -> dict:
    """Shared helper for all graceful already-attested returns."""
    if existing:
        return {
            "tx_hash":          existing["tx_hash"],
            "contract_hash":    existing["contract_hash"],
            "report_hash":      existing["report_hash"],
            "block_number":     existing["block_number"],
            "already_attested": True,
        }
    # On-chain only — historical gap, no Supabase record.
    return {
        "tx_hash":          None,
        "contract_hash":    contract_hash_hex,
        "report_hash":      report_hash_hex,
        "block_number":     None,
        "already_attested": True,
    }


def submit_attestation(
    contract_source: str,
    risk_level: str,
    report_json: str,
) -> dict:
    w3, contract = _load_contract()

    # ── Normalise line endings before hashing ─────────────────────────────────
    # The uploaded file may have \r\n (Windows) or \n (Unix). Normalise to \n
    # so the hash is consistent regardless of the client OS or upload method.
    contract_source = contract_source.replace("\r\n", "\n").replace("\r", "\n")

    contract_hash     = Web3.keccak(text=contract_source)
    report_hash       = Web3.keccak(text=report_json)
    contract_hash_hex = contract_hash.hex()
    report_hash_hex   = report_hash.hex()

    # --- DEBUG (remove after confirming pre-flight works) ---
    print(f"[DEBUG] runtime contract_hash_hex: {contract_hash_hex}")
    # --- END DEBUG ---

    # ── Pre-flight: already in Supabase? ──────────────────────────────────────
    existing = _check_existing(contract_hash_hex)
    if existing:
        print(f"[DEBUG] pre-flight hit — returning already_attested")
        return _already_attested_response(existing, contract_hash_hex, report_hash_hex)

    print(f"[DEBUG] pre-flight miss — proceeding to submit transaction")

    # ── New attestation ────────────────────────────────────────────────────────
    account = w3.eth.account.from_key(DEPLOYER_PRIVATE_KEY)

    tx = contract.functions.attest(
        contract_hash,
        risk_level,
        report_hash,
    ).build_transaction({
        "from":     account.address,
        "nonce":    w3.eth.get_transaction_count(account.address),
        "gas":      200000,
        "gasPrice": w3.eth.gas_price,
    })

    signed_tx = w3.eth.account.sign_transaction(tx, DEPLOYER_PRIVATE_KEY)
    tx_hash   = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    # ── Wait for receipt — handle both revert and timeout gracefully ───────────
    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    except TimeExhausted:
        # Transaction submitted but not mined within 120s (Sepolia congestion).
        # Treat as historical gap — check Supabase one more time, then return.
        print(f"[DEBUG] TimeExhausted waiting for {tx_hash.hex()}")
        late_existing = _check_existing(contract_hash_hex)
        return _already_attested_response(late_existing, contract_hash_hex, report_hash_hex)

    # ── Revert: already attested on-chain but not in Supabase ─────────────────
    if receipt.status != 1:
        print(f"[DEBUG] transaction reverted: {tx_hash.hex()}")
        late_existing = _check_existing(contract_hash_hex)
        return _already_attested_response(late_existing, contract_hash_hex, report_hash_hex)

    # ── Success ───────────────────────────────────────────────────────────────
    result = {
        "tx_hash":          tx_hash.hex(),
        "contract_hash":    contract_hash_hex,
        "report_hash":      report_hash_hex,
        "block_number":     receipt.blockNumber,
        "already_attested": False,
    }

    _write_to_supabase({
        "contract_hash":   result["contract_hash"],
        "auditor_address": account.address.lower(),
        "risk_level":      risk_level,
        "report_hash":     result["report_hash"],
        "tx_hash":         result["tx_hash"],
        "block_number":    result["block_number"],
        "attested_at":     datetime.now(timezone.utc).isoformat(),
    })

    return result