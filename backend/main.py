import os
import json
import subprocess
import tempfile
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, Dict, Any


from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.retrieval import retrieve_context
from backend.prompt_builder import build_audit_prompt
from backend.ollama_client import generate_audit_report
from backend.blockchain import submit_attestation
from backend.chat import run_chat_turn

app = FastAPI(title="Smart Contract Auditor")

class ChatRequest(BaseModel):
    report: dict
    history: list[dict]
    message: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SLITHER_TIMEOUT = 300
ATTESTATION_THRESHOLD = {"Low", "Medium", "Informational", "Optimization"}


# ── internal helper ────────────────────────────────────────────────────────────

def _parse_slither_output(result_json: dict) -> list[dict]:
    findings = []
    for detector_result in result_json.get("results", {}).get("detectors", []):
        findings.append(
            {
                "id": detector_result.get("check", "unknown"),
                "detector": detector_result.get("check", "unknown"),
                "impact": detector_result.get("impact", "Unknown"),
                "confidence": detector_result.get("confidence", "Unknown"),
                "description": detector_result.get("description", ""),
            }
        )
    return findings


def _run_slither(file_path: str) -> list[dict]:
    try:
        result = subprocess.run(
            ["slither", file_path, "--json", "-"],
            capture_output=True,
            text=True,
            timeout=SLITHER_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=503,
            detail=f"Slither timed out after {SLITHER_TIMEOUT}s. Your system may be under memory pressure. Close other applications and retry."
        )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    return _parse_slither_output(data)

def _compute_risk_level(findings: list[dict]) -> str:
    """
    Derives overall risk deterministically from Slither impact levels.
    LLM output is overridden by this for the attestation threshold decision.
    """
    priority = ["Critical", "High", "Medium", "Low", "Informational", "Optimization"]
    impacts = {f.get("impact", "Informational") for f in findings}
    for level in priority:
        if level in impacts:
            return level
    return "Low"


def _run_full_audit(contract_source: str, file_path: str) -> dict:
    findings = _run_slither(file_path)
    descriptions = [f["description"] for f in findings if f.get("description")]
    rag_chunks = retrieve_context(descriptions) if descriptions else []
    prompt = build_audit_prompt(findings, rag_chunks)
    report = generate_audit_report(prompt)
    report_dict = report.model_dump()

    # Override LLM's risk assessment with deterministic calculation
    report_dict["overall_risk"] = _compute_risk_level(findings)

    return report_dict


# ── endpoints ──────────────────────────────────────────────────────────────────

@app.post("/audit/slither")
async def audit_slither(file: UploadFile = File(...)):
    """Runs Slither only — fast, no LLM."""
    content = await file.read()
    with tempfile.NamedTemporaryFile(
        suffix=".sol", delete=False, mode="wb"
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        findings = _run_slither(tmp_path)
        return {"findings": findings, "total": len(findings)}
    finally:
        os.unlink(tmp_path)


@app.post("/audit/full")
async def audit_full(file: UploadFile = File(...)):
    """Full pipeline: Slither → RAG → Ollama. Returns structured audit report."""
    content = await file.read()
    contract_source = content.decode("utf-8")

    with tempfile.NamedTemporaryFile(
        suffix=".sol", delete=False, mode="wb"
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        report_dict = _run_full_audit(contract_source, tmp_path)
        return report_dict
    finally:
        os.unlink(tmp_path)


@app.post("/audit/attest")
async def audit_attest(file: UploadFile = File(...)):
    """
    Full pipeline + on-chain attestation if risk level passes threshold.
    Threshold: Low or Medium → attest. High or Critical → no attestation.
    """
    content = await file.read()
    contract_source = content.decode("utf-8")

    with tempfile.NamedTemporaryFile(
        suffix=".sol", delete=False, mode="wb"
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        report_dict = _run_full_audit(contract_source, tmp_path)
    finally:
        os.unlink(tmp_path)

    risk_level = report_dict.get("overall_risk", "High")

    # Threshold check
    if risk_level not in ATTESTATION_THRESHOLD:
        return {
            "attested": False,
            "reason": f"Risk level '{risk_level}' does not meet attestation threshold (Low or Medium only).",
            "report": report_dict,
        }

    # Submit on-chain
    report_json = json.dumps(report_dict, sort_keys=True)
    try:
        attestation = submit_attestation(
            contract_source=contract_source,
            risk_level=risk_level,
            report_json=report_json,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Audit passed threshold but attestation failed: {str(e)}",
        )

    return {
        "attested": True,
        "already_attested": attestation.get("already_attested", False),
        "tx_hash": attestation["tx_hash"],
        "contract_hash": attestation["contract_hash"],
        "report_hash": attestation["report_hash"],
        "block_number": attestation["block_number"],
        "risk_level": risk_level,
        "report": report_dict,
    }

@app.post("/audit/chat")
async def audit_chat(req: ChatRequest):
    """
    One turn of agentic follow-up chat about an audit report.
    The frontend sends the full report + conversation history + new message.
    Returns the assistant's response as plain text.
    """
    try:
        reply = run_chat_turn(
            report=req.report,
            history=req.history,
            user_message=req.message,
        )
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════
# FORENSICS ENDPOINTS (Phase 4) — everything below is new.
# Nothing above this line has been modified.
# ══════════════════════════════════════════════════════════════════════════

from backend.forensics_report_generator import generate_forensics_report
from backend.forensics_ingest import TransactionNotFoundError
from backend.blockchain import submit_forensics_attestation


class ForensicsRequest(BaseModel):
    tx_hash: str
    chain: str
    include_window: bool = False
    block_window: int = 2
    report: Optional[Dict[str, Any]] = None

def _validate_provided_report(report: dict, req: "ForensicsRequest") -> None:
    if report.get("tx_hash") != req.tx_hash:
        raise HTTPException(
            status_code=400,
            detail=f"Provided report's tx_hash ({report.get('tx_hash')}) does not match request tx_hash ({req.tx_hash})."
        )
    if report.get("chain") != req.chain:
        raise HTTPException(
            status_code=400,
            detail=f"Provided report's chain ({report.get('chain')}) does not match request chain ({req.chain})."
        )
    if report.get("schema_version") != "forensics-report-v1":
        raise HTTPException(
            status_code=400,
            detail=f"Provided report has unrecognized schema_version: {report.get('schema_version')!r}."
        )


def _run_full_forensics(req: "ForensicsRequest") -> dict:
    """
    Shared by both forensics endpoints. Wraps generate_forensics_report()
    and translates TransactionNotFoundError (a bad hash, or a hash that
    doesn't exist on the given chain) into a 404 rather than a generic 500 —
    mirroring how a genuinely bad input should read differently from an
    internal failure.
    """
    try:
        return generate_forensics_report(
            tx_hash=req.tx_hash,
            chain=req.chain,
            include_window=req.include_window,
            block_window=req.block_window,
        )
    except TransactionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/forensics/generate")
async def forensics_generate(req: ForensicsRequest):
    """Full Phase 3 pipeline only — no attestation. Mirrors /audit/full."""
    report = _run_full_forensics(req)
    return report


@app.post("/forensics/attest")
async def forensics_attest(req: ForensicsRequest):
    """
    Full pipeline + gated on-chain attestation. Mirrors /audit/attest.

    If req.report is provided, that exact report is attested as-is (after
    sanity checks) rather than regenerated — the explorer UI always uses
    this path, so the attested report is guaranteed identical to whatever
    the user reviewed via /forensics/generate. Regenerating here would risk
    attesting a different narrative than the one actually reviewed, since
    the LLM is not deterministic run-to-run.

    If req.report is omitted, this endpoint runs the full pipeline itself
    (standalone use — scripting, testing, or calling /forensics/attest
    directly without a prior /forensics/generate call).
    """
    if req.report is not None:
        _validate_provided_report(req.report, req)
        report = req.report
    else:
        report = _run_full_forensics(req)

    if report.get("narrative_validation_failed"):
        return {"attested": False, "reason": "narrative_validation_failed=True — not attestable.", "report": report}
    narrative = report.get("narrative")
    if not narrative:
        return {"attested": False, "reason": "No narrative generated — not attestable.", "report": report}
    candidate_categories = [a["category"] for a in narrative["category_assessments"]]
    has_conflation_flags = len(report.get("protocol_conflation_flags", [])) > 0
    has_fabricated_evidence_flags = len(report.get("fabricated_evidence_flags", [])) > 0
    has_any_quality_flags = has_conflation_flags or has_fabricated_evidence_flags
    report_json = json.dumps(report, sort_keys=True)
    try:
        attestation = submit_forensics_attestation(
            tx_hash=report["tx_hash"], chain=report["chain"], report_json=report_json,
            candidate_categories=candidate_categories, has_conflation_flags=has_any_quality_flags,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forensics report generated but attestation failed: {str(e)}")
    return {
        "attested": True,
        "already_attested": attestation.get("already_attested", False),
        "attestation_tx_hash": attestation.get("attestation_tx_hash"),
        "tx_hash": attestation.get("tx_hash"),
        "chain": attestation.get("chain"),
        "chain_id": attestation.get("chain_id"),
        "report_hash": attestation.get("report_hash"),
        "category_bitmask": attestation.get("category_bitmask"),
        "has_conflation_flags": has_conflation_flags,
        "has_fabricated_evidence_flags": has_fabricated_evidence_flags,
        "has_any_quality_flags_onchain": attestation.get("has_conflation_flags"),
        "block_number": attestation.get("block_number"),
        "report": report,
    }