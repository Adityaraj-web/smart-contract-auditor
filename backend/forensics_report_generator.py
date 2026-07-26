"""
backend/forensics_report_generator.py

Step 3.5: the top-level Phase 3 entry point. Ties together every prior step
into one call:

  ingest_transaction (Phase 2)
    -> build_timeline (3.1)
    -> build_forensics_queries (3.2) -> retrieve_forensics_context (3.2)
    -> score_attack_patterns (3.3)
    -> build_forensics_prompt (3.4) -> generate_forensics_narrative (3.4)
    -> final assembly, with an explicit validation step ensuring the LLM's
       category_assessments actually match the candidate categories it was
       given - exactly, not approximately - since Pydantic's structural
       validation alone only checks shape, not whether the LLM respected the
       "these categories, no others" instruction.

Mirrors the existing audit pipeline's core principle throughout: Python
computes and owns every fact; the LLM only narrates. Where the LLM's output
can't be reconciled with the deterministic evidence after retries, this is
surfaced explicitly (narrative_validation_failed=True, with the raw
mismatched output attached) rather than silently patched, discarded, or
hidden - the same "loud failure over silent wrong answer" principle behind
TransactionNotFoundError and the required chain argument back in Phase 2.

PHASE 4 IMPORT NOTE: each import below prefers the package-style form
(backend.X) so this module shares the SAME retrieval/ollama_client module
instance as main.py — critical for retrieval.py in particular, since it
holds a module-level ChromaDB PersistentClient; loading it twice under two
different module names (backend.retrieval vs. retrieval) in one process
would open two separate clients against the same on-disk Chroma path.
Falls back to the flat import so this file still runs unchanged standalone
from inside backend/, exactly as in Phase 3 (e.g.
`python forensics_report_smoketest.py`).
"""

try:
    from backend.forensics_ingest import ingest_transaction
except ImportError:
    from forensics_ingest import ingest_transaction

try:
    from backend.timeline_builder import build_timeline
except ImportError:
    from timeline_builder import build_timeline

try:
    from backend.query_builder import build_forensics_queries
except ImportError:
    from query_builder import build_forensics_queries

try:
    from backend.retrieval import retrieve_forensics_context
except ImportError:
    from retrieval import retrieve_forensics_context

try:
    from backend.attack_pattern_scoring import score_attack_patterns
except ImportError:
    from attack_pattern_scoring import score_attack_patterns

try:
    from backend.forensics_prompt_builder import build_forensics_prompt
except ImportError:
    from forensics_prompt_builder import build_forensics_prompt

try:
    from backend.ollama_client import generate_forensics_narrative
except ImportError:
    from ollama_client import generate_forensics_narrative


def _validate_category_match(forensics_narrative, candidate_categories: list) -> bool:
    """Checks the LLM returned assessments for exactly the candidate
    categories it was given - same set, same count. Order isn't enforced
    here (harmless if the LLM reorders them), only identity/completeness."""
    returned = {a.category for a in forensics_narrative.category_assessments}
    expected = set(candidate_categories)
    return returned == expected


# Comparison-language markers that make a retrieved protocol's name a
# legitimate comparison rather than a false attribution. Deliberately a
# plain substring list, not full NLP - this is a heuristic safety net, not
# a perfect grounding verifier, and is documented as such below.
_COMPARISON_MARKERS = [
    "resembl", "similar to", "similar in", "comparable to", "reminiscent of",
    "akin to", "as seen in", "as with", "consistent with", "like the",
    "pattern seen in", "echoes",
]
_CONFLATION_CHECK_WINDOW = 60  # chars to look back before a protocol mention


def _check_fabricated_evidence(narrative, pattern_scores: dict) -> list:
    """
    DELIBERATE HEURISTIC, not a perfect check - same spirit as
    _check_protocol_conflation below, but catching a DIFFERENT failure mode
    surfaced by live Phase 4 testing: a category_assessment explicitly
    claiming "[direct evidence]" (the same bracket-tag convention
    forensics_prompt_builder.py's _format_candidate_categories uses when
    presenting direct_signals to the model) for a category where Step 3.3's
    pattern_scores actually recorded ZERO direct_signals - i.e. the model
    asserted a specific fact about THIS transaction's own on-chain evidence
    (e.g. "the same event was emitted") that was never actually observed.

    This is a stricter failure than protocol conflation: conflation borrows
    a real historical protocol's name; this asserts a false fact about the
    evidence Python itself already computed and handed the model. Caught
    directly on a real transaction with zero decoded logs, where several
    category_assessments still claimed "[direct evidence]" despite
    log_sequence and internal_call_sequence both being empty.

    Like _check_protocol_conflation, this is a substring-based heuristic, not
    semantic verification: it can miss a fabricated claim phrased without the
    "[direct evidence]" tag, and could in principle flag a legitimate
    assessment that happens to use that phrase as a hedge rather than a
    factual claim. Documented as a safety net, not a guarantee.

    Returns a list of {"category", "llm_assessment"} flags - empty if none
    found.
    """
    flags = []
    for assessment in narrative.category_assessments:
        category = assessment.category
        text_lower = assessment.llm_assessment.lower()
        claims_direct_evidence = (
            "[direct evidence]" in text_lower or "direct evidence" in text_lower
        )
        if not claims_direct_evidence:
            continue

        direct_signals = pattern_scores.get(category, {}).get("direct_signals", [])
        if not direct_signals:
            flags.append({
                "category": category,
                "llm_assessment": assessment.llm_assessment,
            })
    return flags


def _check_protocol_conflation(narrative, retrieved_incidents: list) -> list:
    """
    DELIBERATE HEURISTIC, not a perfect check - real prompt-engineering
    attempts (see forensics_prompt_builder.py's explicit anti-conflation
    rule + bad/good example) did not reliably stop a 3B model from stating
    a retrieved historical incident's protocol name as if it were the
    actual subject of THIS transaction, sometimes in the same response that
    also correctly used comparison language elsewhere. Rather than trust
    the LLM to self-police this instruction, this scans its own output
    afterward: for every occurrence of a retrieved protocol's name in any
    narrative field, checks whether a comparison marker appears in the
    preceding text. If not, that specific occurrence is flagged.

    This can have false positives (a legitimate comparison phrased in a way
    this substring list doesn't recognize) and false negatives (a
    conflation phrased in a way that happens to have a marker word nearby
    without actually being a real comparison). It is a safety net that
    catches the failure pattern actually observed, not a semantic guarantee.

    Returns a list of {"field", "protocol", "snippet"} flags - empty if none
    found.
    """
    protocol_names = {
        incident.get("protocol") for incident in retrieved_incidents if incident.get("protocol")
    }
    if not protocol_names:
        return []

    fields_to_check = {
        "summary": narrative.summary,
        "timeline_narrative": narrative.timeline_narrative,
        "root_cause_narrative": narrative.root_cause_narrative,
        "why_it_matters": narrative.why_it_matters,
    }
    for assessment in narrative.category_assessments:
        fields_to_check[f"category_assessment[{assessment.category}]"] = assessment.llm_assessment

    flags = []
    for field_name, text in fields_to_check.items():
        if not text:
            continue
        lower_text = text.lower()
        for protocol in protocol_names:
            search_start = 0
            protocol_lower = protocol.lower()
            while True:
                idx = lower_text.find(protocol_lower, search_start)
                if idx == -1:
                    break
                window_start = max(0, idx - _CONFLATION_CHECK_WINDOW)
                preceding_text = lower_text[window_start:idx]
                has_marker = any(marker in preceding_text for marker in _COMPARISON_MARKERS)
                if not has_marker:
                    snippet_start = max(0, idx - 30)
                    snippet_end = min(len(text), idx + len(protocol) + 30)
                    flags.append({
                        "field": field_name,
                        "protocol": protocol,
                        "snippet": text[snippet_start:snippet_end],
                    })
                search_start = idx + len(protocol_lower)
    return flags


def generate_forensics_report(
    tx_hash: str,
    chain: str,
    include_window: bool = False,
    block_window: int = 2,
    api_key: str = None,
    top_k_retrieval: int = 3,
    max_narrative_retries: int = 2,
) -> dict:
    """
    Full Phase 3 pipeline: given a tx_hash + chain, returns one assembled
    forensics report dict combining deterministic evidence (ingestion,
    timeline, pattern scores) with LLM narration.

    chain must be passed explicitly - same reasoning as ingest_transaction
    and EtherscanClient itself: no silent default, given the real risk of
    running against the wrong network.
    """
    # ---- Phase 2: ingestion ----
    ingest_result = ingest_transaction(
        tx_hash=tx_hash,
        chain=chain,
        include_window=include_window,
        block_window=block_window,
        api_key=api_key,
    )

    # ---- 3.1: deterministic timeline ----
    timeline = build_timeline(ingest_result)

    # ---- 3.2: retrieval ----
    queries = build_forensics_queries(ingest_result, timeline)
    retrieved_incidents = retrieve_forensics_context(queries, top_k=top_k_retrieval)

    # ---- 3.3: attack-pattern candidate scoring ----
    pattern_scores = score_attack_patterns(timeline, retrieved_incidents)

    # ---- 3.4: prompt + generation, with category-match validation ----
    prompt, candidate_categories = build_forensics_prompt(
        timeline, pattern_scores, retrieved_incidents, ingest_result["contracts"]
    )

    narrative = None
    narrative_validation_failed = False
    last_invalid_narrative = None

    for attempt in range(1, max_narrative_retries + 1):
        candidate_narrative = generate_forensics_narrative(prompt)
        if _validate_category_match(candidate_narrative, candidate_categories):
            narrative = candidate_narrative
            break
        last_invalid_narrative = candidate_narrative
        print(
            f"[forensics_report_generator] Narrative attempt {attempt}: category "
            f"mismatch (expected {candidate_categories}, got "
            f"{[a.category for a in candidate_narrative.category_assessments]})"
        )
    else:
        # Exhausted retries without a matching response - surface this
        # explicitly rather than silently accepting a mismatched narrative
        # or fabricating one that matches what was expected.
        narrative_validation_failed = True

    # ---- Deterministic post-generation check: protocol-name conflation ----
    # Run even when category-match validation passed - that check only
    # confirms the RIGHT categories were assessed, not that the prose
    # describing them is actually grounded in this transaction rather than
    # a retrieved incident.
    protocol_conflation_flags = (
        _check_protocol_conflation(narrative, retrieved_incidents) if narrative else []
    )

    # ---- Deterministic post-generation check: fabricated direct evidence ----
    # Separate from protocol conflation - this catches a stricter failure:
    # an assessment claiming "[direct evidence]" for a category where
    # pattern_scores recorded no direct_signals at all, i.e. a false factual
    # claim about this transaction's own evidence rather than a borrowed
    # historical name. See _check_fabricated_evidence's docstring for the
    # real case that surfaced this gap.
    fabricated_evidence_flags = (
        _check_fabricated_evidence(narrative, pattern_scores) if narrative else []
    )

    # ---- Final assembly ----
    report = {
        "schema_version": "forensics-report-v1",
        "tx_hash": tx_hash,
        "chain": chain,
        "timeline": timeline,
        "pattern_scores": pattern_scores,
        "retrieved_incidents": retrieved_incidents,
        "narrative": narrative.model_dump() if narrative else None,
        "narrative_validation_failed": narrative_validation_failed,
        "raw_invalid_narrative": (
            last_invalid_narrative.model_dump()
            if narrative_validation_failed and last_invalid_narrative
            else None
        ),
        "protocol_conflation_flags": protocol_conflation_flags,
        "fabricated_evidence_flags": fabricated_evidence_flags,
    }

    return report