"""
backend/timeline_builder_smoketest.py

Step 3.1 smoke test - runs build_timeline() against the real Euler Finance
ingestion result already saved from the Phase 2 smoke test, so this needs
NO new API calls. Run from backend/, after forensics_ingest_smoketest.py has
already produced smoketest_output.json:

    python timeline_builder_smoketest.py
"""

import json
from timeline_builder import build_timeline


def main():
    with open("smoketest_output.json") as f:
        ingest_result = json.load(f)

    timeline = build_timeline(ingest_result)

    print("=" * 70)
    print("MAIN TRANSACTION")
    for k, v in timeline["main_transaction"].items():
        print(f"  {k}: {v}")

    print("-" * 70)
    print("INTERNAL CALL SEQUENCE")
    for entry in timeline["internal_call_sequence"]:
        print(f"  [{entry['sequence_index']}] {entry['call_type']:12s} "
              f"{entry['from_address']} -> {entry['to_address']}  "
              f"created={entry['contract_address']}")

    print("-" * 70)
    print("DECODE SUMMARY")
    for k, v in timeline["decode_summary"].items():
        print(f"  {k}: {v}")

    print("-" * 70)
    print("LOG SEQUENCE (first 10)")
    for log in timeline["log_sequence"][:10]:
        if log["decode_method"] == "undecoded":
            print(f"  [{log['log_index']}] UNDECODED  topic0={log['raw_topic0'][:18]}...  "
                  f"contract={log['contract_address']}")
        else:
            print(f"  [{log['log_index']}] {log['event_name']:10s} ({log['standard']:9s}"
                  f" via {log['decode_method']})  args={log['args']}")

    print("-" * 70)
    print("LIMITATIONS")
    for note in timeline["limitations"]:
        print(f"  - {note}")

    print("-" * 70)
    print(f"related_window: {'None (no window fetched)' if timeline['related_window'] is None else 'present'}")
    print("=" * 70)

    with open("timeline_output.json", "w") as f:
        json.dump(timeline, f, indent=2)
    print("\nFull timeline written to timeline_output.json")


if __name__ == "__main__":
    main()