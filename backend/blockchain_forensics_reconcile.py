"""
backend/blockchain_forensics_reconcile.py

One-off reconciliation tool. Handles the gap exposed during Phase 4
smoketesting: a forensics attestation transaction can genuinely confirm
on-chain *after* wait_for_transaction_receipt has already given up and
returned an "already_attested" response — meaning submit_forensics_attestation
never reached its normal _write_forensics_to_supabase() call for that
attestation, even though the chain itself now has the real record.

This reads the confirmed on-chain state directly (the source of truth) and
writes it into Supabase, rather than reconstructing values from memory of
what was originally intended to be submitted.

Run from the project root:

    python -m backend.blockchain_forensics_reconcile <tx_hash> <attestation_tx_hash>

Where:
  tx_hash             - the subject transaction that was forensicked
                         (the key the contract itself is indexed by)
  attestation_tx_hash - the Sepolia transaction hash that called
                         attestForensics (used only to look up block_number
                         and confirm it succeeded)
"""

import sys
from dotenv import load_dotenv

load_dotenv()

from web3 import Web3
from backend.blockchain import (
    _load_forensics_contract,
    _write_forensics_to_supabase,
    _check_existing_forensics,
)
from datetime import datetime, timezone

# Reverse lookup for chain_id -> chain name, since the on-chain struct only
# stores chain_id, not the string name we use elsewhere in the pipeline.
_CHAIN_ID_TO_NAME = {
    1: "mainnet",
    11155111: "sepolia",
}


def main():
    if len(sys.argv) != 3:
        print("Usage: python -m backend.blockchain_forensics_reconcile <tx_hash> <attestation_tx_hash>")
        sys.exit(1)

    tx_hash = sys.argv[1]
    attestation_tx_hash = sys.argv[2]

    w3, contract = _load_forensics_contract()

    # ── Confirm the attestation transaction actually succeeded ──────────────
    receipt = w3.eth.get_transaction_receipt(attestation_tx_hash)
    if receipt.status != 1:
        print(f"Refusing to reconcile: attestation_tx_hash {attestation_tx_hash} "
              f"has status={receipt.status} (not a success). Nothing written.")
        sys.exit(1)

    # ── Read the confirmed struct back from the contract itself ─────────────
    tx_hash_bytes = Web3.to_bytes(hexstr=tx_hash)
    onchain = contract.functions.getForensicsAttestation(tx_hash_bytes).call()
    # struct order: (txHash, chainId, attestor, timestamp, reportHash, categoryBitmask, hasConflationFlags)
    onchain_tx_hash, chain_id, attestor, timestamp, report_hash, category_bitmask, has_conflation_flags = onchain

    if timestamp == 0:
        print(f"Refusing to reconcile: on-chain record for {tx_hash} has "
              f"timestamp=0, meaning it was never actually attested. Nothing written.")
        sys.exit(1)

    chain_name = _CHAIN_ID_TO_NAME.get(chain_id, f"unknown_chain_id_{chain_id}")

    # ── Guard against double-writing if this was somehow already reconciled ──
    existing = _check_existing_forensics(tx_hash)
    if existing:
        print(f"Supabase already has a record for {tx_hash} — nothing to do.")
        print(existing)
        return

    record = {
        "tx_hash":              tx_hash,
        "chain":                chain_name,
        "chain_id":             chain_id,
        "attestor_address":     attestor.lower(),
        "category_bitmask":     category_bitmask,
        "has_conflation_flags": has_conflation_flags,
        "report_hash":          report_hash.hex(),
        "attestation_tx_hash":  attestation_tx_hash,
        "block_number":         receipt.blockNumber,
        "attested_at":          datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(),
    }

    print("Reconciling with on-chain record:")
    print(record)

    _write_forensics_to_supabase(record)
    print("Done. Supabase row written from confirmed on-chain state.")


if __name__ == "__main__":
    main()