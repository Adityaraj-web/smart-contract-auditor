import { ForensicsConflationFlag, ForensicsFabricationFlag } from "@/lib/types";

interface QualityFlagsPanelProps {
  conflationFlags: ForensicsConflationFlag[];
  fabricationFlags: ForensicsFabricationFlag[];
}

export default function QualityFlagsPanel({
  conflationFlags,
  fabricationFlags,
}: QualityFlagsPanelProps) {
  const total = conflationFlags.length + fabricationFlags.length;
  if (total === 0) return null;

  return (
    <div className="border border-yellow-500/20 bg-yellow-500/5 rounded-lg px-5 py-4 space-y-3">
      <div className="flex gap-3 items-start">
        <span className="font-mono text-yellow-500 shrink-0 mt-px">!</span>
        <div className="space-y-1">
          <p className="font-mono text-sm text-yellow-400">
            {total} quality flag{total !== 1 ? "s" : ""} — attestable with caveats
          </p>
          <p className="font-mono text-xs text-[#5d6d88] leading-relaxed">
            The narrative passed validation, but the checks below flagged heuristic issues.
            These don&apos;t block attestation but are worth reviewing.
          </p>
        </div>
      </div>

      {conflationFlags.length > 0 && (
        <div className="pl-7 space-y-1.5">
          <p className="font-mono text-xs text-yellow-500/70 uppercase tracking-widest">
            protocol conflation ({conflationFlags.length})
          </p>
          {conflationFlags.map((f, i) => (
            <p key={i} className="font-mono text-xs text-[#8892a4] leading-relaxed">
              <span className="text-[#5d6d88]">[{f.field}]</span> bare mention of &lsquo;
              {f.protocol}&rsquo;: &ldquo;{f.snippet}&rdquo;
            </p>
          ))}
        </div>
      )}

      {fabricationFlags.length > 0 && (
        <div className="pl-7 space-y-1.5 pt-2 border-t border-yellow-500/10">
          <p className="font-mono text-xs text-yellow-500/70 uppercase tracking-widest">
            fabricated evidence ({fabricationFlags.length})
          </p>
          {fabricationFlags.map((f, i) => (
            <p key={i} className="font-mono text-xs text-[#8892a4] leading-relaxed">
              <span className="text-[#5d6d88]">[{f.category}]</span> {f.claim}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}