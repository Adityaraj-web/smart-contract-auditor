"use client";

import { useState, useEffect, useRef } from "react";
import FileUpload from "@/components/FileUpload";
import AuditReport from "@/components/AuditReport";
import ChatInterface from "@/components/ChatInterface";
import { runAttest } from "@/lib/api";
import { AttestResult } from "@/lib/types";

const LOADING_STAGES = [
  "running slither static analysis",
  "retrieving vulnerability context via rag",
  "generating audit report with local llm",
  "finalising results",
];

// Approximate time each stage takes before advancing the UI label.
// Last stage has no timer — it stays until the response arrives.
const STAGE_DURATIONS_MS = [15_000, 10_000, 50_000];

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export default function AuditPage() {
  const [isLoading, setIsLoading]   = useState(false);
  const [stageIndex, setStageIndex] = useState(0);
  const [result, setResult]         = useState<AttestResult | null>(null);
  const [error, setError]           = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  function scheduleNextStage(index: number) {
    const ms = STAGE_DURATIONS_MS[index];
    if (ms === undefined) return;
    timerRef.current = setTimeout(() => {
      setStageIndex(index + 1);
      scheduleNextStage(index + 1);
    }, ms);
  }

  function clearTimer() {
    if (timerRef.current) clearTimeout(timerRef.current);
  }

  async function handleAudit(file: File) {
    if (!API_URL) return;
    setIsLoading(true);
    setResult(null);
    setError(null);
    setStageIndex(0);
    scheduleNextStage(0);

    try {
      const data = await runAttest(file);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Audit failed.");
    } finally {
      clearTimer();
      setIsLoading(false);
    }
  }

  useEffect(() => () => clearTimer(), []);

  return (
    <main className="min-h-screen bg-[#07080d] px-6 py-14">
      <div className="max-w-5xl mx-auto">

        {/* ── No-backend banner (Vercel deployment) ────────────── */}
        {!API_URL && (
          <div className="mb-10 border border-yellow-500/20 bg-yellow-500/5 rounded-lg px-5 py-4 flex gap-3 items-start">
            <span className="font-mono text-yellow-500 shrink-0 mt-px">!</span>
            <div className="space-y-1">
              <p className="font-mono text-sm text-yellow-400">
                audit unavailable in this environment
              </p>
              <p className="font-mono text-xs text-[#5d6d88] leading-relaxed">
                The audit pipeline requires a local backend (FastAPI + Ollama).{" "}
                
                <a
                  href="https://github.com/Adityaraj-web/smart-contract-auditor"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[#38bdf8] hover:text-[#7dd3fc] transition-colors"
                >
                  see the readme for local setup →
                </a>{" "}
                The{" "}
                <a href="/attestations" className="text-[#38bdf8] hover:text-[#7dd3fc] transition-colors">
                  attestation explorer
                </a>{" "}
                is fully available.
              </p>
            </div>
          </div>
        )}

        {/* ── Page header ──────────────────────────────────────── */}
        <div className="mb-10">
          <p className="font-mono text-xs text-[#38ef8a] tracking-widest uppercase mb-3">
            smart contract security
          </p>
          <h1 className="text-4xl font-bold text-white tracking-tight leading-none mb-4"
          style={{ fontFamily: "var(--font-syne)" }}>
            Solidity Auditor
          </h1>
          <p className="font-mono text-sm text-[#5d6d88] leading-relaxed max-w-xl">
            Slither static analysis · on-chain attestation
          </p>
        </div>

        {/* ── Upload zone ──────────────────────────────────────── */}
        <FileUpload onAudit={handleAudit} isLoading={isLoading} />

        {/* ── Loading — terminal log ────────────────────────────── */}
        {isLoading && (
          <div className="mt-6 bg-[#0c0e16] border border-[#1b2235] rounded-lg p-5 space-y-2.5">
            {LOADING_STAGES.map((label, i) => {
              const done    = i < stageIndex;
              const current = i === stageIndex;

              return (
                <div key={i} className="flex items-center gap-3">
                  {/* Status glyph */}
                  {done && (
                    <span className="font-mono text-xs text-[#38ef8a] w-3 shrink-0">✓</span>
                  )}
                  {current && (
                    <span className="w-3 h-3 border border-[#38ef8a] border-t-transparent rounded-full animate-spin shrink-0" />
                  )}
                  {!done && !current && (
                    <span className="font-mono text-xs text-[#2a3450] w-3 shrink-0">·</span>
                  )}

                  {/* Stage label */}
                  <span
                    className={`font-mono text-sm ${
                      done    ? "text-[#3d4f6e] line-through decoration-[#2a3450]" :
                      current ? "text-[#c8d0e7]" :
                                "text-[#2a3450]"
                    }`}
                  >
                    {label}
                  </span>
                </div>
              );
            })}

            <p className="font-mono text-xs text-[#2a3450] pt-3 mt-1 border-t border-[#1b2235]">
              full pipeline on cpu · typically 60–120s
            </p>
          </div>
        )}

        {/* ── Error ────────────────────────────────────────────── */}
        {error && (
          <div className="mt-6 bg-[#0c0e16] border border-red-500/20 rounded-lg px-5 py-4 flex gap-3 items-start">
            <span className="font-mono text-red-500 shrink-0 mt-px">✗</span>
            <div className="space-y-1">
              <p className="font-mono text-sm text-red-400">audit failed</p>
              <p className="font-mono text-xs text-[#5d6d88]">{error}</p>
            </div>
          </div>
        )}

        {/* ── Report + chat ─────────────────────────────────────── */}
        {result && !isLoading && (
          <>
            <AuditReport result={result} />
            <ChatInterface report={result.report} />
          </>
        )}

      </div>
    </main>
  );
}