import { supabase } from "@/lib/supabase";
import { Attestation } from "@/lib/types";

const RISK_BADGE: Record<string, string> = {
  Low:           "border-green-500/30 text-green-400 bg-green-500/10",
  Medium:        "border-yellow-500/30 text-yellow-400 bg-yellow-500/10",
  Informational: "border-blue-500/30 text-blue-400 bg-blue-500/10",
  Optimization:  "border-purple-500/30 text-purple-400 bg-purple-500/10",
  High:          "border-red-500/30 text-red-400 bg-red-500/10",
  Critical:      "border-red-600/30 text-red-300 bg-red-600/10",
};

function truncate(str: string, start = 6, end = 4): string {
  return `${str.slice(0, start)}…${str.slice(-end)}`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

async function getAttestations(): Promise<Attestation[]> {
  const { data, error } = await supabase
    .from("attestations")
    .select("*")
    .order("attested_at", { ascending: false });

  if (error) {
    console.error("Supabase fetch error:", error);
    return [];
  }
  return data ?? [];
}

export default async function AttestationsPage() {
  const attestations = await getAttestations();

  return (
    <main className="min-h-screen bg-[#07080d] px-6 py-14">
      <div className="max-w-7xl mx-auto">

        {/* ── Page header ──────────────────────────────────────── */}
        <div className="mb-10">
          <p className="font-mono text-xs text-[#38ef8a] tracking-widest uppercase mb-3">
            on-chain records
          </p>
          <h1 className="text-4xl font-bold text-white tracking-tight leading-none mb-4"
          style={{ fontFamily: "var(--font-syne)" }}>
            Attestation Explorer
          </h1>
          <p className="font-mono text-sm text-[#5d6d88] leading-relaxed max-w-xl">
            Contracts that passed the audit risk threshold, attested on the
            Sepolia testnet via{" "}
            <code className="text-[#38bdf8] text-xs">AttestationRegistry.sol</code>
          </p>
        </div>

        {/* ── Stats bar ────────────────────────────────────────── */}
        <div className="flex gap-4 mb-8">
          <div className="bg-[#0c0e16] border border-[#1b2235] rounded-lg px-5 py-3 flex flex-col gap-1">
            <p className="font-mono text-xs text-[#5d6d88] uppercase tracking-widest">
              total attestations
            </p>
            <p className="font-mono text-2xl font-semibold text-white leading-none">
              {attestations.length}
            </p>
          </div>
          <div className="bg-[#0c0e16] border border-[#1b2235] rounded-lg px-5 py-3 flex flex-col gap-1">
            <p className="font-mono text-xs text-[#5d6d88] uppercase tracking-widest">
              network
            </p>
            <p className="font-mono text-2xl font-semibold text-[#38bdf8] leading-none">
              sepolia
            </p>
          </div>
          <div className="bg-[#0c0e16] border border-[#1b2235] rounded-lg px-5 py-3 flex flex-col gap-1">
            <p className="font-mono text-xs text-[#5d6d88] uppercase tracking-widest">
              contract
            </p>
            
            <a
              href={`https://sepolia.etherscan.io/address/${process.env.NEXT_PUBLIC_REGISTRY_ADDRESS}`}
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-sm text-[#38bdf8] hover:text-[#7dd3fc] transition-colors leading-none pt-1"
            >
              AttestationRegistry ↗
            </a>
          </div>
        </div>

        {/* ── Table ────────────────────────────────────────────── */}
        {attestations.length === 0 ? (
          <div className="bg-[#0c0e16] border border-[#1b2235] rounded-lg p-16 text-center">
            <p className="font-mono text-sm text-[#5d6d88]">
              no attestations yet
            </p>
          </div>
        ) : (
          <div className="bg-[#0c0e16] border border-[#1b2235] rounded-lg overflow-hidden">
            <table className="w-full">

              {/* Header */}
              <thead>
                <tr className="border-b border-[#1b2235]">
                  {["contract hash", "risk", "auditor", "block", "attested at", "transaction"].map((col) => (
                    <th
                      key={col}
                      className="px-5 py-3 text-left font-mono text-xs text-[#8892a4] uppercase tracking-widest font-normal"
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>

              {/* Rows */}
              <tbody className="divide-y divide-[#1b2235]">
                {attestations.map((a) => (
                  <tr
                    key={a.id}
                    className="hover:bg-[#141828] transition-colors duration-150 group"
                  >
                    {/* Contract hash */}
                    <td className="px-5 py-3.5">
                      <span className="font-mono text-xs text-[#c8d0e7]">
                        {truncate(a.contract_hash, 10, 8)}
                      </span>
                    </td>

                    {/* Risk level */}
                    <td className="px-5 py-3.5">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded border font-mono text-xs font-medium ${
                          RISK_BADGE[a.risk_level] ?? RISK_BADGE["Informational"]
                        }`}
                      >
                        <span className="w-1 h-1 rounded-full bg-current shrink-0" />
                        {a.risk_level}
                      </span>
                    </td>

                    {/* Auditor */}
                    <td className="px-5 py-3.5">
                      <span className="font-mono text-xs text-[#5d6d88]">
                        {truncate(a.auditor_address, 6, 4)}
                      </span>
                    </td>

                    {/* Block */}
                    <td className="px-5 py-3.5">
                      <span className="font-mono text-xs text-[#5d6d88]">
                        {a.block_number.toLocaleString()}
                      </span>
                    </td>

                    {/* Attested at */}
                    <td className="px-5 py-3.5">
                      <span className="font-mono text-xs text-[#5d6d88]">
                        {formatDate(a.attested_at)}
                      </span>
                    </td>

                    {/* Transaction link */}
                    <td className="px-5 py-3.5">
                      {a.tx_hash ? (
                        <a
                          href={`https://sepolia.etherscan.io/tx/0x${a.tx_hash}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-mono text-xs text-[#38bdf8] hover:text-[#7dd3fc] transition-colors group-hover:underline underline-offset-2"
                        >
                          {truncate(a.tx_hash, 8, 6)} ↗
                        </a>
                      ) : (
                        <span className="font-mono text-xs text-[#3d4f6e]">
                          —
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}