"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function ForensicsLandingPage() {
  const router = useRouter();
  const [txHash, setTxHash] = useState("");
  const [chain, setChain] = useState("mainnet");
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = txHash.trim();
    if (!/^0x[a-fA-F0-9]{64}$/.test(trimmed)) {
      setError("Enter a valid transaction hash (0x + 64 hex characters).");
      return;
    }
    setError(null);
    router.push(`/forensics/${trimmed}?chain=${encodeURIComponent(chain.trim())}`);
  }

  return (
    <main className="min-h-screen bg-[#07080d] px-6 py-14">
      <div className="max-w-3xl mx-auto">
        <div className="mb-10">
          <p className="font-mono text-xs text-[#38ef8a] tracking-widest uppercase mb-3">
            post-incident analysis
          </p>
          <h1
            className="text-4xl font-bold text-white tracking-tight leading-none mb-4"
            style={{ fontFamily: "var(--font-syne)" }}
          >
            Forensics Explorer
          </h1>
          <p className="font-mono text-sm text-[#5d6d88] leading-relaxed max-w-xl">
            Paste a transaction hash to generate a post-mortem report — historical
            pattern matching, decoded event timeline, and gated on-chain attestation.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-[#0c0e16] border border-[#1b2235] rounded-lg p-5 space-y-4"
        >
          <div className="space-y-1.5">
            <label className="font-mono text-xs text-[#5d6d88] uppercase tracking-widest">
              transaction hash
            </label>
            <input
              type="text"
              value={txHash}
              onChange={(e) => setTxHash(e.target.value)}
              placeholder="0x..."
              className="w-full bg-[#09090f] border border-[#1b2235] rounded px-3 py-2 font-mono text-sm text-[#c8d0e7] placeholder:text-[#3d4f6e] focus:outline-none focus:border-[#38bdf8]/50"
            />
          </div>

          <div className="space-y-1.5">
            <label className="font-mono text-xs text-[#5d6d88] uppercase tracking-widest">
              chain
            </label>
            <input
              type="text"
              value={chain}
              onChange={(e) => setChain(e.target.value)}
              className="w-full bg-[#09090f] border border-[#1b2235] rounded px-3 py-2 font-mono text-sm text-[#c8d0e7] focus:outline-none focus:border-[#38bdf8]/50"
            />
          </div>

          {error && <p className="font-mono text-xs text-red-400">{error}</p>}

          <button
            type="submit"
            className="w-full bg-[#38ef8a]/10 border border-[#38ef8a]/30 text-[#38ef8a] font-mono text-sm py-2.5 rounded hover:bg-[#38ef8a]/20 transition-colors"
          >
            generate report →
          </button>
        </form>
      </div>
    </main>
  );
}