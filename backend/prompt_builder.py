import re


def _clean_description(description: str) -> str:
    """Strip noisy temp file paths from Slither descriptions."""
    # Replaces Windows temp paths like C:/Users/.../AppData/Local/Temp/tmpXXXXX/
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

    prompt = f"""You are a smart contract security auditor. You will be given:
1. A list of findings from Slither static analysis
2. Relevant background context on vulnerability types

Your task is to produce a structured audit report in JSON format.

SLITHER FINDINGS:
{findings_section}

BACKGROUND CONTEXT FROM KNOWLEDGE BASE:
{context_section}

Respond with ONLY a valid JSON object in this exact structure, no explanation or markdown:
{{
  "overall_risk": "High" | "Medium" | "Low" | "Informational",
  "summary": "2-3 sentence plain English summary of the contract's security posture",
  "findings": [
    {{
      "id": 1,
      "detector": "detector-name",
      "impact": "High" | "Medium" | "Low" | "Informational" | "Optimization",
      "confidence": "High" | "Medium" | "Low",
      "title": "Short human-readable title",
      "explanation": "Plain English explanation of the vulnerability and its risk",
      "recommendation": "Concrete fix recommendation"
    }}
  ],
  "rag_context_used": ["list of knowledge base titles used to inform this report"]
}}"""

    return prompt