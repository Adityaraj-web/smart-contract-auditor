import { supabase } from "@/lib/supabase";
import { Attestation } from "@/lib/types";

const RISK_COLORS: Record<string, string> = {
  Low: "bg-green-500/20 text-green-400 border border-green-500/30",
  Medium: "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30",
  Informational: "bg-blue-500/20 text-blue-400 border border-blue-500/30",
  Optimization: "bg-purple-500/20 text-purple-400 border border-purple-500/30",
  High: "bg-red-500/20 text-red-400 border border-red-500/30",
  Critical: "bg-red-700/20 text-red-300 border border-red-700/30",
};

function truncate(str: string, start = 6, end = 4): string {
  return `${str.slice(0, start)}...${str.slice(-end)}`;
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

export default async function Home() {
  const attestations = await getAttestations();

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100 px-6 py-12">
      <div className="max-w-6xl mx-auto">

        <div className="mb-10">
          <h1 className="text-3xl font-bold text-white mb-2">
            Smart Contract Attestation Explorer
          </h1>
          <p className="text-gray-400 text-sm">
            On-chain audit attestations issued on the Sepolia testnet.
            Each record represents a contract that passed the AI-powered
            security audit threshold.
          </p>
        </div>

        <div className="mb-8 flex gap-6">
          <div className="bg-gray-900 rounded-lg px-5 py-3 border border-gray-800">
            <p className="text-xs text-gray-500 mb-1">Total Attestations</p>
            <p className="text-2xl font-bold text-white">{attestations.length}</p>
          </div>
          <div className="bg-gray-900 rounded-lg px-5 py-3 border border-gray-800">
            <p className="text-xs text-gray-500 mb-1">Network</p>
            <p className="text-2xl font-bold text-blue-400">Sepolia</p>
          </div>
        </div>

        {attestations.length === 0 ? (
          <div className="text-center py-20 text-gray-600">
            No attestations yet.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-gray-800">
            <table className="w-full text-sm">
              <thead className="bg-gray-900 text-gray-400 text-xs uppercase tracking-wider">
                <tr>
                  <th className="px-5 py-4 text-left">Contract Hash</th>
                  <th className="px-5 py-4 text-left">Risk Level</th>
                  <th className="px-5 py-4 text-left">Auditor</th>
                  <th className="px-5 py-4 text-left">Block</th>
                  <th className="px-5 py-4 text-left">Attested At</th>
                  <th className="px-5 py-4 text-left">Transaction</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {attestations.map((a) => (
                  <tr
                    key={a.id}
                    className="bg-gray-950 hover:bg-gray-900 transition-colors"
                  >
                    <td className="px-5 py-4 font-mono text-gray-300">
                      {truncate(a.contract_hash, 8, 6)}
                    </td>
                    <td className="px-5 py-4">
                      <span
                        className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                          RISK_COLORS[a.risk_level] ?? RISK_COLORS["Informational"]
                        }`}
                      >
                        {a.risk_level}
                      </span>
                    </td>
                    <td className="px-5 py-4 font-mono text-gray-400">
                      {truncate(a.auditor_address, 6, 4)}
                    </td>
                    <td className="px-5 py-4 text-gray-400">
                      {a.block_number.toLocaleString()}
                    </td>
                    <td className="px-5 py-4 text-gray-400">
                      {formatDate(a.attested_at)}
                    </td>
                    <td className="px-5 py-4">
                      
                     <a href={`https://sepolia.etherscan.io/tx/0x${a.tx_hash}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 font-mono underline underline-offset-2"
                     >
                        {truncate(a.tx_hash, 6, 4)}
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <p className="mt-8 text-center text-xs text-gray-700">
          Attestations are issued by an AI-powered smart contract auditing
          pipeline running Slither + RAG + Ollama locally.
        </p>

      </div>
    </main>
  );
}