"""
backend/attack_pattern_scoring.py

Step 3.3: scores a transaction's evidence against the 9 fixed taxonomy
categories, surfacing CANDIDATES WITH EVIDENCE rather than a single
confident classification. The final categorization stays a human (or
LLM-narrated-but-flagged-as-interpretive) judgment call - never something
this module asserts as settled fact.

Two separate evidence tracks per category:
  - direct_signals: heuristics computed straight from THIS transaction's own
    decoded evidence (Step 3.1's timeline).
  - retrieval_support: which retrieved historical incidents (Step 3.2) are
    tagged with this category, carried through as corroborating context -
    NOT as proof about this specific transaction.

DELIBERATE DESIGN CHOICE: direct_signals are only implemented for the 2
categories where a genuinely reliable, low-guesswork heuristic exists given
free-tier Etherscan data (flash_loan_enabled, reentrancy - see each
detector's docstring for exactly what it can and can't actually tell us).
For the remaining 6 categories, no direct heuristic is implemented at all.
Inventing brittle pattern-matching rules for those (e.g. "governance_attack
if an event name contains 'vote'") would look precise while actually being
closer to guessing than the honest alternative used here: relying on
retrieval_support alone.
"""

TAXONOMY_CATEGORIES = [
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


def _detect_flash_loan_signal(timeline: dict) -> list:
    """Reliable: a decoded event literally named 'FlashLoan' (case/underscore
    -insensitive match) is strong, direct evidence a flash loan occurred."""
    evidence = []
    for log in timeline.get("log_sequence", []):
        name = log.get("event_name") or ""
        if "flashloan" in name.lower().replace("_", ""):
            evidence.append(
                f"Decoded event '{name}' at log index {log.get('log_index')} "
                f"on contract {log.get('contract_address')}."
            )
    return evidence


def _detect_reentrancy_signal(timeline: dict) -> list:
    """WEAK heuristic - see module docstring. Flags an address invoked more
    than once across the internal call sequence. This is equally consistent
    with ordinary repeated sequential calls as with genuine reentrancy, since
    Etherscan's free-tier internal-tx-by-hash data carries no call-depth or
    trace-address field to actually confirm nested re-entry."""
    call_counts = {}
    for entry in timeline.get("internal_call_sequence", []):
        to_addr = entry.get("to_address")
        if to_addr:
            call_counts[to_addr] = call_counts.get(to_addr, 0) + 1

    evidence = []
    for address, count in call_counts.items():
        if count > 1:
            evidence.append(
                f"Address {address} appears as the target of {count} "
                f"separate internal calls. NOT confirmed reentrancy - this "
                f"data has no call-depth information, so it's equally "
                f"consistent with normal repeated calls."
            )
    return evidence


_DIRECT_SIGNAL_DETECTORS = {
    "flash_loan_enabled": _detect_flash_loan_signal,
    "reentrancy": _detect_reentrancy_signal,
}


def _retrieval_support_by_category(retrieved_incidents: list) -> dict:
    """Groups retrieved historical incidents by which taxonomy category(ies)
    each is tagged with. An incident can carry more than one tag (e.g.
    Wormhole, tagged both signature_replay_verification_bypass and
    bridge_cross_chain_exploit per the Phase 1 correction)."""
    support = {category: [] for category in TAXONOMY_CATEGORIES}
    for incident in retrieved_incidents:
        for category in incident.get("attack_type", []):
            if category in support:
                support[category].append({
                    "protocol": incident.get("protocol"),
                    "title": incident.get("title"),
                    "section": incident.get("section"),
                    "distance": incident.get("distance"),
                })
    return support


def score_attack_patterns(timeline: dict, retrieved_incidents: list) -> dict:
    """
    Returns {category: {"direct_signals": [...], "retrieval_support": [...],
    "is_candidate": bool}} for all 9 taxonomy categories, always - categories
    with zero evidence still appear, with empty lists, so downstream code
    (Step 3.4's prompt builder) never has to special-case a missing key.

    is_candidate is True if there is ANY evidence at all (direct or
    retrieval-based). It is a flag for "worth Step 3.4's narration
    considering this," never a confidence score or a classification.
    """
    retrieval_support = _retrieval_support_by_category(retrieved_incidents)

    results = {}
    for category in TAXONOMY_CATEGORIES:
        detector = _DIRECT_SIGNAL_DETECTORS.get(category)
        direct_signals = detector(timeline) if detector else []
        support = retrieval_support.get(category, [])

        results[category] = {
            "direct_signals": direct_signals,
            "retrieval_support": support,
            "is_candidate": bool(direct_signals or support),
        }

    return results