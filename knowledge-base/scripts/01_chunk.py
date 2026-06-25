"""
Reads raw markdown source files (frontmatter + body), splits each into
one or more chunks based on length, and writes a single structured
JSON file of chunks ready for embedding.
"""

import re
import json
import uuid
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "raw"
OUTPUT_FILE = Path(__file__).parent.parent / "processed" / "chunks.json"

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


def split_into_chunks(body: str) -> list[str]:
    """
    Group consecutive paragraphs together until adding the next one
    would exceed MAX_CHUNK_TOKENS. Never splits mid-paragraph.
    """
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]

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
    text_chunks = split_into_chunks(body)

    records = []
    for i, chunk_text in enumerate(text_chunks):
        records.append({
            "chunk_id": str(uuid.uuid4()),
            "category": metadata.get("category"),
            "swc_id": metadata.get("swc_id"),
            "source_type": metadata.get("source_type"),
            "title": metadata.get("title"),
            "source_url": metadata.get("source_url"),
            "text": chunk_text,
            "chunk_index": i,
            "source_file": filepath.name,
        })
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