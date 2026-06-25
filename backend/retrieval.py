import os
import chromadb
from sentence_transformers import SentenceTransformer

# Paths relative to project root (where uvicorn is launched from)
CHROMA_PATH = os.path.join("knowledge-base", "chroma_db")
COLLECTION_NAME = "vulnerability_corpus"
MODEL_NAME = "all-MiniLM-L6-v2"

# Load once at module level — avoids reloading on every request
_model = SentenceTransformer(MODEL_NAME)
_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _client.get_collection(COLLECTION_NAME)


def retrieve_context(finding_descriptions: list[str], top_k: int = 2) -> list[dict]:
    """
    Given a list of Slither finding description strings, retrieve the most
    relevant chunks from the knowledge base for each finding, deduplicated.

    Returns a list of chunk dicts with keys:
        id, text, category, swc_id, title, source_type, source_url
    """
    seen_ids = set()
    results = []

    for description in finding_descriptions:
        embedding = _model.encode(description).tolist()

        query_result = _collection.query(
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