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