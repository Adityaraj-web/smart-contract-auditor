"""
backend/timeline_builder.py

Step 3.1: builds the deterministic attack "timeline" from Phase 2's
ingest_transaction() output.

Produces TWO separately-ordered event tracks (internal calls, decoded logs)
rather than one merged sequence. This is deliberate, not a shortcut: there is
no shared ordinal key between Etherscan's internal-transaction trace order
and log-index order that would allow safely interleaving "internal call #3
happened between log #5 and log #6" without guessing - and guessing here
would break the same "Python reconstructs facts, never infers" rule that
governs overall_risk in the existing pre-deployment auditor.

Any related-window transactions (Phase 2 Step 2.5, address-scoped) are kept
in a clearly separate, explicitly-unconfirmed section. This directly reflects
what the Euler Finance smoke test showed: that incident's real 6-transaction
attack sequence spanned two different attacker addresses, so an
address-scoped window is a genuinely incomplete signal, never a confirmed
timeline, and must never be presented as one.

No interpretation happens here: no root-cause guessing, no taxonomy tagging,
no LLM calls. Just facts, ordered and decoded where deterministically
possible, with every known gap stated explicitly in the output itself.
"""

# Phase 4 addition: prefer the package-style import so this module shares the
# SAME log_decoder module identity as anything else loaded via `backend.X`
# (log_decoder.py itself holds no risky module-level state, so this is about
# consistency rather than a real duplication risk) — falls back to the flat
# import so this file still runs unchanged standalone from inside backend/,
# exactly as in Phase 3 (e.g. `python timeline_builder_smoketest.py`).
try:
    from backend.log_decoder import decode_all_logs
except ImportError:
    from log_decoder import decode_all_logs


def build_timeline(ingest_result: dict) -> dict:
    """
    ingest_result: the dict returned by forensics_ingest.ingest_transaction().

    Returns a dict with:
      - main_transaction: the core facts about the transaction itself
      - internal_call_sequence: internal calls, in Etherscan's trace order
      - log_sequence: decoded event logs, ordered by logIndex
      - decode_summary: how many logs decoded successfully vs. not
      - related_window: None if not fetched, else the Step 2.5 window data
        with an explicit non-confirmation caveat attached
      - limitations: known, load-bearing gaps in this evidence, carried
        forward from Phase 2 and added to here
    """
    tx = ingest_result["transaction"]
    internal_result = ingest_result["internal_transactions"]
    contracts = ingest_result["contracts"]
    related_window = ingest_result.get("related_window")

    decoded_logs = decode_all_logs(tx.get("logs", []), contracts)

    internal_sequence = [
        {**entry, "sequence_index": i}
        for i, entry in enumerate(internal_result.get("internal_transactions", []))
    ]

    undecoded_count = sum(1 for log in decoded_logs if log["decode_method"] == "undecoded")
    verified_abi_count = sum(1 for log in decoded_logs if log["decode_method"] == "verified_abi")
    known_signature_count = sum(1 for log in decoded_logs if log["decode_method"] == "known_signature")

    timeline = {
        "main_transaction": {
            "tx_hash": ingest_result["tx_hash"],
            "chain": ingest_result["chain"],
            "block_number": tx.get("block_number"),
            "block_timestamp": tx.get("block_timestamp"),
            "from_address": tx.get("from_address"),
            "to_address": tx.get("to_address"),
            "status": tx.get("status"),
        },
        "internal_call_sequence": internal_sequence,
        "log_sequence": decoded_logs,
        "decode_summary": {
            "total_logs": len(decoded_logs),
            "verified_abi_decoded": verified_abi_count,
            "known_signature_decoded": known_signature_count,
            "undecoded": undecoded_count,
        },
        "related_window": None,
        "limitations": [
            "internal_call_sequence and log_sequence are two independently-"
            "ordered tracks, not a single merged timeline: there is no shared "
            "ordinal key between Etherscan's internal-transaction trace order "
            "and log-index order that would allow safely interleaving them "
            "without guessing.",
            internal_result.get("limitation_note", ""),
        ],
    }

    if related_window is not None:
        timeline["related_window"] = {
            **related_window,
            "confirmed": False,
            "caveat": (
                "These transactions are candidates only, scoped to a single "
                "address over a small block window. They are NOT confirmed "
                "to be part of the same attack. As demonstrated by the real "
                "Euler Finance incident (March 2023), whose 6 attack "
                "transactions were split across two different attacker "
                "addresses, this window can legitimately miss real related "
                "transactions sent from a different address entirely."
            ),
        }

    return timeline