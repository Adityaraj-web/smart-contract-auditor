import RiskBadge from "./RiskBadge";
import FindingCard from "./FindingCard";
import { AttestResult } from "@/lib/types";

interface AuditReportProps {
  result: AttestResult;
}

export default function AuditReport({ result }: AuditReportProps) {
  const { report, attested, already_attested, tx_hash, block_number, reason } = result;

  return (
    <div className="mt-8 space-y-4">

      {/* ── Report header ──────────────────────────────────────── */}
      <div className="bg-[#0c0e16] border border-[#1b2235] rounded-lg p-5">

        {/* Risk + attestation status */}
        <div className="flex items-start justify-between gap-6 flex-wrap">

          <div className="space-y-2">
            <p className="font-mono text-xs text-[#5d6d88] uppercase tracking-widest">
              overall risk
            </p>
            <RiskBadge level={report.overall_risk} showDescription />
          </div>

          <div className="text-right space-y-1.5">
            {attested ? (
              <>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded border border-green-500/30 bg-green-500/10 font-mono text-xs text-green-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-400 shrink-0" />
                  {already_attested ? "previously attested" : "attested on-chain"}
                </span>
                <div className="space-y-0.5 pt-0.5">
                  {tx_hash ? (
                    <>
            
                      <a 
                        href={`https://sepolia.etherscan.io/tx/0x${tx_hash}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block font-mono text-xs text-[#38bdf8] hover:text-[#7dd3fc] transition-colors"
                      >
                        0x{tx_hash.slice(0, 8)}…{tx_hash.slice(-6)} ↗
                      </a>
                      {block_number && (
                        <p className="font-mono text-xs text-[#5d6d88]">
                          block {block_number.toLocaleString()} · sepolia
                        </p>
                      )}
                    </>
                  ) : (
                    <p className="font-mono text-xs text-[#5d6d88]">
                      attested on-chain · record not in local db
                    </p>
                  )}
                </div>
              </>
            ) : (
              <>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded border border-yellow-500/30 bg-yellow-500/10 font-mono text-xs text-yellow-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 shrink-0" />
                  not attested
                </span>
                {reason && (
                  <p className="font-mono text-xs text-[#5d6d88] max-w-48 text-right leading-relaxed pt-1">
                    {reason}
                  </p>
                )}
              </>
            )}
          </div>
        </div>

        {/* Summary */}
        <div className="mt-5 pt-4 border-t border-[#1b2235] space-y-2">
          <p className="font-mono text-xs text-[#5d6d88] uppercase tracking-widest">
            summary
          </p>
          <p className="text-[#c8d0e7] text-sm leading-relaxed">
            {report.summary}
          </p>
        </div>

        {/* Meta row — bumped up from near-invisible #2a3450 */}
        <div className="mt-4 pt-3 border-t border-[#1b2235] flex gap-5">
          <span className="font-mono text-xs text-[#5d6d88]">
            {report.findings.length} finding{report.findings.length !== 1 ? "s" : ""}
          </span>
          <span className="font-mono text-xs text-[#5d6d88]">
            {report.rag_context_used.length > 0
              ? `${report.rag_context_used.length} rag source${report.rag_context_used.length !== 1 ? "s" : ""}`
              : "no rag context"}
          </span>
        </div>
      </div>

      {/* ── Findings ───────────────────────────────────────────── */}
      {report.findings.length > 0 ? (
        <div className="space-y-2">
          <p className="font-mono text-xs text-[#5d6d88] uppercase tracking-widest px-1 pt-2">
            findings
          </p>
          {report.findings.map((finding, i) => (
            <FindingCard key={finding.id ?? i} finding={finding} index={i} />
          ))}
        </div>
      ) : (
        <div className="bg-[#0c0e16] border border-[#1b2235] rounded-lg p-8 text-center">
          <p className="font-mono text-sm text-[#5d6d88]">no findings detected</p>
        </div>
      )}

    </div>
  );
}