import { ForensicsDecodeSummary } from "@/lib/types";

interface DecodeSummaryStripProps {
  summary: ForensicsDecodeSummary;
}

export default function DecodeSummaryStrip({ summary }: DecodeSummaryStripProps) {
  const items = [
    { label: "total logs", value: summary.total_logs, color: "text-white" },
    { label: "verified abi", value: summary.verified_abi_decoded, color: "text-[#38ef8a]" },
    { label: "known signature", value: summary.known_signature_decoded, color: "text-[#38bdf8]" },
    {
      label: "undecoded",
      value: summary.undecoded,
      color: summary.undecoded > 0 ? "text-yellow-400" : "text-[#5d6d88]",
    },
  ];

  return (
    <div className="flex gap-4 flex-wrap">
      {items.map((item) => (
        <div
          key={item.label}
          className="bg-[#0c0e16] border border-[#1b2235] rounded-lg px-5 py-3 flex flex-col gap-1"
        >
          <p className="font-mono text-xs text-[#5d6d88] uppercase tracking-widest">
            {item.label}
          </p>
          <p className={`font-mono text-2xl font-semibold leading-none ${item.color}`}>
            {item.value}
          </p>
        </div>
      ))}
    </div>
  );
}