"""
backend/query_builder.py

Step 3.2 (query side): builds retrieval queries deterministically from
Step 3.1's decoded timeline, rather than letting an LLM freely phrase them.

Why deterministic: the audit side's retrieval queries come directly from
Slither's own finding descriptions - fixed, reproducible text. Forensics has
no equivalent static-analysis step, so without this module the query text
would have to come from an LLM's paraphrase of the evidence, which makes
retrieval non-reproducible (same transaction, different query text, possibly
different retrieved incidents, on two different runs) and one step removed
from the actual evidence rather than grounded in it directly.

Produces TWO separate queries rather than one blended paragraph:
  1. An event-pattern query, built from the distinct decoded event names -
     this is the primary signal, analogous to a fingerprint of what the
     transaction actually did on-chain.
  2. A structural-signal query, built from higher-level patterns (internal
     contract creation, unverified-contract involvement, unlimited token
     approvals) - kept separate from (1) so a strong structural signal isn't
     diluted by being blended into the same embedding as the raw event list.
Query 2 is only included if at least one structural signal is actually
present, rather than always emitting a mostly-empty query.
"""

MAX_UINT256 = 2 ** 256 - 1


def _distinct_event_names(timeline: dict) -> list[str]:
    """Preserves first-occurrence order rather than sorting - the sequence
    events actually happened in is itself part of the description's meaning
    (e.g. 'Deposit then RequestMint' reads differently than an alphabetized
    'Deposit, RequestMint')."""
    seen = []
    for log in timeline.get("log_sequence", []):
        name = log.get("event_name")
        if name and name not in seen:
            seen.append(name)
    return seen


def _has_internal_create(timeline: dict) -> bool:
    return any(
        entry.get("call_type") == "create"
        for entry in timeline.get("internal_call_sequence", [])
    )


def _has_unverified_contract(ingest_result: dict) -> bool:
    contracts = ingest_result.get("contracts", {})
    return any(not info.get("verified", False) for info in contracts.values())


def _has_unlimited_approval(timeline: dict) -> bool:
    for log in timeline.get("log_sequence", []):
        if log.get("event_name") != "Approval":
            continue
        args = log.get("args") or {}
        # different token implementations name the amount field differently
        # (value, wad, amount) - check all three rather than assuming one
        for key in ("value", "wad", "amount"):
            if args.get(key) == MAX_UINT256:
                return True
    return False


def build_forensics_queries(ingest_result: dict, timeline: dict) -> list[str]:
    """
    Returns a list of 1-2 deterministically-built query strings, ready to
    pass into retrieval.retrieve_forensics_context().
    """
    queries = []

    event_names = _distinct_event_names(timeline)
    if event_names:
        queries.append(
            "On-chain transaction emitting the following sequence of "
            f"events: {', '.join(event_names)}."
        )
    else:
        # No decoded events at all is itself worth querying on, rather than
        # returning an empty query list - a transaction with no recognizable
        # events is unusual and may itself resemble certain incident types
        # (e.g. a raw low-level call exploiting an unverified contract).
        queries.append(
            "On-chain transaction with no decoded standard or verified "
            "event signatures emitted."
        )

    signal_phrases = []
    if _has_internal_create(timeline):
        signal_phrases.append(
            "the transaction deploys one or more new contracts during its "
            "own execution (internal contract creation)"
        )
    if _has_unverified_contract(ingest_result):
        signal_phrases.append(
            "the transaction interacts with one or more unverified, "
            "unaudited contracts"
        )
    if _has_unlimited_approval(timeline):
        signal_phrases.append(
            "an unlimited (maximum uint256) token approval is granted "
            "during execution"
        )

    if signal_phrases:
        queries.append(
            "Structural pattern: " + "; ".join(signal_phrases) + "."
        )

    return queries