import type { Metadata } from "next";
import { Space_Grotesk, JetBrains_Mono, Syne } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
});

const syne = Syne({
  variable: "--font-syne",
  subsets: ["latin"],
  weight: ["700", "800"],
});

export const metadata: Metadata = {
  title: "Solidity Auditor",
  description:
    "AI-powered smart contract security analysis with on-chain attestation on Sepolia.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${spaceGrotesk.variable} ${jetbrainsMono.variable} ${syne.variable} h-full`}
    >
      <body className="min-h-full flex flex-col bg-[#07080d] text-[#c8d0e7] antialiased font-space">

        {/* ── Top nav ──────────────────────────────────────────── */}
        <header className="shrink-0 border-b border-[#1b2235] h-11 px-6 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 group">
            <span className="text-[#38ef8a] font-mono text-sm select-none">◈</span>
            <span className="font-mono text-sm text-[#c8d0e7] tracking-tight">
              solidity-auditor
            </span>
          </Link>

          <nav className="flex items-center gap-6">
            <Link
              href="/"
              className="font-mono text-xs text-[#8892a4] hover:text-[#c8d0e7] transition-colors duration-150"
            >
              audit
            </Link>
            <Link
              href="/attestations"
              className="font-mono text-xs text-[#8892a4] hover:text-[#c8d0e7] transition-colors duration-150"
            >
              attestations
            </Link>
            
            <a href="https://github.com/Adityaraj-web/smart-contract-auditor"
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-xs text-[#8892a4] hover:text-[#38bdf8] transition-colors duration-150"
            >
              github ↗
            </a>
          </nav>
        </header>

        <div className="flex-1 flex flex-col">{children}</div>
      </body>
    </html>
  );
}