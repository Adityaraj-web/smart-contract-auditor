import { AttestResult, AuditReport, ChatMessage } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function runAttest(file: File): Promise<AttestResult> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_URL}/audit/attest`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    let detail = `Server returned ${res.status}`;
    try {
      const err = await res.json();
      if (err.detail) detail = err.detail;
    } catch {}
    throw new Error(detail);
  }

  return res.json() as Promise<AttestResult>;
}

export async function sendChat(
  report: AuditReport,
  history: ChatMessage[],
  message: string
): Promise<string> {
  const res = await fetch(`${API_URL}/audit/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ report, history, message }),
  });

  if (!res.ok) {
    let detail = `Server returned ${res.status}`;
    try {
      const err = await res.json();
      if (err.detail) detail = err.detail;
    } catch {}
    throw new Error(detail);
  }

  const data = await res.json();
  return data.reply as string;
}