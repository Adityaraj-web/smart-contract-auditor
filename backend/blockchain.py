import os
import json
from pathlib import Path
from datetime import datetime, timezone
from web3 import Web3
from web3.exceptions import TimeExhausted
from dotenv import load_dotenv
from supabase import create_client
from backend.etherscan_client import CHAIN_IDS

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


# ══════════════════════════════════════════════════════════════════════════
# FORENSICS ADDITIONS (Phase 4) — everything below is new.
# Nothing above this line has been modified.
# ══════════════════════════════════════════════════════════════════════════

FORENSICS_CONTRACT_ADDRESS = os.getenv("FORENSICS_CONTRACT_ADDRESS")

FORENSICS_ARTIFACT_PATH = (
    Path(__file__).parent.parent
    / "hardhat"
    / "artifacts"
    / "contracts"
    / "ForensicsAttestationRegistry.sol"
    / "ForensicsAttestationRegistry.json"
)

# Receipt-wait timeout for forensics attestation transactions. Separate from
# submit_attestation()'s fixed 120s — a real Sepolia confirmation during
# testing took longer than 120s under a low ambient gas price, so this is
# given its own longer budget, mirroring the same reasoning that gave
# generate_forensics_narrative() its own longer FORENSICS_TIMEOUT_SECONDS
# back in Phase 3 (heavier data / slower conditions justify a longer wait,
# without touching the audit side's proven-fine value).
FORENSICS_RECEIPT_TIMEOUT_SECONDS = 300
# This order is permanent once anything is attested with it — changing it
# later would silently reinterpret every previously-attested bitmask.
FORENSICS_TAXONOMY_ORDER = [
    "reentrancy",
    "oracle_manipulation",
    "flash_loan_enabled",
    "access_control_failure",
    "logic_error",
    "front_running_mev",
    "signature_replay_verification_bypass",
    "bridge_cross_chain_exploit",
    "governance_attack",
]


def _compute_category_bitmask(candidate_categories: list) -> int:
    """
    Encodes a list of candidate category names into the on-chain uint16
    bitmask, using FORENSICS_TAXONOMY_ORDER as the fixed bit ordering.
    Raises loudly on an unrecognized category rather than silently
    dropping it — an unknown name here almost certainly means the taxonomy
    list has drifted against attack_pattern_scoring.py.
    """
    bitmask = 0
    for category in candidate_categories:
        try:
            bit_index = FORENSICS_TAXONOMY_ORDER.index(category)
        except ValueError:
            raise ValueError(
                f"Unknown forensics category '{category}' — not in "
                f"FORENSICS_TAXONOMY_ORDER. Check for drift against the "
                f"taxonomy used in attack_pattern_scoring.py."
            )
        bitmask |= (1 << bit_index)
    return bitmask


def _load_forensics_contract():
    w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))
    if not w3.is_connected():
        raise ConnectionError("Could not connect to Sepolia RPC")
    with open(FORENSICS_ARTIFACT_PATH) as f:
        artifact = json.load(f)
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(FORENSICS_CONTRACT_ADDRESS),
        abi=artifact["abi"],
    )
    return w3, contract


def _write_forensics_to_supabase(record: dict):
    _get_supabase().table("forensics_attestations").upsert(
        record, on_conflict="tx_hash"
    ).execute()


def _check_existing_forensics(tx_hash: str) -> dict | None:
    result = (
        _get_supabase()
        .table("forensics_attestations")
        .select("*")
        .eq("tx_hash", tx_hash)
        .limit(1)
        .execute()
    )
    if result.data and len(result.data) > 0:
        return result.data[0]
    return None


def _already_attested_forensics_response(
    existing: dict | None, tx_hash: str, report_hash_hex: str
) -> dict:
    """Shared helper for all graceful already-attested returns — mirrors
    _already_attested_response on the audit side."""
    if existing:
        return {
            "attestation_tx_hash":  existing["attestation_tx_hash"],
            "tx_hash":              existing["tx_hash"],
            "chain":                existing["chain"],
            "chain_id":             existing["chain_id"],
            "report_hash":          existing["report_hash"],
            "category_bitmask":     existing["category_bitmask"],
            "has_conflation_flags": existing["has_conflation_flags"],
            "block_number":         existing["block_number"],
            "already_attested":     True,
        }
    # On-chain only — historical gap, no Supabase record.
    return {
        "attestation_tx_hash":  None,
        "tx_hash":              tx_hash,
        "chain":                None,
        "chain_id":             None,
        "report_hash":          report_hash_hex,
        "category_bitmask":     None,
        "has_conflation_flags": None,
        "block_number":         None,
        "already_attested":     True,
    }


def submit_forensics_attestation(
    tx_hash: str,
    chain: str,
    report_json: str,
    candidate_categories: list,
    has_conflation_flags: bool,
) -> dict:
    """
    tx_hash / chain here describe the SUBJECT transaction being forensicked
    (e.g. a mainnet incident) — not to be confused with the Sepolia
    transaction this function itself submits to write the attestation.
    The attestation is always written to Sepolia via SEPOLIA_RPC_URL,
    regardless of what chain the subject transaction lived on; chain_id is
    stored on-chain purely as descriptive metadata about the subject tx.
    """
    w3, contract = _load_forensics_contract()

    chain_id = CHAIN_IDS.get(chain.lower())
    if chain_id is None:
        raise ValueError(f"Unsupported chain '{chain}'. Supported: {list(CHAIN_IDS)}")

    tx_hash_bytes = Web3.to_bytes(hexstr=tx_hash)
    if len(tx_hash_bytes) != 32:
        raise ValueError(
            f"tx_hash must be a 32-byte hash, got {len(tx_hash_bytes)} bytes: {tx_hash}"
        )

    report_hash       = Web3.keccak(text=report_json)
    report_hash_hex   = report_hash.hex()
    category_bitmask  = _compute_category_bitmask(candidate_categories)

    # ── Pre-flight: already in Supabase? ──────────────────────────────────────
    existing = _check_existing_forensics(tx_hash)
    if existing:
        return _already_attested_forensics_response(existing, tx_hash, report_hash_hex)

    # ── New attestation ────────────────────────────────────────────────────────
    account = w3.eth.account.from_key(DEPLOYER_PRIVATE_KEY)

    # Gas is estimated dynamically rather than hardcoded, unlike the audit
    # side's fixed 200000. ForensicsAttestation has more fields (7 vs 5,
    # including a fresh uint16 + bool alongside the existing types) plus the
    # same array push and a wider event — a real first attempt at a fixed
    # 200000 ran out of gas on Sepolia. Estimating against the live network
    # and adding a 30% buffer avoids re-guessing a magic number if the
    # struct ever changes again.
    estimated_gas = contract.functions.attestForensics(
        tx_hash_bytes,
        chain_id,
        report_hash,
        category_bitmask,
        has_conflation_flags,
    ).estimate_gas({"from": account.address})
    gas_limit = int(estimated_gas * 1.3)
    print(f"[DEBUG] estimated_gas={estimated_gas}, using gas_limit={gas_limit}")

    tx = contract.functions.attestForensics(
        tx_hash_bytes,
        chain_id,
        report_hash,
        category_bitmask,
        has_conflation_flags,
    ).build_transaction({
        "from":     account.address,
        "nonce":    w3.eth.get_transaction_count(account.address),
        "gas":      gas_limit,
        "gasPrice": w3.eth.gas_price,
    })

    signed_tx = w3.eth.account.sign_transaction(tx, DEPLOYER_PRIVATE_KEY)
    attestation_tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"[DEBUG] forensics attestation tx submitted: {attestation_tx_hash.hex()}")

    try:
        receipt = w3.eth.wait_for_transaction_receipt(
            attestation_tx_hash, timeout=FORENSICS_RECEIPT_TIMEOUT_SECONDS
        )
    except TimeExhausted:
        print(f"[DEBUG] TimeExhausted waiting for {attestation_tx_hash.hex()}")
        late_existing = _check_existing_forensics(tx_hash)
        return _already_attested_forensics_response(late_existing, tx_hash, report_hash_hex)

    if receipt.status != 1:
        print(f"[DEBUG] transaction reverted: {attestation_tx_hash.hex()}, receipt={dict(receipt)}")
        late_existing = _check_existing_forensics(tx_hash)
        return _already_attested_forensics_response(late_existing, tx_hash, report_hash_hex)

    print(f"[DEBUG] forensics attestation confirmed in block {receipt.blockNumber}")

    result = {
        "attestation_tx_hash":   attestation_tx_hash.hex(),
        "tx_hash":               tx_hash,
        "chain":                 chain,
        "chain_id":              chain_id,
        "report_hash":           report_hash_hex,
        "category_bitmask":      category_bitmask,
        "has_conflation_flags":  has_conflation_flags,
        "block_number":          receipt.blockNumber,
        "already_attested":      False,
    }

    _write_forensics_to_supabase({
        "tx_hash":              result["tx_hash"],
        "chain":                result["chain"],
        "chain_id":             result["chain_id"],
        "attestor_address":     account.address.lower(),
        "category_bitmask":     result["category_bitmask"],
        "has_conflation_flags": result["has_conflation_flags"],
        "report_hash":          result["report_hash"],
        "attestation_tx_hash":  result["attestation_tx_hash"],
        "block_number":         result["block_number"],
        "attested_at":          datetime.now(timezone.utc).isoformat(),
    })

    return result