import re
import json
import httpx
from backend.retrieval import retrieve_context

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2:3b"
MAX_TOOL_ROUNDS = 5  # prevent infinite loops

# ── Tool definitions (Ollama tool-call schema) ─────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_finding_details",
            "description": (
                "Returns the full details of a specific audit finding by its "
                "number. Use this when the user asks about a specific finding, "
                "e.g. 'explain finding 2' or 'what is F-003'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "finding_id": {
                        "type": "integer",
                        "description": "The finding number (1-based index)",
                    }
                },
                "required": ["finding_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Searches the vulnerability knowledge base for background "
                "information on a topic. Use this when the user asks for more "
                "context on a vulnerability type, exploit pattern, or fix "
                "strategy that goes beyond what the audit report contains."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query, e.g. 'reentrancy attack pattern'",
                    }
                },
                "required": ["query"],
            },
        },
    },
]


# ── Tool execution ─────────────────────────────────────────────────────────────

def _execute_tool(name: str, arguments: dict, findings: list[dict]) -> str:
    """
    Run the requested tool and return its result as a plain string.
    Ollama expects tool results as strings in the message content.
    """
    if name == "get_finding_details":
        raw_id = str(arguments.get("finding_id", "1"))
        digits = re.search(r"\d+", raw_id)
        finding_id = int(digits.group()) if digits else 1
        idx = finding_id - 1
        if idx < 0 or idx >= len(findings):
            return f"Finding {finding_id} does not exist. There are {len(findings)} findings."
        f = findings[idx]
        return json.dumps(f, indent=2)

    if name == "search_knowledge_base":
        query = str(arguments.get("query", ""))
        if not query:
            return "No query provided."
        chunks = retrieve_context([query], top_k=2)
        if not chunks:
            return "No relevant results found in the knowledge base."
        result = ""
        for chunk in chunks:
            swc = f"SWC-{chunk['swc_id']}" if chunk.get("swc_id") else "N/A"
            result += f"\n=== {chunk['title']} ({swc}) ===\n{chunk['text']}\n"
        return result.strip()

    return f"Unknown tool: {name}"


# ── System prompt builder ──────────────────────────────────────────────────────

def _build_system_prompt(report: dict) -> str:
    """
    Build the system prompt with the audit report baked in as context.
    The model uses this as its base knowledge for the conversation.
    """
    findings_summary = ""
    for i, f in enumerate(report.get("findings", []), 1):
        findings_summary += (
            f"  F-{i:03d}: {f.get('title', f.get('detector', 'Unknown'))} "
            f"[Impact: {f.get('impact')}, Confidence: {f.get('confidence')}]\n"
        )

    return f"""You are a smart contract security expert reviewing an audit report with a developer.

AUDIT REPORT SUMMARY:
- Overall Risk: {report.get('overall_risk', 'Unknown')}
- Total Findings: {len(report.get('findings', []))}
- Summary: {report.get('summary', '')}

FINDINGS LIST:
{findings_summary}

You have access to two tools:
1. get_finding_details(finding_id) — retrieve full details of a specific finding by number
2. search_knowledge_base(query) — search for background context on vulnerability types

MANDATORY TOOL USE RULES — you MUST follow these without exception:
- If the user asks about ANY specific finding (e.g. "explain finding 1", "what is F-003", "the highest severity finding", "the reentrancy issue") → you MUST call get_finding_details BEFORE answering. Do not answer from memory.
- If the user asks for deeper context on a vulnerability type, attack pattern, or fix strategy → call search_knowledge_base first.
- Never describe a finding's details without first calling get_finding_details to retrieve the actual data.
- Base every answer on tool results — do not rely on general knowledge about what a finding might contain.
- Be concise and practical. The developer wants actionable information.
- If the user asks something unrelated to this audit report, smart contract security, or blockchain development, do not answer the off-topic question. Instead, politely redirect them — for example: "I'm focused on this audit report. Try asking about a specific finding, a vulnerability type, or how to fix an issue."

EXAMPLE: User asks "explain the highest severity finding"
→ CORRECT: call get_finding_details(1), then explain based on the returned data
→ WRONG: explain reentrancy from general knowledge without calling the tool"""

# ── Main chat function ─────────────────────────────────────────────────────────

def run_chat_turn(
    report: dict,
    history: list[dict],
    user_message: str,
) -> str:
    """
    Run one turn of the agentic chat loop.

    report:       the full AuditReport dict from the audit pipeline
    history:      list of prior {"role": ..., "content": ...} message dicts
    user_message: the user's latest message

    Returns the assistant's final plain-text response.
    """
    findings = report.get("findings", [])

    # Build the full message list for this turn
    messages = [
        {"role": "system", "content": _build_system_prompt(report)},
        *history,
        {"role": "user", "content": user_message},
    ]

    # Agentic loop — keeps going while model requests tool calls
    for round_num in range(MAX_TOOL_ROUNDS):
        response = httpx.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "tools": TOOLS,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_ctx": 8192,
                },
            },
            timeout=120.0,
        )
        response.raise_for_status()

        data = response.json()
        message = data.get("message", {})
        tool_calls = message.get("tool_calls")

        # No tool calls — model produced a final text response
        if not tool_calls:
            return message.get("content", "").strip()

        # Append the assistant's tool-call message to the conversation
        messages.append({"role": "assistant", "content": None, "tool_calls": tool_calls})

        # Execute each tool and append results
        for call in tool_calls:
            fn = call.get("function", {})
            tool_name = fn.get("name", "")
            # Ollama returns arguments as a dict directly (already parsed)
            arguments = fn.get("arguments", {})
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}

            result = _execute_tool(tool_name, arguments, findings)

            messages.append({
                "role": "tool",
                "content": result,
            })

    # Fallback if we somehow exhaust tool rounds
    return "I was unable to complete the reasoning chain. Please try rephrasing your question."