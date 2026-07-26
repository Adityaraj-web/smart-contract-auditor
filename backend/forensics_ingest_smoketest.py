"""
backend/forensics_ingest_smoketest.py

Step 2.7 — manual smoke test for the Phase 2 ingestion pipeline, run against
a real historical incident before Phase 3 builds on top of it.

Target: the first of the six Euler Finance attack transactions
(March 13, 2023) — a good stress-test candidate because it involves
contract creation (two internal CREATEs), a large number of ERC-20 Transfer
logs across several tokens, and a flash-loan-driven sequence, all in one tx.

Run from the backend/ directory (so the `from etherscan_client import ...`
and `from forensics_ingest import ...` imports resolve), with ETHERSCAN_API_KEY
set in your environment or .env:

    python forensics_ingest_smoketest.py
"""

import json
from dotenv import load_dotenv
from forensics_ingest import ingest_transaction

# main.py does NOT call load_dotenv() anywhere in this project — whatever
# mechanism gets ETHERSCAN_API_KEY (and friends) into the FastAPI process's
# environment isn't something this standalone script can rely on. Loading
# .env explicitly here makes this script self-sufficient regardless of how
# the rest of the project is run.
load_dotenv()

EULER_ATTACK_TX_1 = "0xc310a0affe2169d1f6feec1c63dbc7f7c62a887fa48795d327d4d2da2d6b111d"


def summarize(result: dict):
    """Prints a compact summary rather than the full structure — the full
    result (especially `logs`) can be large, and for a smoke test you mainly
    want to eyeball that each section populated sensibly."""
    tx = result["transaction"]
    internal = result["internal_transactions"]
    contracts = result["contracts"]

    print("=" * 70)
    print(f"schema_version:   {result['schema_version']}")
    print(f"tx_hash:          {result['tx_hash']}")
    print(f"chain:            {result['chain']}")
    print("-" * 70)
    print("TRANSACTION")
    print(f"  block_number:   {tx['block_number']}")
    print(f"  block_timestamp:{tx['block_timestamp']}")
    print(f"  from_address:   {tx['from_address']}")
    print(f"  to_address:     {tx['to_address']}")
    print(f"  status:         {tx['status']}  (expect '0x1' = success)")
    print(f"  value_wei:      {tx['value_wei']}")
    print(f"  gas_used:       {tx['gas_used']}")
    print(f"  log_count:      {len(tx['logs'])}")
    print("-" * 70)
    print("INTERNAL TRANSACTIONS")
    print(f"  count:          {len(internal['internal_transactions'])}")
    creates = [t for t in internal["internal_transactions"] if t["call_type"] == "create"]
    print(f"  create_calls:   {len(creates)}  (expect 2, per Etherscan's 'Created' tags)")
    print(f"  limitation_note:{internal['limitation_note']}")
    print("-" * 70)
    print("CONTRACTS")
    print(f"  unique_addresses_resolved: {len(contracts)}")
    verified_count = sum(1 for c in contracts.values() if c.get("verified"))
    print(f"  verified:       {verified_count}")
    print(f"  unverified:     {len(contracts) - verified_count}")
    for addr, info in contracts.items():
        tag = "VERIFIED" if info.get("verified") else "unverified"
        name = info.get("contract_name") or "-"
        print(f"    {addr}  [{tag}]  {name}")
    print("-" * 70)
    print(f"related_window:  {'None (include_window=False)' if result['related_window'] is None else 'present'}")
    print("=" * 70)


def main():
    print("Running WITHOUT window (base case)...\n")
    result = ingest_transaction(
        tx_hash=EULER_ATTACK_TX_1,
        chain="mainnet",
        include_window=False,
    )
    summarize(result)

    # Dump the full structure to a file too, for closer inspection —
    # printed summary above is deliberately partial.
    with open("smoketest_output.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\nFull result written to smoketest_output.json")


if __name__ == "__main__":
    main()