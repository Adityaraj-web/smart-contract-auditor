export interface Attestation {
  id: string;
  contract_hash: string;
  auditor_address: string;
  risk_level: string;
  report_hash: string;
  tx_hash: string;
  block_number: number;
  attested_at: string;
}

// ── Audit pipeline types ───────────────────────────────────────────────────────

export interface AuditFinding {
  id: number;                  // was string — Python model uses int
  detector: string;
  impact: string;
  confidence: string;
  title: string;
  explanation: string;
  recommendation: string;
}

export interface AuditReport {
  overall_risk: string;
  summary: string;
  findings: AuditFinding[];
  rag_context_used: string[];  // was boolean — Python model returns List[str]
}

export interface AttestResult {
  attested: boolean;
  already_attested?: boolean;
  reason?: string;
  tx_hash?: string;
  contract_hash?: string;
  report_hash?: string;
  block_number?: number;
  risk_level?: string;
  report: AuditReport;
}

// ── Chat types ─────────────────────────────────────────────────────────────────

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}