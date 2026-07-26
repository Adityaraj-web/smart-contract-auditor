"""
backend/forensics_report_smoketest.py

Full Phase 3 end-to-end smoke test - the first time the entire pipeline
runs live: real Etherscan calls, real ChromaDB retrieval against the
historical_exploits collection, and a real Ollama generation call.

Prerequisites before running:
  1. ETHERSCAN_API_KEY set (loaded via .env below, same as Phase 2's smoketest)
  2. Ollama running locally with llama3.2:3b pulled and available
  3. knowledge-base/chroma_db's historical_exploits collection already built
     (Phase 1 forensics-scripts/02_embed_and_store.py already run)

Run from backend/:
    python forensics_report_smoketest.py

Heads-up on runtime: this makes ~5-9 real Etherscan calls, one embedding
pass per retrieval query, and at least one real Ollama generation call
(CPU inference - could take a couple minutes; up to 2 narrative retries if
the category-match validation fails on the first attempt, so worst case is
a few minutes, not seconds).
"""

import json
from dotenv import load_dotenv
from forensics_report_generator import generate_forensics_report

load_dotenv()

EULER_ATTACK_TX_1 = "0xc310a0affe2169d1f6feec1c63dbc7f7c62a887fa48795d327d4d2da2d6b111d"


def summarize(report: dict):
    timeline = report["timeline"]
    pattern_scores = report["pattern_scores"]
    narrative = report["narrative"]

    print("=" * 70)
    print(f"schema_version: {report['schema_version']}")
    print(f"tx_hash:        {report['tx_hash']}")
    print(f"chain:          {report['chain']}")
    print("-" * 70)
    print("DECODE SUMMARY (from timeline)")
    for k, v in timeline["decode_summary"].items():
        print(f"  {k}: {v}")
    print("-" * 70)
    print("CANDIDATE ATTACK PATTERNS (Step 3.3)")
    candidates = {c: d for c, d in pattern_scores.items() if d["is_candidate"]}
    if not candidates:
        print("  (none - no category had any supporting evidence)")
    for category, data in candidates.items():
        print(f"  {category}:")
        for s in data["direct_signals"]:
            print(f"    [direct] {s}")
        for s in data["retrieval_support"]:
            print(f"    [retrieval] resembles '{s['title']}' ({s['protocol']}, dist={s['distance']})")
    print("-" * 70)
    print(f"RETRIEVED INCIDENTS: {len(report['retrieved_incidents'])}")
    for inc in report["retrieved_incidents"]:
        print(f"  - {inc['title']} ({inc['protocol']}, section: {inc['section']}, dist: {inc['distance']})")
    print("-" * 70)
    print(f"narrative_validation_failed: {report['narrative_validation_failed']}")
    conflation_flags = report.get("protocol_conflation_flags", [])
    print(f"protocol_conflation_flags: {len(conflation_flags)}")
    for flag in conflation_flags:
        print(f"  !! [{flag['field']}] bare mention of '{flag['protocol']}': ...{flag['snippet']}...")
    if narrative:
        print("-" * 70)
        print("NARRATIVE SUMMARY:")
        print(f"  {narrative['summary']}")
        print("\nROOT CAUSE NARRATIVE:")
        print(f"  {narrative['root_cause_narrative']}")
        print("\nCATEGORY ASSESSMENTS:")
        for a in narrative["category_assessments"]:
            print(f"  [{a['category']}] {a['llm_assessment']}")
        print(f"\nHISTORICAL CITATIONS USED: {narrative['historical_citations_used']}")
    else:
        print("\n!! No narrative produced - see raw_invalid_narrative in the full JSON output.")
    print("=" * 70)


def main():
    print("Running full Phase 3 pipeline against the Euler Finance attack tx...")
    print("(this makes real API/Ollama calls and may take a few minutes)\n")

    report = generate_forensics_report(
        tx_hash=EULER_ATTACK_TX_1,
        chain="mainnet",
        include_window=False,
    )

    summarize(report)

    with open("forensics_report_output.json", "w") as f:
        json.dump(report, f, indent=2)
    print("\nFull report written to forensics_report_output.json")


if __name__ == "__main__":
    main()