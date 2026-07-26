"""
backend/forensics_prompt_builder.py

Step 3.4 (prompt side): builds the LLM prompt for forensics report
narration, mirroring build_audit_prompt's discipline of strict, explicit
constraints on what the LLM is and isn't allowed to add.

Key constraint, directly analogous to audit's "EXACTLY {finding_count}
findings" rule: the LLM may only discuss taxonomy categories that Step 3.3
already flagged as candidates (is_candidate=True). Categories with no
evidence at all are never shown to the LLM in the first place - not shown
and told "don't mention this" but simply absent - so there's nothing for it
to latch onto and narrate around.

The LLM's job here is narration only: plain-language summary, root-cause
explanation, and an assessment of each candidate category's plausibility
given the evidence already gathered. It does not get to invent facts (tx
values, addresses, event names) beyond what's included below, and it does
not get to assert a final single category - every category assessment must
explicitly reference whether it's supported by direct transaction evidence,
retrieval similarity to historical incidents, or both, so the eventual
report reader can see exactly what kind of evidence backs each claim.
"""


def _format_log_sequence(log_sequence: list, max_logs: int = 30) -> str:
    """Truncates to the first max_logs entries with a note, rather than
    dumping all 56+ logs from an incident like Euler into the prompt -
    keeps prompt size reasonable for an 8192-token context window shared
    with everything else being included."""
    lines = []
    for log in log_sequence[:max_logs]:
        if log.get("decode_method") == "undecoded":
            lines.append(f"  [log {log.get('log_index')}] (undecoded event, "
                          f"topic0={log.get('raw_topic0')})")
        else:
            lines.append(f"  [log {log.get('log_index')}] {log.get('event_name')} "
                          f"({log.get('standard')}) args={log.get('args')}")
    if len(log_sequence) > max_logs:
        lines.append(f"  ... ({len(log_sequence) - max_logs} further logs omitted for brevity)")
    return "\n".join(lines) if lines else "  (no decoded logs)"


def _format_internal_calls(internal_sequence: list) -> str:
    lines = []
    for entry in internal_sequence:
        create_note = f" [CREATED {entry['contract_address']}]" if entry.get("contract_address") else ""
        lines.append(
            f"  [{entry['sequence_index']}] {entry.get('call_type')}: "
            f"{entry.get('from_address')} -> {entry.get('to_address')}{create_note}"
        )
    return "\n".join(lines) if lines else "  (no internal calls with non-zero value - see limitations)"


def _format_candidate_categories(pattern_scores: dict) -> tuple:
    """Returns (formatted_text, candidate_category_list) - the list is used
    later to enforce the 'exactly these categories, no others' prompt rule."""
    candidates = {cat: data for cat, data in pattern_scores.items() if data["is_candidate"]}

    if not candidates:
        return "  (no taxonomy category has any supporting evidence)", []

    lines = []
    for category, data in candidates.items():
        lines.append(f"\n  Category: {category}")
        for signal in data["direct_signals"]:
            lines.append(f"    - [direct evidence] {signal}")
        for support in data["retrieval_support"]:
            lines.append(
                f"    - [historical similarity] resembles '{support['title']}' "
                f"({support['protocol']}, section: {support['section']}, "
                f"distance: {support['distance']})"
            )
    return "\n".join(lines), list(candidates.keys())


def _format_retrieved_incidents(retrieved_incidents: list) -> str:
    if not retrieved_incidents:
        return "  (no historical incidents retrieved)"
    lines = []
    for incident in retrieved_incidents:
        lines.append(
            f"\n--- {incident['title']} ({incident['protocol']}, {incident['date']}, "
            f"section: {incident['section']}) ---\n{incident['text']}"
        )
    return "\n".join(lines)


def _format_contracts(contracts: dict) -> str:
    """Surfaces the REAL, verified contract names actually involved in this
    transaction (from Phase 2's getsourcecode resolution) as a concrete
    grounding fact. Added specifically to counter a real observed failure:
    without any concrete proper noun for 'what this transaction actually
    is', a 3B model reached for the retrieved historical incidents' protocol
    names instead and stated one of them as the subject of this transaction
    (e.g. claiming a real Euler Finance tx was "on Beanstalk Farms"). Giving
    it this transaction's own real names first is a stronger anchor than an
    instruction alone."""
    if not contracts:
        return "  (no contract information available)"
    lines = []
    for address, info in contracts.items():
        if info.get("verified"):
            name = info.get("contract_name") or "(verified, name unavailable)"
            lines.append(f"  {address}: VERIFIED - {name}")
        else:
            lines.append(f"  {address}: unverified")
    return "\n".join(lines)


def build_forensics_prompt(
    timeline: dict,
    pattern_scores: dict,
    retrieved_incidents: list,
    contracts: dict,
) -> str:
    """
    Builds the full forensics narration prompt.

    Returns (prompt_string, candidate_categories) - candidate_categories is
    needed by the caller to validate the LLM's response actually only used
    the categories it was given, mirroring how build_audit_prompt's caller
    validates finding_count against the response.
    """
    tx = timeline["main_transaction"]
    candidates_text, candidate_categories = _format_candidate_categories(pattern_scores)
    category_count = len(candidate_categories)

    prompt = f"""You are a blockchain forensics analyst. Analyze the on-chain evidence below for a suspected exploit transaction and produce a structured post-mortem.

CRITICAL RULES:
- All transaction facts, event data, and internal call data below are ALREADY VERIFIED from on-chain sources. Do not contradict them, and do not invent additional facts (addresses, amounts, event names) not present below.
- THIS TRANSACTION involves ONLY the contracts listed in "CONTRACTS INVOLVED IN THIS TRANSACTION" below. The protocols named in "RETRIEVED HISTORICAL INCIDENTS" are DIFFERENT, PAST incidents used only for comparison - they are NOT what happened in this transaction.
- NEVER state or imply that this transaction happened to, or occurred on, any protocol named only in the historical incidents section. If you reference a retrieved protocol's name, it must appear inside an explicit comparison phrase such as "resembles X" or "similar to X's incident" - never as the subject of a sentence describing what this transaction did.
  BAD (do not do this): "This transaction is a governance attack on Beanstalk Farms."
  GOOD: "This transaction shows a pattern that resembles Beanstalk Farms' governance attack."
- The "category_assessments" array in your response MUST contain EXACTLY {category_count} entries - one for each candidate category listed below, in the order listed. Do NOT add categories that aren't listed. Do NOT omit any that are listed.
- Each category_assessment's "llm_assessment" must explicitly reference whether its evidence is direct (from this transaction) or historical-similarity-based (from retrieved incidents), or both - never present either kind of evidence as more certain than it is.
- This is a candidate assessment, not a final classification - phrase your assessments accordingly (e.g. "consistent with", "resembles", "may indicate"), not as settled conclusions.
- Use the historical incident context to inform your explanations and comparisons, not as a source of facts about THIS transaction.

TRANSACTION FACTS:
  tx_hash: {tx['tx_hash']}
  chain: {tx['chain']}
  block_number: {tx['block_number']}
  block_timestamp: {tx['block_timestamp']}
  from_address: {tx['from_address']}
  to_address: {tx['to_address']}
  status: {tx['status']} ({"success" if tx['status'] == '0x1' else "reverted" if tx['status'] == '0x0' else "unknown"})

CONTRACTS INVOLVED IN THIS TRANSACTION (the ONLY real subject of this analysis):
{_format_contracts(contracts)}

INTERNAL CALL SEQUENCE (own ordering track - see limitations, NOT interleaved with logs below):
{_format_internal_calls(timeline['internal_call_sequence'])}

DECODED EVENT LOG SEQUENCE (own ordering track, by log index):
{_format_log_sequence(timeline['log_sequence'])}

KNOWN LIMITATIONS IN THIS EVIDENCE (factor these into your confidence language):
{chr(10).join(f"  - {note}" for note in timeline['limitations'])}

CANDIDATE ATTACK PATTERN CATEGORIES ({category_count} total - respond with exactly these, no others):
{candidates_text}

RETRIEVED HISTORICAL INCIDENTS (DIFFERENT, PAST incidents - reference material for comparison ONLY, never facts about this transaction):
{_format_retrieved_incidents(retrieved_incidents)}

Respond with ONLY a valid JSON object in this exact structure, no explanation or markdown:
{{
  "summary": "2-3 sentence plain English summary of what this transaction did, based only on the facts above - must name only the contracts listed in CONTRACTS INVOLVED IN THIS TRANSACTION, never a retrieved incident's protocol",
  "timeline_narrative": "plain English walkthrough of the sequence of events, honestly noting where internal calls and logs could not be merged into one true order",
  "root_cause_narrative": "plausible explanation of what went wrong, grounded in the evidence above and comparisons to retrieved historical incidents where relevant - explicitly note this is an interpretation, not a certainty, and phrase any retrieved-incident reference as a comparison, not a fact about this transaction",
  "why_it_matters": "plain English explanation of the impact/significance of this type of exploit",
  "category_assessments": [
    {{
      "category": "exact category name from the candidate list above",
      "llm_assessment": "plausibility assessment referencing direct evidence and/or historical similarity, phrased as an interpretation not a fact"
    }}
  ],
  "historical_citations_used": ["list of historical incident titles that informed your narrative"]
}}

Remember: exactly {category_count} category_assessments, matching the {category_count} candidate categories above, in order."""

    return prompt, candidate_categories