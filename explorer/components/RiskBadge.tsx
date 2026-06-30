const RISK_STYLES: Record<string, { badge: string; dot: string }> = {
  Low:           { badge: "border-green-500/40 text-green-400 bg-green-500/10",    dot: "bg-green-400" },
  Medium:        { badge: "border-yellow-500/40 text-yellow-400 bg-yellow-500/10", dot: "bg-yellow-400" },
  Informational: { badge: "border-blue-500/40 text-blue-400 bg-blue-500/10",       dot: "bg-blue-400" },
  Optimization:  { badge: "border-purple-500/40 text-purple-400 bg-purple-500/10", dot: "bg-purple-400" },
  High:          { badge: "border-red-500/40 text-red-400 bg-red-500/10",          dot: "bg-red-400" },
  Critical:      { badge: "border-red-600/40 text-red-300 bg-red-600/10",          dot: "bg-red-300" },
};

const RISK_DESCRIPTIONS: Record<string, string> = {
  Low:           "Minor issues only.",
  Medium:        "Moderate issues — review before deployment.",
  Informational: "No security impact.",
  Optimization:  "Gas or code quality suggestions only.",
  High:          "High severity issues — do not deploy.",
  Critical:      "Critical vulnerabilities — unsafe to deploy.",
};

interface RiskBadgeProps {
  level: string;
  showDescription?: boolean;
}

export default function RiskBadge({ level, showDescription = false }: RiskBadgeProps) {
  const style = RISK_STYLES[level] ?? RISK_STYLES["Informational"];
  const description = RISK_DESCRIPTIONS[level] ?? "";

  return (
    <div className="flex flex-col gap-1.5">
      <span className={`inline-flex items-center gap-2 px-3 py-1 rounded border font-mono text-sm font-medium w-fit ${style.badge}`}>
        <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${style.dot}`} />
        {level}
      </span>
      {showDescription && (
        <p className="font-mono text-xs text-[#4a5570]">{description}</p>
      )}
    </div>
  );
}