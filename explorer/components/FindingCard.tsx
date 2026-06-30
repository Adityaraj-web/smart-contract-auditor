"use client";

import { useState } from "react";
import { AuditFinding } from "@/lib/types";

const IMPACT_BORDER: Record<string, string> = {
  High:          "border-l-red-500",
  Critical:      "border-l-red-600",
  Medium:        "border-l-yellow-500",
  Low:           "border-l-green-500",
  Informational: "border-l-blue-500",
  Optimization:  "border-l-purple-500",
};

const IMPACT_BADGE: Record<string, string> = {
  High:          "border-red-500/30 text-red-400 bg-red-500/10",
  Critical:      "border-red-600/30 text-red-300 bg-red-600/10",
  Medium:        "border-yellow-500/30 text-yellow-400 bg-yellow-500/10",
  Low:           "border-green-500/30 text-green-400 bg-green-500/10",
  Informational: "border-blue-500/30 text-blue-400 bg-blue-500/10",
  Optimization:  "border-purple-500/30 text-purple-400 bg-purple-500/10",
};

interface FindingCardProps {
  finding: AuditFinding;
  index: number;
}

export default function FindingCard({ finding, index }: FindingCardProps) {
  const [expanded, setExpanded] = useState(false);

  const borderColor = IMPACT_BORDER[finding.impact] ?? "border-l-[#4a5570]";
  const impactStyle = IMPACT_BADGE[finding.impact] ?? "border-[#1b2235] text-[#c8d0e7] bg-[#0c0e16]";

  return (
    <div className={`border-l-4 ${borderColor} bg-[#0c0e16] border border-[#1b2235] rounded-r-lg overflow-hidden`}>

      {/* ── Header ─────────────────────────────────────────────── */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left px-5 py-3.5 flex items-center gap-4 hover:bg-[#141828] transition-colors duration-150 group"
      >
        {/* Finding ID */}
        <span className="font-mono text-xs text-[#38ef8a] shrink-0 w-12 opacity-70 group-hover:opacity-100 transition-opacity">
          F-{String(index + 1).padStart(3, "0")}
        </span>

        {/* Title + detector */}
        <div className="flex-1 min-w-0 space-y-0.5">
          <p className="text-[#c8d0e7] text-sm font-medium leading-snug truncate">
            {finding.title || finding.detector}
          </p>
          <p className="font-mono text-xs text-[#5d6d88] truncate">
            {finding.detector}
          </p>
        </div>

        {/* Impact badge + chevron — confidence moved to expanded body */}
        <div className="flex items-center gap-2.5 shrink-0">
          <span className={`px-2 py-0.5 rounded border font-mono text-xs font-medium ${impactStyle}`}>
            {finding.impact}
          </span>
          <span className="font-mono text-xs text-[#3d4f6e] group-hover:text-[#5d6d88] transition-colors">
            {expanded ? "▲" : "▼"}
          </span>
        </div>
      </button>

      {/* ── Expanded body ───────────────────────────────────────── */}
      {expanded && (
        <div className="border-t border-[#1b2235] bg-[#09090f] px-5 py-4 space-y-4">

          {/* Confidence — now labelled so it's clear what it means */}
          <div className="flex items-center gap-3 pb-3 border-b border-[#1b2235]">
            <span className="font-mono text-xs text-[#5d6d88] uppercase tracking-widest">
              slither confidence
            </span>
            <span className="font-mono text-xs text-[#c8d0e7]">
              {finding.confidence}
            </span>
            <span className="font-mono text-xs text-[#3d4f6e]">
              — certainty this is a real issue, not a false positive
            </span>
          </div>

          <div className="space-y-1.5">
            <p className="font-mono text-xs text-[#5d6d88] uppercase tracking-widest">
              explanation
            </p>
            <p className="text-[#c8d0e7] text-sm leading-relaxed">
              {finding.explanation}
            </p>
          </div>

          <div className="space-y-1.5 pt-3 border-t border-[#1b2235]">
            <p className="font-mono text-xs text-[#5d6d88] uppercase tracking-widest">
              recommendation
            </p>
            <p className="text-[#c8d0e7] text-sm leading-relaxed">
              {finding.recommendation}
            </p>
          </div>

        </div>
      )}
    </div>
  );
}