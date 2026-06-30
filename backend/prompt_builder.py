import re


def _clean_description(description: str) -> str:
    """Strip noisy temp file paths from Slither descriptions."""
    cleaned = re.sub(r"[A-Za-z]:/Users/[^/]+/AppData/Local/Temp/[^/]+/", "", description)
    return cleaned.strip()


def build_audit_prompt(findings: list[dict], rag_chunks: list[dict]) -> str:
    """
    Combine Slither findings and RAG-retrieved context into a structured
    prompt for the LLM.

    findings: list of Finding dicts (check, impact, confidence, description)
    rag_chunks: list of chunk dicts from retrieve_context()
    """

    findings_section = ""
    for i, f in enumerate(findings, 1):
        clean_desc = _clean_description(f["description"])
        findings_section += f"""
Finding {i}:
  Detector: {f["detector"]}
  Impact: {f["impact"]}
  Confidence: {f["confidence"]}
  Description: {clean_desc}
"""

    context_section = ""
    for chunk in rag_chunks:
        swc = f"SWC-{chunk['swc_id']}" if chunk.get("swc_id") else "N/A"
        context_section += f"""
--- {chunk["title"]} (Category: {chunk["category"]}, {swc}) ---
{chunk["text"]}
"""

    finding_count = len(findings)

    prompt = f"""You are a smart contract security auditor. Analyze the Slither static analysis findings below and produce a structured audit report.

CRITICAL RULES:
- The "findings" array in your response MUST contain EXACTLY {finding_count} entries — one per Slither finding listed below.
- Do NOT add findings that are not in the Slither output.
- Do NOT remove or merge any findings.
- Use the background context ONLY to write better explanations and recommendations — it is reference material, not a source of additional findings.
- The "overall_risk" field must reflect the highest impact level seen in the Slither findings.

SLITHER FINDINGS ({finding_count} total):
{findings_section}

BACKGROUND CONTEXT (reference only — do not treat as findings):
{context_section}

Respond with ONLY a valid JSON object in this exact structure, no explanation or markdown:
{{
  "overall_risk": "High" | "Medium" | "Low" | "Informational",
  "summary": "2-3 sentence plain English summary of what Slither found in this contract",
  "findings": [
    {{
      "id": 1,
      "detector": "exact detector name from Slither finding",
      "impact": "exact impact level from Slither finding",
      "confidence": "exact confidence level from Slither finding",
      "title": "short human-readable title for this specific finding",
      "explanation": "plain English explanation of this vulnerability and its risk",
      "recommendation": "concrete fix recommendation for this specific issue"
    }}
  ],
  "rag_context_used": ["list of background context titles that informed your explanations"]
}}

Remember: exactly {finding_count} findings in the array, matching the {finding_count} Slither findings above in order."""

    return prompt