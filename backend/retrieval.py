import os
import chromadb
from sentence_transformers import SentenceTransformer

# CHROMA_PATH is resolved relative to THIS FILE's location, not the current
# working directory. The original version used a bare relative path
# ("knowledge-base/chroma_db"), which only resolved correctly when the
# process's cwd happened to be the project root (true when main.py runs via
# `uvicorn main:app` from D:\smart-contract-auditor, since main.py imports
# this as `backend.retrieval`). Every Phase 2/3 standalone script, though,
# is run directly from inside backend/ (`python forensics_report_smoketest.py`
# from D:\smart-contract-auditor\backend) - under that cwd, the same
# relative path resolved to a nonexistent backend/knowledge-base/chroma_db.
# Anchoring to __file__ instead makes this resolve to the same correct
# absolute path either way - a pure robustness fix, not a behavior change
# for the existing uvicorn-from-root case.
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)
CHROMA_PATH = os.path.join(_PROJECT_ROOT, "knowledge-base", "chroma_db")
AUDIT_COLLECTION_NAME = "vulnerability_corpus"
FORENSICS_COLLECTION_NAME = "historical_exploits"
MODEL_NAME = "all-MiniLM-L6-v2"

# Load once at module level - avoids reloading on every request. Shared
# across BOTH audit and forensics retrieval below, same reasoning as reusing
# the existing Ollama fallback logic rather than introducing a third model.
_model = SentenceTransformer(MODEL_NAME)
_client = chromadb.PersistentClient(path=CHROMA_PATH)

# Collections are fetched lazily and cached per name, rather than eagerly
# fetching both at import time - this means a missing historical_exploits
# collection (e.g. on a machine that's only ever run the audit side) won't
# break audit-only usage of this module at import time.
_collections = {}


def _get_collection(collection_name: str):
    if collection_name not in _collections:
        _collections[collection_name] = _client.get_collection(collection_name)
    return _collections[collection_name]


def retrieve_context(
    finding_descriptions: list[str],
    top_k: int = 2,
    collection_name: str = AUDIT_COLLECTION_NAME,
) -> list[dict]:
    """
    Given a list of Slither finding description strings, retrieve the most
    relevant chunks from the knowledge base for each finding, deduplicated.

    UNCHANGED from the original: default collection_name preserves exact
    existing behavior for every current call site (main.py's audit pipeline
    calls this with no collection_name argument at all).

    Returns a list of chunk dicts with keys:
        id, text, category, swc_id, title, source_type, source_url
    """
    collection = _get_collection(collection_name)
    seen_ids = set()
    results = []

    for description in finding_descriptions:
        embedding = _model.encode(description).tolist()

        query_result = collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        for doc, meta, dist in zip(
            query_result["documents"][0],
            query_result["metadatas"][0],
            query_result["distances"][0]
        ):
            chunk_id = meta.get("title", doc[:40])
            if chunk_id in seen_ids:
                continue
            seen_ids.add(chunk_id)

            results.append({
                "text": doc,
                "category": meta.get("category"),
                "swc_id": meta.get("swc_id"),
                "title": meta.get("title"),
                "source_type": meta.get("source_type"),
                "source_url": meta.get("source_url"),
                "distance": round(dist, 4)
            })

    return results


def retrieve_forensics_context(query_texts: list[str], top_k: int = 3) -> list[dict]:
    """
    Forensics counterpart to retrieve_context(), targeting the
    historical_exploits collection instead of vulnerability_corpus.

    Deliberately a separate function rather than a parameterized branch
    inside retrieve_context(): the two collections have genuinely different
    metadata schemas (category/swc_id vs. protocol/date/attack_type/
    funds_lost_usd), so forcing them through one function would mean either
    a pile of "if forensics: ... else: ..." branching inside a single
    function, or a lossy shared field format that fits neither well.

    query_texts: one or more deterministically-constructed description
    strings (see query_builder.py) - NOT raw Slither findings, since
    forensics has no static-analysis step. Each query is run independently
    and results are deduplicated by (source_file, section), since the
    forensics corpus is chunked section-aware (Summary/What Happened/
    Root Cause/Why It Matters per incident) - the same incident can and
    should surface via multiple distinct sections, which a title-only dedup
    key (as used in retrieve_context) would incorrectly collapse.

    Returns a list of chunk dicts with keys:
        text, protocol, title, date, attack_type (list[str]), chain,
        funds_lost_usd, source, section, distance
    """
    collection = _get_collection(FORENSICS_COLLECTION_NAME)
    seen_chunk_keys = set()
    results = []

    for query_text in query_texts:
        embedding = _model.encode(query_text).tolist()

        query_result = collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        for doc, meta, dist in zip(
            query_result["documents"][0],
            query_result["metadatas"][0],
            query_result["distances"][0]
        ):
            chunk_key = (meta.get("source_file"), meta.get("section"))
            if chunk_key in seen_chunk_keys:
                continue
            seen_chunk_keys.add(chunk_key)

            # attack_type is stored as a raw comma-joined string in Chroma
            # metadata (lists aren't a valid metadata value type) - split
            # back into a list here so downstream code (Step 3.3's taxonomy
            # scoring) never has to remember this storage quirk itself.
            raw_attack_type = meta.get("attack_type", "") or ""
            attack_type = [t.strip() for t in raw_attack_type.split(",") if t.strip()]

            results.append({
                "text": doc,
                "protocol": meta.get("protocol"),
                "title": meta.get("title"),
                "date": meta.get("date"),
                "attack_type": attack_type,
                "chain": meta.get("chain"),
                "funds_lost_usd": meta.get("funds_lost_usd"),
                "source": meta.get("source"),
                "section": meta.get("section"),
                "distance": round(dist, 4),
            })

    return results