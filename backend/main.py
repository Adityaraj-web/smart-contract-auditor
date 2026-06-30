import os
import json
import subprocess
import tempfile
from pathlib import Path
from pydantic import BaseModel


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