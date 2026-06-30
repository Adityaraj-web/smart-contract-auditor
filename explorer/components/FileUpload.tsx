"use client";

import { useRef, useState } from "react";

interface FileUploadProps {
  onAudit: (file: File) => void;
  isLoading: boolean;
}

export default function FileUpload({ onAudit, isLoading }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFile(f: File) {
    if (!f.name.endsWith(".sol")) {
      alert("Please upload a Solidity (.sol) file.");
      return;
    }
    setFile(f);
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }

  function handleDragOver(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave() {
    setIsDragging(false);
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) handleFile(f);
  }

  return (
    <div className="space-y-3">

      {/* ── Drop zone ──────────────────────────────────────────── */}
      <div
        onClick={() => !isLoading && inputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`
          relative overflow-hidden rounded-lg border transition-colors duration-200
          ${isLoading ? "pointer-events-none" : "cursor-pointer"}
          ${isDragging
            ? "border-[#38ef8a] bg-[#38ef8a08]"
            : "border-[#1b2235] bg-[#0c0e16] hover:border-[#2a3450]"
          }
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".sol"
          className="hidden"
          onChange={handleChange}
          disabled={isLoading}
        />

        {/* Scanline — always present, speed tied to state */}
        <span
          aria-hidden="true"
          className={`
            pointer-events-none absolute inset-x-0 h-px
            bg-gradient-to-r from-transparent via-[#38ef8a] to-transparent
            ${isLoading
              ? "[animation:scanline_1.2s_linear_infinite]"
              : "[animation:scanline_4s_linear_infinite]"
            }
          `}
          style={{ opacity: isLoading ? 0.9 : 0.35 }}
        />

        {/* Content */}
        <div className="px-8 py-10 text-center">
          {file ? (
            <div className="space-y-1.5">
              <p className="font-mono text-sm text-[#38ef8a]">{file.name}</p>
              <p className="font-mono text-xs text-[#4a5570]">
                {(file.size / 1024).toFixed(1)} KB
                <span className="mx-2 opacity-40">·</span>
                click to change
              </p>
            </div>
          ) : (
            <div className="space-y-1.5">
              <p className="font-mono text-sm text-[#c8d0e7]">
                drop a <span className="text-[#38ef8a]">.sol</span> file here
              </p>
              <p className="font-mono text-xs text-[#4a5570]">
                or click to browse
              </p>
            </div>
          )}
        </div>
      </div>

      {/* ── Run Audit button ────────────────────────────────────── */}
      <button
        onClick={() => file && onAudit(file)}
        disabled={!file || isLoading}
        className={`
          w-full py-2.5 rounded-lg font-mono text-sm tracking-wide transition-all duration-200
          ${!file || isLoading
            ? "bg-[#0c0e16] text-[#2a3450] border border-[#1b2235] cursor-not-allowed"
            : "bg-[#38ef8a] text-[#07080d] font-semibold hover:bg-[#52f59a] cursor-pointer"
          }
        `}
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="w-3 h-3 border border-[#2a3450] border-t-[#38ef8a] rounded-full animate-spin" />
            scanning…
          </span>
        ) : (
          "run audit →"
        )}
      </button>
    </div>
  );
}