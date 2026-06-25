"""
Loads processed chunks, generates embeddings locally with Sentence
Transformers, and stores them in a persistent local Chroma collection.
"""

import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

CHUNKS_FILE = Path(__file__).parent.parent / "processed" / "chunks.json"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME = "vulnerability_corpus"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

METADATA_FIELDS = ["category", "swc_id", "source_type", "title",
                    "source_url", "source_file", "chunk_index"]


def load_chunks() -> list[dict]:
    return json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))


def clean_metadata(chunk: dict) -> dict:
    """Chroma rejects None values, so only keep fields that are actually present."""
    return {k: chunk[k] for k in METADATA_FIELDS if chunk.get(k) is not None}


def main():
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks")

    print(f"Loading embedding model '{EMBEDDING_MODEL}' (first run downloads it)...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    texts = [c["text"] for c in chunks]
    print("Encoding chunks...")
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Wipe and rebuild on every run, so re-running this script after adding
    # new source files never produces duplicate entries.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    collection.add(
        ids=[c["chunk_id"] for c in chunks],
        embeddings=embeddings,
        documents=texts,
        metadatas=[clean_metadata(c) for c in chunks],
    )

    print(f"Stored {collection.count()} chunks in '{COLLECTION_NAME}' at {CHROMA_DIR}")


if __name__ == "__main__":
    main()