import json
import re
import httpx
from pydantic import BaseModel, ValidationError
from typing import List, Optional


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"
MAX_RETRIES = 2


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


def _parse_response(raw: str) -> AuditReport:
    """Parse and validate the raw LLM string response into AuditReport."""
    # Strip markdown code fences if model adds them despite instructions
    clean = raw.strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```[a-z]*\n?", "", clean)
        clean = re.sub(r"\n?```$", "", clean)
        clean = clean.strip()

    data = json.loads(clean)
    return AuditReport(**data)


def generate_audit_report(prompt: str) -> AuditReport:
    """
    Send prompt to Ollama and return a validated AuditReport.
    Retries up to MAX_RETRIES times on JSON parse or validation failure.
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