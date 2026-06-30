import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        // font-mono now resolves to JetBrains Mono everywhere
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
        // font-space for headings and display text
        space: ["var(--font-space)", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;