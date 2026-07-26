"""
Reads raw forensics incident markdown files (frontmatter + four-section
body), splits each into one chunk per section, and writes a single
structured JSON file of chunks ready for embedding.

Deviates from the vulnerability-corpus chunker in one deliberate way:
chunks are split along the incident's own "## Section" headers (Summary,
What Happened, Root Cause, Why It Matters) rather than by a token budget
alone. Each incident file is short enough that a token-budget-only split
would often collapse multiple sections into a single chunk, blending a
root cause with an unrelated "why it matters" note. Section-aware
chunking keeps each chunk semantically single-purpose, which matters
for forensics retrieval specifically (e.g. "similar root cause" queries
should retrieve Root Cause sections, not a mixed blob).
"""

import re
import json
import uuid
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "forensics" / "raw"
OUTPUT_FILE = Path(__file__).parent.parent / "forensics" / "processed" / "chunks.json"

CHARS_PER_TOKEN = 4          # rough estimate for English prose
MAX_CHUNK_TOKENS = 400


def parse_frontmatter(raw_text: str) -> tuple[dict, str]:
    """Split a markdown file into its frontmatter dict and body text."""
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", raw_text, re.DOTALL)
    if not match:
        raise ValueError("File missing frontmatter block")
    frontmatter_block, body = match.groups()

    metadata = {}
    for line in frontmatter_block.strip().split("\n"):
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()

    return metadata, body.strip()


def split_into_sections(body: str) -> list[tuple[str, str]]:
    """
    Split the body on '## Section Name' headers.
    Returns a list of (section_name, section_text) tuples, in order.
    """
    parts = re.split(r"^## (.+)$", body, flags=re.MULTILINE)

    # parts[0] is anything before the first header (empty/whitespace for
    # our files, since every incident file starts with "## Summary").
    sections = []
    for i in range(1, len(parts), 2):
        section_name = parts[i].strip()
        section_text = parts[i + 1].strip()
        sections.append((section_name, section_text))
    return sections


def group_paragraphs(text: str) -> list[str]:
    """
    Group consecutive paragraphs together until adding the next one
    would exceed MAX_CHUNK_TOKENS. Never splits mid-paragraph.
    Same logic as the vulnerability-corpus chunker, scoped to one section
    (in practice each section is short enough that this rarely splits
    further and just returns the section as a single chunk).
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    current = []
    current_len = 0

    for para in paragraphs:
        para_tokens = len(para) // CHARS_PER_TOKEN
        if current and current_len + para_tokens > MAX_CHUNK_TOKENS:
            chunks.append("\n\n".join(current))
            current = []
            current_len = 0
        current.append(para)
        current_len += para_tokens

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def process_file(filepath: Path) -> list[dict]:
    raw_text = filepath.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(raw_text)
    sections = split_into_sections(body)

    funds_lost_raw = metadata.get("funds_lost_usd")
    try:
        funds_lost_usd = int(funds_lost_raw) if funds_lost_raw is not None else None
    except ValueError:
        funds_lost_usd = None

    records = []
    chunk_index = 0
    for section_name, section_text in sections:
        for chunk_text in group_paragraphs(section_text):
            records.append({
                "chunk_id": str(uuid.uuid4()),
                "protocol": metadata.get("protocol"),
                "title": metadata.get("protocol"),  # mirrors 'title' field used elsewhere
                "date": metadata.get("date"),
                "attack_type": metadata.get("attack_type"),
                "chain": metadata.get("chain"),
                "funds_lost_usd": funds_lost_usd,
                "source": metadata.get("source"),
                "section": section_name,
                "text": chunk_text,
                "chunk_index": chunk_index,
                "source_file": filepath.name,
            })
            chunk_index += 1
    return records


def main():
    all_chunks = []
    for filepath in RAW_DIR.rglob("*.md"):
        chunks = process_file(filepath)
        all_chunks.extend(chunks)
        print(f"{filepath.name}: {len(chunks)} chunk(s)")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(all_chunks, indent=2), encoding="utf-8")
    print(f"\nTotal: {len(all_chunks)} chunks written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()