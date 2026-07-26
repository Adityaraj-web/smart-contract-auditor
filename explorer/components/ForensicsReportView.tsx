import { ForensicsReport, ForensicsAttestResult } from "@/lib/types";
import DecodeSummaryStrip from "./DecodeSummaryStrip";
import QualityFlagsPanel from "./QualityFlagsPanel";
import CategoryAssessmentCard from "./CategoryAssessmentCard";

interface ForensicsReportViewProps {
  report: ForensicsReport;
  attestation?: Omit<ForensicsAttestResult, "report">;
}

function truncateHash(str: string, start = 8, end = 6): string {
  return `${str.slice(0, start)}…${str.slice(-end)}`;
}

export default function ForensicsReportView({ report, attestation }: ForensicsReportViewProps) {
  const {
    timeline,
    narrative,
    narrative_validation_failed,
    protocol_conflation_flags,
    fabricated_evidence_flags,
    pattern_scores,
  } = report;

  return (
    <div className="mt-8 space-y-4">

      {/* ── Report header ──────────────────────────────────────── */}
      <div className="bg-[#0c0e16] border border-[#1b2235] rounded-lg p-5">
        <div className="flex items-start justify-between gap-6 flex-wrap">
          <div className="space-y-2">
            <p className="font-mono text-xs text-[#5d6d88] uppercase tracking-widest">
              transaction
            </p>
            
            <a 
              href={`https://etherscan.io/tx/${report.tx_hash}`}
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-sm text-[#38bdf8] hover:text-[#7dd3fc] transition-colors"
            >
              {truncateHash(report.tx_hash)} ↗
            </a>
            <p className="font-mono text-xs text-[#5d6d88]">
              {report.chain} · block {timeline.main_transaction.block_number.toLocaleString()}
            </p>
          </div>

          {attestation && (
            <div className="text-right space-y-1.5">
              {attestation.attested ? (
                <>
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded border border-green-500/30 bg-green-500/10 font-mono text-xs text-green-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-400 shrink-0" />
                    {attestation.already_attested ? "previously attested" : "attested on-chain"}
                  </span>
                  {attestation.attestation_tx_hash && (
                    
                    <a  
                      href={`https://sepolia.etherscan.io/tx/${attestation.attestation_tx_hash}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block font-mono text-xs text-[#38bdf8] hover:text-[#7dd3fc] transition-colors"
                    >
                      {truncateHash(attestation.attestation_tx_hash)} ↗
                    </a>
                  )}
                  {attestation.block_number && (
                    <p className="font-mono text-xs text-[#5d6d88]">
                      block {attestation.block_number.toLocaleString()} · sepolia
                    </p>
                  )}
                </>
              ) : (
                <>
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded border border-red-500/30 bg-red-500/10 font-mono text-xs text-red-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-400 shrink-0" />
                    not attested
                  </span>
                  {attestation.reason && (
                    <p className="font-mono text-xs text-[#5d6d88] max-w-64 text-right leading-relaxed pt-1">
                      {attestation.reason}
                    </p>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Decode summary ─────────────────────────────────────── */}
      <DecodeSummaryStrip summary={timeline.decode_summary} />

      {/* ── Hard block vs normal narrative ─────────────────────── */}
      {narrative_validation_failed || !narrative ? (
        <div className="bg-[#0c0e16] border border-red-500/20 rounded-lg px-5 py-4 flex gap-3 items-start">
          <span className="font-mono text-red-500 shrink-0 mt-px">✗</span>
          <div className="space-y-1">
            <p className="font-mono text-sm text-red-400">narrative validation failed</p>
            <p className="font-mono text-xs text-[#5d6d88] leading-relaxed">
              The generated narrative did not pass validation and cannot be attested.
              This is a correctness failure, not a severity finding.
            </p>
          </div>
        </div>
      ) : (
        <>
          <QualityFlagsPanel
            conflationFlags={protocol_conflation_flags}
            fabricationFlags={fabricated_evidence_flags}
          />

          <div className="bg-[#0c0e16] border border-[#1b2235] rounded-lg p-5 space-y-4">
            <div className="space-y-2">
              <p className="font-mono text-xs text-[#5d6d88] uppercase tracking-widest">summary</p>
              <p className="text-[#c8d0e7] text-sm leading-relaxed">{narrative.summary}</p>
            </div>
            <div className="space-y-2 pt-3 border-t border-[#1b2235]">
              <p className="font-mono text-xs text-[#5d6d88] uppercase tracking-widest">timeline</p>
              <p className="text-[#c8d0e7] text-sm leading-relaxed">{narrative.timeline_narrative}</p>
            </div>
            <div className="space-y-2 pt-3 border-t border-[#1b2235]">
              <p className="font-mono text-xs text-[#5d6d88] uppercase tracking-widest">root cause</p>
              <p className="text-[#c8d0e7] text-sm leading-relaxed">{narrative.root_cause_narrative}</p>
            </div>
            <div className="space-y-2 pt-3 border-t border-[#1b2235]">
              <p className="font-mono text-xs text-[#5d6d88] uppercase tracking-widest">why it matters</p>
              <p className="text-[#c8d0e7] text-sm leading-relaxed">{narrative.why_it_matters}</p>
            </div>
          </div>

          <div className="space-y-2">
            <p className="font-mono text-xs text-[#5d6d88] uppercase tracking-widest px-1 pt-2">
              candidate categories ({narrative.category_assessments.length})
            </p>
            {narrative.category_assessments.map((assessment, i) => (
              <CategoryAssessmentCard
                key={assessment.category}
                assessment={assessment}
                patternScore={pattern_scores[assessment.category]}
                index={i}
              />
            ))}
          </div>

          {narrative.historical_citations_used.length > 0 && (
            <div className="bg-[#0c0e16] border border-[#1b2235] rounded-lg p-5 space-y-2">
              <p className="font-mono text-xs text-[#5d6d88] uppercase tracking-widest">
                historical citations used
              </p>
              <div className="flex flex-wrap gap-2">
                {narrative.historical_citations_used.map((c, i) => (
                  <span
                    key={i}
                    className="px-2.5 py-1 rounded border border-[#1b2235] bg-[#141828] font-mono text-xs text-[#8892a4]"
                  >
                    {c}
                  </span>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}