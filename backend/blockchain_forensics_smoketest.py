"""
backend/blockchain_forensics_smoketest.py

Smoke test for submit_forensics_attestation(), run against a real assembled
forensics report (forensics_report_output.json — the Euler Finance tx from
Phase 2/3 testing).

IMPORTANT — invocation differs from every other Phase 2/3 smoketest:
blockchain.py imports `from backend.etherscan_client import CHAIN_IDS`, a
package-style import identical to how main.py loads backend modules. That
only resolves when "backend" is reachable as a package, i.e. when this is
run as a module from the PROJECT ROOT — not with a flat `python
blockchain_forensics_smoketest.py` from inside backend/, unlike the other
Phase 2/3 smoketests.

Run from D:\\smart-contract-auditor:

    python -m backend.blockchain_forensics_smoketest

This mirrors the same gating logic the /forensics/attest endpoint (next
step) will need to apply before ever calling submit_forensics_attestation:
  - narrative_validation_failed=True -> hard block, no attestation attempt.
  - protocol_conflation_flags non-empty -> warn, but still attest, with
    has_conflation_flags=True recorded on-chain and in Supabase.
"""

import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from backend.blockchain import submit_forensics_attestation

REPORT_PATH = Path(__file__).parent / "forensics_report_output.json"


def main():
    with open(REPORT_PATH) as f:
        report = json.load(f)

    tx_hash = report["tx_hash"]
    chain = report["chain"]

    print(f"Loaded report for tx_hash={tx_hash} chain={chain}")

    # ── Gating: block on failed narrative validation ───────────────────────
    if report.get("narrative_validation_failed"):
        print(
            "BLOCKED: narrative_validation_failed=True — this report is not "
            "attestable. (This is the correctness-failure gate from Q2 — "
            "not something the smoketest can override.)"
        )
        return

    narrative = report.get("narrative")
    if not narrative:
        print("BLOCKED: no narrative present in report — nothing to attest.")
        return

    # candidate_categories is reconstructed from the narrative's own
    # category_assessments — since _validate_category_match already
    # confirmed (at generation time) that this set exactly matches what
    # build_forensics_prompt designated as candidates.
    candidate_categories = [a["category"] for a in narrative["category_assessments"]]
    print(f"Candidate categories: {candidate_categories}")

    # ── Warn-but-allow on conflation flags ──────────────────────────────────
    conflation_flags = report.get("protocol_conflation_flags", [])
    has_conflation_flags = len(conflation_flags) > 0
    if has_conflation_flags:
        print(
            f"WARNING: {len(conflation_flags)} protocol_conflation_flag(s) "
            f"present — proceeding with attestation, but has_conflation_flags "
            f"will be recorded as True for downstream review."
        )
        for flag in conflation_flags:
            print(f"  - [{flag['field']}] protocol={flag['protocol']!r} "
                  f"snippet={flag['snippet']!r}")
    else:
        print("No protocol_conflation_flags — clean.")

    # report_json must match exactly what the report hash will be computed
    # against — sort_keys=True mirrors the convention already used for the
    # audit side in main.py's /audit/attest (json.dumps(report_dict, sort_keys=True)).
    report_json = json.dumps(report, sort_keys=True)

    print("\nSubmitting forensics attestation...")
    result = submit_forensics_attestation(
        tx_hash=tx_hash,
        chain=chain,
        report_json=report_json,
        candidate_categories=candidate_categories,
        has_conflation_flags=has_conflation_flags,
    )

    print("\n--- Result ---")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()