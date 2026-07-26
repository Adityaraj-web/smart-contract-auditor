"use client";

import { useState } from "react";
import { ForensicsCategoryAssessment, ForensicsPatternScore } from "@/lib/types";

function formatCategoryName(category: string): string {
  return category
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

interface CategoryAssessmentCardProps {
  assessment: ForensicsCategoryAssessment;
  patternScore?: ForensicsPatternScore;
  index: number;
}

export default function CategoryAssessmentCard({
  assessment,
  patternScore,
  index,
}: CategoryAssessmentCardProps) {
  const [expanded, setExpanded] = useState(false);
  const retrievalMatches = patternScore?.retrieval_support ?? [];
  const directCount = patternScore?.direct_signals.length ?? 0;

  return (
    <div className="border-l-4 border-l-[#38bdf8] bg-[#0c0e16] border border-[#1b2235] rounded-r-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left px-5 py-3.5 flex items-center gap-4 hover:bg-[#141828] transition-colors duration-150 group"
      >
        <span className="font-mono text-xs text-[#38ef8a] shrink-0 w-12 opacity-70 group-hover:opacity-100 transition-opacity">
          C-{String(index + 1).padStart(3, "0")}
        </span>

        <div className="flex-1 min-w-0 space-y-0.5">
          <p className="text-[#c8d0e7] text-sm font-medium leading-snug truncate">
            {formatCategoryName(assessment.category)}
          </p>
          <p className="font-mono text-xs text-[#5d6d88] truncate">
            {retrievalMatches.length} historical match{retrievalMatches.length !== 1 ? "es" : ""}
            {directCount > 0 ? ` · ${directCount} direct signal${directCount !== 1 ? "s" : ""}` : ""}
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <span className="px-2 py-0.5 rounded border border-[#38bdf8]/30 text-[#38bdf8] bg-[#38bdf8]/10 font-mono text-xs font-medium">
            candidate
          </span>
          <span className="font-mono text-xs text-[#3d4f6e] group-hover:text-[#5d6d88] transition-colors">
            {expanded ? "▲" : "▼"}
          </span>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-[#1b2235] bg-[#09090f] px-5 py-4 space-y-4">
          <div className="space-y-1.5">
            <p className="font-mono text-xs text-[#5d6d88] uppercase tracking-widest">assessment</p>
            <p className="text-[#c8d0e7] text-sm leading-relaxed">{assessment.llm_assessment}</p>
          </div>

          {retrievalMatches.length > 0 && (
            <div className="space-y-1.5 pt-3 border-t border-[#1b2235]">
              <p className="font-mono text-xs text-[#5d6d88] uppercase tracking-widest">
                historical matches
              </p>
              <div className="space-y-2">
                {retrievalMatches.map((r, i) => (
                  <div key={i} className="flex items-center justify-between gap-3">
                    <span className="text-[#c8d0e7] text-sm">
                      {r.protocol} <span className="text-[#5d6d88] text-xs">— {r.section}</span>
                    </span>
                    <span className="font-mono text-xs text-[#3d4f6e] shrink-0">
                      dist {r.distance.toFixed(4)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}