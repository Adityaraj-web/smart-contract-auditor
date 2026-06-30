"use client";

import { useState, useRef, useEffect } from "react";
import { AuditReport, ChatMessage } from "@/lib/types";
import { sendChat } from "@/lib/api";

interface ChatInterfaceProps {
  report: AuditReport;
}

const SUGGESTIONS = [
  "Explain the highest severity finding",
  "What should I fix first?",
  "How does reentrancy work?",
  "Is this contract safe to deploy?",
];

export default function ChatInterface({ report }: ChatInterfaceProps) {
  const [messages, setMessages]   = useState<ChatMessage[]>([]);
  const [input, setInput]         = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError]         = useState<string | null>(null);
  const bottomRef                 = useRef<HTMLDivElement>(null);
  const inputRef                  = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  async function handleSend() {
    const text = input.trim();
    if (!text || isLoading) return;

    const userMessage: ChatMessage = { role: "user", content: text };
    const updatedHistory = [...messages, userMessage];

    setMessages(updatedHistory);
    setInput("");
    setIsLoading(true);
    setError(null);

    try {
      const reply = await sendChat(report, messages, text);
      setMessages([...updatedHistory, { role: "assistant", content: reply }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chat request failed.");
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="mt-4 bg-[#0c0e16] border border-[#1b2235] rounded-lg overflow-hidden">

      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="px-5 py-3 border-b border-[#1b2235] flex items-center gap-2.5">
        <span className="w-1.5 h-1.5 rounded-full bg-[#38ef8a] animate-pulse shrink-0" />
        <p className="font-mono text-xs text-[#c8d0e7] tracking-wide">
          ask about this report
        </p>
      </div>

      {/* ── Message area ───────────────────────────────────────── */}
      <div className="px-5 py-4 min-h-48 max-h-96 overflow-y-auto space-y-3 bg-[#09090f]">

        {/* Empty state — suggestion chips */}
        {messages.length === 0 && !isLoading && (
          <div className="space-y-3 py-2">
            <p className="font-mono text-xs text-[#5d6d88]">try asking:</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => setInput(s)}
                  className="px-3 py-1.5 bg-[#0c0e16] hover:bg-[#141828] border border-[#1b2235] hover:border-[#2a3450] rounded font-mono text-xs text-[#5d6d88] hover:text-[#c8d0e7] transition-all duration-150"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.role === "assistant" && (
              <span className="font-mono text-xs text-[#38ef8a] shrink-0 mt-2.5 select-none leading-none">
                ◈
              </span>
            )}
            <div
              className={`max-w-[82%] px-4 py-2.5 rounded text-sm leading-relaxed whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-[#141828] border border-[#1b2235] text-[#c8d0e7] rounded-tr-none"
                  : "bg-[#0c0e16] border border-[#1b2235] text-[#c8d0e7] rounded-tl-none"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex gap-3 justify-start">
            <span className="font-mono text-xs text-[#38ef8a] shrink-0 mt-2.5 select-none leading-none">
              ◈
            </span>
            <div className="bg-[#0c0e16] border border-[#1b2235] px-4 py-3 rounded rounded-tl-none flex items-center gap-1.5">
              <span className="w-1 h-1 bg-[#38ef8a] rounded-full animate-bounce [animation-delay:0ms] opacity-70" />
              <span className="w-1 h-1 bg-[#38ef8a] rounded-full animate-bounce [animation-delay:150ms] opacity-70" />
              <span className="w-1 h-1 bg-[#38ef8a] rounded-full animate-bounce [animation-delay:300ms] opacity-70" />
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <p className="font-mono text-xs text-red-400 text-center py-2">{error}</p>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Input row ──────────────────────────────────────────── */}
      <div className="border-t border-[#1b2235] px-4 py-3 flex gap-3 items-end bg-[#0c0e16]">
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="ask about a finding or vulnerability…"
          disabled={isLoading}
          rows={1}
          className="flex-1 bg-[#09090f] border border-[#1b2235] rounded px-4 py-2.5 font-mono text-sm text-[#c8d0e7] placeholder-[#3d4f6e] resize-none focus:outline-none focus:border-[#38ef8a]/40 disabled:opacity-40 transition-colors duration-150"
          style={{ minHeight: "42px", maxHeight: "120px" }}
          onInput={(e) => {
            const el = e.currentTarget;
            el.style.height = "auto";
            el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
          }}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
          className={`px-4 py-2.5 rounded font-mono text-sm transition-all duration-150 shrink-0 ${
            !input.trim() || isLoading
              ? "bg-[#09090f] text-[#3d4f6e] border border-[#1b2235] cursor-not-allowed"
              : "bg-[#38ef8a] text-[#07080d] font-semibold hover:bg-[#52f59a] cursor-pointer"
          }`}
        >
          send
        </button>
      </div>

    </div>
  );
}