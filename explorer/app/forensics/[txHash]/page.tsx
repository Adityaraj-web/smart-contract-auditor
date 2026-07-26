"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { runForensicsGenerate, runForensicsAttest } from "@/lib/api";
import { ForensicsReport, ForensicsAttestResult } from "@/lib/types";
import ForensicsReportView from "@/components/ForensicsReportView";

const LOADING_STAGES = [
  "fetching transaction from etherscan",
  "decoding event logs",
  "retrieving similar historical incidents",
  "generating forensic narrative with local llm",
];
const STAGE_DURATIONS_MS = [8_000, 8_000, 15_000];

export default function ForensicsReportPage() {
  const params = useParams<{ txHash: string }>();
  const searchParams = useSearchParams();
  const chain = searchParams.get("chain") ?? "mainnet";
  const txHash = params.txHash;

  const [isLoading, setIsLoading] = useState(true);
  const [stageIndex, setStageIndex] = useState(0);
  const [report, setReport] = useState<ForensicsReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [isAttesting, setIsAttesting] = useState(false);
  const [attestation, setAttestation] = useState<Omit<ForensicsAttestResult, "report"> | null>(null);
  const [attestError, setAttestError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;

    function scheduleNextStage(index: number) {
      const ms = STAGE_DURATIONS_MS[index];
      if (ms === undefined) return;
      timer = setTimeout(() => {
        if (!cancelled) {
          setStageIndex(index + 1);
          scheduleNextStage(index + 1);
        }
      }, ms);
    }

    async function load() {
      setIsLoading(true);
      setError(null);
      setStageIndex(0);
      scheduleNextStage(0);
      try {
        const data = await runForensicsGenerate({ tx_hash: txHash, chain });
        if (!cancelled) setReport(data);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Report generation failed.");
      } finally {
        if (timer) clearTimeout(timer);
        if (!cancelled) setIsLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [txHash, chain]);

  async function handleAttest() {
    if (!report) return;
    setIsAttesting(true);
    setAttestError(null);
    try {
      const result = await runForensicsAttest({ tx_hash: txHash, chain, report });
      const { report: _omit, ...rest } = result;
      setAttestation(rest);
    } catch (err) {
      setAttestError(err instanceof Error ? err.message : "Attestation failed.");
    } finally {
      setIsAttesting(false);
    }
  }

  // Only hides the button once attestation actually succeeds — a failed
  // attempt (attestation.attested === false, e.g. a transient chain error)
  // leaves the button available for retry rather than locking the page.
  const canAttest =
    !!report &&
    !report.narrative_validation_failed &&
    !!report.narrative &&
    attestation?.attested !== true;

  return (
    <main className="min-h-screen bg-[#07080d] px-6 py-14">
      <div className="max-w-5xl mx-auto">
        <div className="mb-10">
          <p className="font-mono text-xs text-[#38ef8a] tracking-widest uppercase mb-3">
            post-incident analysis
          </p>
          <h1
            className="text-4xl font-bold text-white tracking-tight leading-none mb-4"
            style={{ fontFamily: "var(--font-syne)" }}
          >
            Forensics Report
          </h1>
          <p className="font-mono text-sm text-[#5d6d88] break-all">
            {txHash} · {chain}
          </p>
        </div>

        {isLoading && (
          <div className="bg-[#0c0e16] border border-[#1b2235] rounded-lg p-5 space-y-2.5">
            {LOADING_STAGES.map((label, i) => {
              const done = i < stageIndex;
              const current = i === stageIndex;
              return (
                <div key={i} className="flex items-center gap-3">
                  {done && <span className="font-mono text-xs text-[#38ef8a] w-3 shrink-0">✓</span>}
                  {current && (
                    <span className="w-3 h-3 border border-[#38ef8a] border-t-transparent rounded-full animate-spin shrink-0" />
                  )}
                  {!done && !current && <span className="font-mono text-xs text-[#2a3450] w-3 shrink-0">·</span>}
                  <span
                    className={`font-mono text-sm ${
                      done ? "text-[#3d4f6e] line-through" : current ? "text-[#c8d0e7]" : "text-[#2a3450]"
                    }`}
                  >
                    {label}
                  </span>
                </div>
              );
            })}
            <p className="font-mono text-xs text-[#2a3450] pt-3 mt-1 border-t border-[#1b2235]">
              full pipeline on cpu · can take a couple minutes
            </p>
          </div>
        )}

        {error && (
          <div className="bg-[#0c0e16] border border-red-500/20 rounded-lg px-5 py-4 flex gap-3 items-start">
            <span className="font-mono text-red-500 shrink-0 mt-px">✗</span>
            <div className="space-y-1">
              <p className="font-mono text-sm text-red-400">report generation failed</p>
              <p className="font-mono text-xs text-[#5d6d88]">{error}</p>
            </div>
          </div>
        )}

        {report && !isLoading && (
          <>
            <ForensicsReportView report={report} attestation={attestation ?? undefined} />

            {canAttest && (
              <div className="mt-6 flex items-center gap-4">
                <button
                  onClick={handleAttest}
                  disabled={isAttesting}
                  className="bg-[#38ef8a]/10 border border-[#38ef8a]/30 text-[#38ef8a] font-mono text-sm px-5 py-2.5 rounded hover:bg-[#38ef8a]/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isAttesting ? "attesting on-chain…" : "attest on-chain →"}
                </button>
                {attestError && <p className="font-mono text-xs text-red-400">{attestError}</p>}
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
}