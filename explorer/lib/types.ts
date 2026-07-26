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
  id: number;
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
  rag_context_used: string[];
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

// ── Forensics pipeline types ─────────────────────────────────────────────────
// Confirmed against a real forensics_report_output.json (Euler Finance
// incident). Two fields remain genuine guesses, marked below.

export interface ForensicsMainTransaction {
  tx_hash: string;
  chain: string;
  block_number: number;
  block_timestamp: number;
  from_address: string;
  to_address: string;
  status: string;
}

export interface ForensicsInternalCall {
  from_address: string;
  to_address: string;
  value_wei: string | number;  // uint256-range wei amounts; see parseLosslessJson.ts
  contract_address: string;
  input_data: string;
  call_type: string;
  gas: number;
  gas_used: number;
  is_error: boolean;
  err_code: string | null;
  sequence_index: number;
}

export type ForensicsLogArgs = Record<string, string | number | null> | null;

export interface ForensicsLogEntry {
  event_name: string | null;
  standard: string | null;
  args: ForensicsLogArgs;
  decode_method: "verified_abi" | "known_signature" | "undecoded";
  raw_topic0?: string;
  contract_address: string;
  log_index: number;
}

export interface ForensicsDecodeSummary {
  total_logs: number;
  verified_abi_decoded: number;
  known_signature_decoded: number;
  undecoded: number;
}

export interface ForensicsTimeline {
  main_transaction: ForensicsMainTransaction;
  internal_call_sequence: ForensicsInternalCall[];
  log_sequence: ForensicsLogEntry[];
  decode_summary: ForensicsDecodeSummary;
  related_window: unknown | null;  // UNCONFIRMED — always null in observed data
  limitations: string[];
}

export interface ForensicsRetrievalSupport {
  protocol: string;
  title: string;
  section: string;
  distance: number;
}

export interface ForensicsPatternScore {
  direct_signals: unknown[];  // UNCONFIRMED shape — always empty in observed data
  retrieval_support: ForensicsRetrievalSupport[];
  is_candidate: boolean;
}

export interface ForensicsRetrievedIncident {
  text: string;
  protocol: string;
  title: string;
  date: string;
  attack_type: string[];
  chain: string;
  funds_lost_usd: number;
  source: string;
  section: string;
  distance: number;
}

export interface ForensicsCategoryAssessment {
  category: string;
  llm_assessment: string;
}

export interface ForensicsNarrative {
  summary: string;
  timeline_narrative: string;
  root_cause_narrative: string;
  why_it_matters: string;
  category_assessments: ForensicsCategoryAssessment[];
  historical_citations_used: string[];
}

export interface ForensicsConflationFlag {
  field: string;
  protocol: string;
  snippet: string;
}

// UNCONFIRMED shape — always [] in every sample seen so far. Reconstructed
// from _check_fabricated_evidence's description. Verify against a real
// populated example before relying on this in the UI.
export interface ForensicsFabricationFlag {
  category: string;
  claim: string;
  snippet?: string;
}

export interface ForensicsReport {
  schema_version: string;
  tx_hash: string;
  chain: string;
  timeline: ForensicsTimeline;
  pattern_scores: Record<string, ForensicsPatternScore>;
  retrieved_incidents: ForensicsRetrievedIncident[];
  narrative: ForensicsNarrative | null;
  narrative_validation_failed: boolean;
  raw_invalid_narrative: string | null;  // UNCONFIRMED shape when populated
  protocol_conflation_flags: ForensicsConflationFlag[];
  fabricated_evidence_flags: ForensicsFabricationFlag[];
}

export interface ForensicsAttestResult {
  attested: boolean;
  already_attested?: boolean;
  reason?: string;
  attestation_tx_hash?: string;
  tx_hash?: string;
  chain?: string;
  chain_id?: number;
  report_hash?: string;
  category_bitmask?: number;
  has_conflation_flags?: boolean;
  has_fabricated_evidence_flags?: boolean;
  has_any_quality_flags_onchain?: boolean;
  block_number?: number;
  report: ForensicsReport;
}