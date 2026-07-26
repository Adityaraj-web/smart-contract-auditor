import json
import re
import httpx
from pydantic import BaseModel, ValidationError
from typing import List, Optional


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"
MAX_RETRIES = 2

# Forensics responses ask for substantially more generated prose than the
# audit report (summary + timeline_narrative + root_cause_narrative +
# why_it_matters + a full category_assessments array with an explanation
# per category, vs. audit's more compact structure). On CPU-only inference,
# that reliably needs more wall-clock time - this is a real cost of
# forensics' richer output shape, not a sign anything is broken. Kept as a
# SEPARATE constant so the audit path's existing timeout=300.0 (proven to
# work reliably for its own, shorter output) is never touched.
FORENSICS_TIMEOUT_SECONDS = 900.0


class AuditFinding(BaseModel):
    id: int
    detector: str
    impact: str
    confidence: str
    title: str
    explanation: str
    recommendation: str


class AuditReport(BaseModel):
    overall_risk: str
    summary: str
    findings: List[AuditFinding]
    rag_context_used: List[str]


def _strip_markdown_fences(raw: str) -> str:
    """Shared by both audit and forensics parsing - factored out here so the
    fence-stripping logic exists in exactly one place, but this is a pure
    refactor: _parse_response's external behavior for the audit path is
    completely unchanged."""
    clean = raw.strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```[a-z]*\n?", "", clean)
        clean = re.sub(r"\n?```$", "", clean)
        clean = clean.strip()
    return clean


def _parse_response(raw: str) -> AuditReport:
    """Parse and validate the raw LLM string response into AuditReport.
    UNCHANGED behavior from the original - still audit-specific."""
    clean = _strip_markdown_fences(raw)
    data = json.loads(clean)
    return AuditReport(**data)


def generate_audit_report(prompt: str) -> AuditReport:
    """
    Send prompt to Ollama and return a validated AuditReport.
    Retries up to MAX_RETRIES times on JSON parse or validation failure.

    UNCHANGED from the original - every existing call site in main.py keeps
    working exactly as before.
    """
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = httpx.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent structured output
                        "num_ctx": 8192
                    }
                },
                timeout=300.0  # CPU inference is slow — 5 min ceiling
            )
            response.raise_for_status()

            raw_text = response.json()["response"]
            return _parse_response(raw_text)

        except (json.JSONDecodeError, ValidationError, KeyError) as e:
            last_error = e
            print(f"[ollama_client] Attempt {attempt} failed: {e}")
            continue

        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama HTTP error: {e}")

    raise RuntimeError(
        f"Failed to get valid response after {MAX_RETRIES} attempts. Last error: {last_error}"
    )


# ── forensics additions (Step 3.4) ──────────────────────────────────────────
# Reuses the SAME model, URL, retry count, and generation settings as the
# audit path above - there is no qwen2.5-coder:7b -> llama3.2:3b cascade
# actually present in this file to reuse (an earlier project summary implied
# one, but the real code here only ever used a single model with
# retry-on-parse-failure), so this mirrors what's ACTUALLY here rather than
# inventing a fallback that was never implemented.

class ForensicsCategoryAssessment(BaseModel):
    category: str
    llm_assessment: str


class ForensicsReport(BaseModel):
    summary: str
    timeline_narrative: str
    root_cause_narrative: str
    why_it_matters: str
    category_assessments: List[ForensicsCategoryAssessment]
    historical_citations_used: List[str]


def _parse_forensics_response(raw: str) -> ForensicsReport:
    clean = _strip_markdown_fences(raw)
    data = json.loads(clean)
    return ForensicsReport(**data)


def generate_forensics_narrative(prompt: str) -> ForensicsReport:
    """
    Send a forensics prompt to Ollama and return a validated ForensicsReport.
    Retries up to MAX_RETRIES times on JSON parse or validation failure -
    identical retry discipline to generate_audit_report, just against a
    different response schema.

    Named generate_forensics_narrative (not generate_forensics_report) to
    keep it clearly distinct from Step 3.5's top-level orchestrator function,
    which will be named generate_forensics_report(tx_hash, chain, ...) and
    calls this one internally alongside ingestion, timeline-building, etc.
    """
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = httpx.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_ctx": 8192
                    }
                },
                timeout=FORENSICS_TIMEOUT_SECONDS  # richer output shape needs more wall-clock time on CPU inference - see constant definition above
            )
            response.raise_for_status()

            raw_text = response.json()["response"]
            return _parse_forensics_response(raw_text)

        except (json.JSONDecodeError, ValidationError, KeyError) as e:
            last_error = e
            print(f"[ollama_client] Forensics attempt {attempt} failed: {e}")
            continue

        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama HTTP error: {e}")

    raise RuntimeError(
        f"Failed to get valid forensics response after {MAX_RETRIES} attempts. "
        f"Last error: {last_error}"
    )